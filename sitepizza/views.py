from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from functools import wraps
from urllib.parse import urlencode
from decimal import Decimal

from PIL import Image, UnidentifiedImageError

from .models import MORADA_MAX, QTD_MAXIMA, Produto, Pedido, ProdutoPedido, Perfil, Checkout
from .forms import CreateUserForm, PerfilForm
from .contexto import total_carrinho
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import formats
from django.utils.translation import gettext as _

# Largest order total Pedido.valorPedido can store (Decimal(8, 2): 999 999.99).
_campo_total = Pedido._meta.get_field('valorPedido')
TOTAL_MAXIMO = Decimal(10) ** (_campo_total.max_digits - _campo_total.decimal_places) - Decimal(1).scaleb(-_campo_total.decimal_places)

# Profile photos: what the page promises ("JPG ou PNG, até 2 MB").
FOTO_MAX_BYTES = 2 * 1024 * 1024
FOTO_FORMATOS = {'JPEG', 'PNG'}


def home(request):
    perfil = None
    if request.user.is_authenticated:
        perfil = Perfil.objects.filter(user=request.user).first()
    return render(request, 'sitepizza/home.html', {'perfil': perfil})


def sobrenos(request):
    return render(request, 'sitepizza/sobrenos.html')


def contactos(request):
    return render(request, 'sitepizza/contactos.html')

@login_required(login_url='navegar:login')
def finalizar(request):
    user = request.user
    pedido = Pedido.objects.filter(user=user, ordered=False).first()
    if pedido is None:
        # No open order (e.g. already finalized): go somewhere safe
        return redirect('navegar:home')   # use your own URL name

    produtos_pedido = pedido.produtos.all()
    perfil = get_object_or_404(Perfil, user=request.user)
    ctx = {'produtos_pedido': produtos_pedido, 'pedido': pedido, 'perfil': perfil}

    if request.method != 'POST':
        return render(request, 'sitepizza/checkout.html', ctx)

    if not produtos_pedido.exists():
        messages.warning(request, _('Adicione Produtos ao carrinho.'))
        return redirect('navegar:checkout')

    entrega = request.POST.get('entrega')
    morada = request.POST.get('morada')
    pagamento = request.POST.get('pagamento')

    ENTREGAS = {'Entrega em casa', 'Recolha no restaurante'}
    PAGAMENTOS = {'Dinheiro', 'Cartao', 'Mbway'}

    if entrega not in ENTREGAS or pagamento not in PAGAMENTOS:
        messages.warning(request, _('Preencha os campos todos para finalizar.'))
        return render(request, 'sitepizza/checkout.html', ctx)

    if entrega == 'Recolha no restaurante':
        morada = 'Recolha no restaurante'
    elif morada == 'morada2':
        morada = request.POST.get('morada-nova', '').strip()
        if not morada:
            messages.warning(request, _('Preencha os campos todos para finalizar.'))
            return render(request, 'sitepizza/checkout.html', ctx)
        if len(morada) > MORADA_MAX:
            messages.warning(request, _('A morada pode ter até %(max)s caracteres.') % {'max': MORADA_MAX})
            return render(request, 'sitepizza/checkout.html', ctx)
    elif morada:
        morada = perfil.morada      # ignore the posted text, use the stored address
    else:
        messages.warning(request, _('Preencha os campos todos para finalizar.'))
        return render(request, 'sitepizza/checkout.html', ctx)

    # Can't happen with 20 per product at up to 999.99, unless the menu grows past 50 products;
    # checked anyway, so it's a message and not a database error.
    if pedido.subtotal() > TOTAL_MAXIMO:
        messages.warning(request, _('O pedido ultrapassa o valor máximo. Retira alguns produtos ou fala connosco.'))
        return render(request, 'sitepizza/checkout.html', ctx)

    with transaction.atomic():
        checkout = Checkout.objects.create(
            pedido=pedido, metEntrega=entrega, morada=morada, metPagamento=pagamento
        )
        pedido.valorPedido = pedido.subtotal()   # compute server-side, see note
        pedido.ordered = True
        pedido.estado = 'Recebido'
        pedido.save()
        ProdutoPedido.objects.filter(user=user, ordered=False).update(ordered=True)

    return redirect('navegar:finalizar_confirmacao', checkout_id=checkout.id)

