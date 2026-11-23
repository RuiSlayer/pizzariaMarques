from django.shortcuts import render, redirect, get_object_or_404
from .models import Produto, Pedido, ProdutoPedido, Perfil, Checkout
from .forms import CreateUserForm, PerfilForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


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
        messages.warning(request, 'Adicione Produtos ao carrinho.')
        return redirect('navegar:checkout')

    entrega = request.POST.get('entrega')
    morada = request.POST.get('morada')
    pagamento = request.POST.get('pagamento')

    ENTREGAS = {'Entrega em casa', 'Recolha no restaurante'}
    PAGAMENTOS = {'Dinheiro', 'Cartao', 'Mbway'}

    if entrega not in ENTREGAS or pagamento not in PAGAMENTOS:
        messages.warning(request, 'Preencha os campos todos para finalizar.')
        return render(request, 'sitepizza/checkout.html', ctx)

    if entrega == 'Recolha no restaurante':
        morada = 'Recolha no restaurante'
    elif morada == 'morada2':
        morada = request.POST.get('morada-nova', '').strip()
        if not morada:
            messages.warning(request, 'Preencha os campos todos para finalizar.')
            return render(request, 'sitepizza/checkout.html', ctx)
    elif morada:
        morada = perfil.morada      # ignore the posted text, use the stored address
    else:
        messages.warning(request, 'Preencha os campos todos para finalizar.')
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


@login_required(login_url='navegar:login')
@require_POST
def add_carrinho(request):
    produto = get_object_or_404(Produto, pk=request.POST.get('produto'))
    try:
        qtd = int(request.POST.get('quantidade', 1))
    except ValueError:
        qtd = 0
    if not 1 <= qtd <= 50:
        messages.error(request, 'Quantidade inválida.')
        return redirect('navegar:menu')

    with transaction.atomic():
        pedido, _ = Pedido.objects.get_or_create(user=request.user, ordered=False)
        pp, _ = ProdutoPedido.objects.get_or_create(
            produto=produto, user=request.user, ordered=False)
        pedido.produtos.add(pp)        # safe to call even if already added
        pp.quantidade += qtd
        pp.save()
        pedido.countprodutos += qtd
        pedido.save()

    messages.success(request, 'Produto adicionado ao carrinho.')
    return redirect('navegar:menu')


@login_required(login_url='navegar:login')
@require_POST
def remove_do_carrinho(request):
    pp = get_object_or_404(ProdutoPedido, produto=request.POST.get('produtopizza'),
                           user=request.user, ordered=False)
    with transaction.atomic():
        if pp.quantidade <= 1:
            pp.delete()
        else:
            pp.quantidade -= 1
            pp.save()
        pedido = Pedido.objects.filter(user=request.user, ordered=False).first()
        if pedido:
            pedido.countprodutos = max(0, pedido.countprodutos - 1)
            pedido.save()

    messages.success(request, 'Produto removido.')
    return redirect('navegar:checkout')

@login_required(login_url='navegar:login')
def checkout(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    pedido, _ = Pedido.objects.get_or_create(user=request.user, ordered=False)
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

            messages.success(request, 'A conta foi criada para ' + user.username)
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
            return redirect('navegar:home')
        messages.error(request, 'Username ou Password Incorreta!')

    return render(request, 'sitepizza/login.html')


def logoutUser(request):
    logout(request)
    return redirect('navegar:login')


#---------------------------------------Perfil--------------------------------------------------------------------------

@login_required(login_url='navegar:login')
def perfil(request, user_id):
    perfil = get_object_or_404(Perfil, user=request.user, user_id=user_id)
    return render(request, 'sitepizza/perfil.html', {'perfil': perfil})

@login_required(login_url='navegar:login')
@require_POST
def fazer_upload(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    myfile = request.FILES.get('myfile')

    if myfile is None or not myfile.content_type.startswith('image/') or myfile.size > 2 * 1024 * 1024:
        messages.error(request, 'Envie uma imagem até 2 MB.')
    else:
        perfil.image = myfile
        perfil.save()
        messages.success(request, 'Imagem atualizada.')

    return redirect('navegar:perfil', user_id=request.user.id)