@login_required(login_url='navegar:login')
def finalizar_confirmacao(request, checkout_id):
    checkout = get_object_or_404(Checkout, id=checkout_id, pedido__user=request.user)
    return render(request, 'sitepizza/finalizar.html',
                  {'checkout': checkout, 'pedido': checkout.pedido})

def menu(request):
    """
    buscar cada produto de cada categoria
    """
        # 
    pizzas = Produto.objects.filter(categoria__nome__icontains="pizza")
    acompanhamentos = Produto.objects.filter(categoria__nome__icontains="acompanhamento")
    bebidas = Produto.objects.filter(categoria__nome__icontains="bebida")
    sobremesas = Produto.objects.filter(categoria__nome__icontains="sobremesa")

    #por no contexto

    context = {
        'pizzas': pizzas,
        'acompanhamentos': acompanhamentos,
        'bebidas': bebidas,
        'sobremesas': sobremesas,
    }

    #fazer render
    return render(request, 'sitepizza/menu.html', context)


@require_POST
def add_carrinho(request):
    """Add a product to the cart.

    The menu's forms post here. With JavaScript the request asks for JSON (Accept: application/json)
    and the page updates in place; without it, the response goes back to the same product on the menu.
    """
    produto = get_object_or_404(Produto, pk=request.POST.get('produto'))
    json = 'application/json' in request.headers.get('Accept', '')
    no_menu = reverse('navegar:menu') + f'#produto-{produto.id}'

    if not request.user.is_authenticated:
        # Log in, then come back to this product (not to the home page).
        destino = reverse('navegar:login') + '?' + urlencode({'next': no_menu})
        messages.info(request, _('Inicia sessão para adicionar produtos ao carrinho.'))
        return JsonResponse({'redirect': destino}, status=401) if json else redirect(destino)

    try:
        qtd = int(request.POST.get('quantidade', 1))
    except ValueError:
        qtd = 0
    if not 1 <= qtd <= QTD_MAXIMA:
        mensagem = _('Quantidade inválida.')
        if json:
            return JsonResponse({'mensagem': mensagem}, status=400)
        messages.error(request, mensagem)
        return redirect(no_menu)

    with transaction.atomic():
        pedido, _criado = Pedido.objects.get_or_create(user=request.user, ordered=False)
        pp, _criado = ProdutoPedido.objects.select_for_update().get_or_create(
            produto=produto, user=request.user, ordered=False)
        ja_tem = pp.quantidade
        if ja_tem + qtd <= QTD_MAXIMA:
            pedido.produtos.add(pp)        # safe to call even if already added
            pp.quantidade += qtd
            pp.save()
            pedido.countprodutos += qtd
            pedido.save()

    if ja_tem + qtd > QTD_MAXIMA:
        # The same 20 as the stepper, for the whole cart line (not only per add).
        mensagem = _('Podes ter até %(max)s × %(nome)s no carrinho (já tens %(tens)s).') % {
            'max': QTD_MAXIMA, 'nome': _(produto.nome), 'tens': ja_tem}
        if json:
            return JsonResponse({'mensagem': mensagem}, status=400)
        messages.warning(request, mensagem)
        return redirect(no_menu)

    mensagem = _('Adicionado ao carrinho: %(qtd)s × %(nome)s') % {'qtd': qtd, 'nome': _(produto.nome)}
    if json:
        return JsonResponse({'mensagem': mensagem, 'total': total_carrinho(request.user)})
    messages.success(request, mensagem)
    return redirect(no_menu)


def _login_e_voltar_a(nome_url):
    """login_required for POST-only views: after logging in, go to a page (the cart, the profile),
    not back to the form's URL, which only accepts POST."""
    def decorador(view):
        @wraps(view)
        def envolvida(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(reverse('navegar:login') + '?' + urlencode({'next': reverse(nome_url)}))
            return view(request, *args, **kwargs)
        return envolvida
    return decorador


@_login_e_voltar_a('navegar:checkout')
@require_POST
def alterar_carrinho(request):
    """Set the quantity of a cart line (the cart's − n + stepper); 0 removes it (the Remover button).

    The buttons post the quantity they lead to, not a step, so a repeated request can't remove twice.
    With JavaScript (Accept: application/json) the page updates in place; without it, back to the line.
    """
    json = 'application/json' in request.headers.get('Accept', '')
    carrinho = reverse('navegar:checkout')
    try:
        qtd = int(request.POST.get('quantidade', ''))
    except ValueError:
        qtd = -1

    with transaction.atomic():
        pp = (ProdutoPedido.objects.select_for_update().select_related('produto')
              .filter(produto=request.POST.get('produto'), user=request.user, ordered=False).first())
        if pp is None or not 0 <= qtd <= QTD_MAXIMA:
            erro = _('Este produto já não está no carrinho.') if pp is None else _('Quantidade inválida.')
        else:
            erro = None
            diferenca = qtd - pp.quantidade
            if qtd == 0:
                pp.delete()
            else:
                pp.quantidade = qtd
                pp.save()
            pedido = Pedido.objects.filter(user=request.user, ordered=False).first()
            if pedido:
                pedido.countprodutos = max(0, pedido.countprodutos + diferenca)
                pedido.save()

    if erro:
        if json:
            return JsonResponse({'mensagem': erro}, status=400)
        messages.error(request, erro)
        return redirect(carrinho)

    nome = _(pp.produto.nome)
    if qtd == 0:
        mensagem = _('Removido do carrinho: %(nome)s') % {'nome': nome}
    else:
        mensagem = _('Quantidade de %(nome)s: %(qtd)s') % {'nome': nome, 'qtd': qtd}
    if json:
        pedido = Pedido.objects.filter(user=request.user, ordered=False).first()
        subtotal = pedido.subtotal() if pedido else Decimal('0.00')
        return JsonResponse({
            'quantidade': qtd,
            'linha': formats.localize(qtd * pp.produto.preco),     # same format as the template
            'subtotal': formats.localize(subtotal),
            'total': total_carrinho(request.user),
            'mensagem': mensagem,
        })
    if qtd == 0:
        messages.success(request, mensagem)
        return redirect(carrinho + '#titulo-carrinho')
    return redirect(carrinho + f'#item-{pp.produto_id}')

@login_required(login_url='navegar:login')
def checkout(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    pedido, _criado = Pedido.objects.get_or_create(user=request.user, ordered=False)
    return render(request, 'sitepizza/checkout.html', {
        'produtos_pedido': pedido.produtos.all(),
        'pedido': pedido,
        'perfil': perfil,
    })

#--------------------------LOGIN / REGISTO-------------------------------------------------------------

def registo(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        perfil_form = PerfilForm(request.POST)

        if form.is_valid() and perfil_form.is_valid():
            with transaction.atomic():
                user = form.save()
                perfil = perfil_form.save(commit=False)
                perfil.user = user
                perfil.save()

            messages.success(request, _('A conta foi criada para %(nome)s') % {'nome': user.username})
            return redirect('navegar:login')
    else:
        form = CreateUserForm()
        perfil_form = PerfilForm()
    return render(request, 'sitepizza/registo.html', {'form': form, 'perfil_form': perfil_form})


def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Back to where the visitor was going (e.g. the product they tried to add), if it's on this site.
            seguinte = request.GET.get('next', '')
            if url_has_allowed_host_and_scheme(seguinte, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(seguinte)
            return redirect('navegar:home')
        messages.error(request, _('Username ou Password Incorreta!'))

    return render(request, 'sitepizza/login.html')


def logoutUser(request):
    logout(request)
    return redirect('navegar:login')


#---------------------------------------Perfil--------------------------------------------------------------------------

@login_required(login_url='navegar:login')
def perfil(request, user_id):
    perfil = get_object_or_404(Perfil, user=request.user, user_id=user_id)
    return render(request, 'sitepizza/perfil.html', {'perfil': perfil})

def _foto_valida(ficheiro):
    """JPEG or PNG up to 2 MB, checked on the file itself (the browser's content type can be anything)."""
    if ficheiro is None or ficheiro.size > FOTO_MAX_BYTES:
        return False
    try:
        with Image.open(ficheiro) as imagem:
            formato = imagem.format
            imagem.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        return False
    finally:
        ficheiro.seek(0)
    return formato in FOTO_FORMATOS


@_login_e_voltar_a('navegar:home')
@require_POST
def fazer_upload(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    myfile = request.FILES.get('myfile')

    if not _foto_valida(myfile):
        messages.error(request, _('Envia uma foto JPG ou PNG até 2 MB.'))
    else:
        perfil.image = myfile
        perfil.save()
        messages.success(request, _('Imagem atualizada.'))

    return redirect('navegar:perfil', user_id=request.user.id)