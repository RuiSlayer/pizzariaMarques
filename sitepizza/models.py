import os
import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

BIG_CHAR = 100
MEDIUM_CHAR = 50
SMALL_CHAR = 25
DINHEIRO = 5
DECIMAL = 2
ID = 3

# Limits shared by the models, the forms, the views and the templates (one value, used everywhere).
PRECO_MINIMO = Decimal('0.01')   # a product can't be free or negative; max is 999.99 (max_digits=5)
MORADA_MAX = 150                 # characters in an address (profile and checkout)
QTD_MAXIMA = 20                  # of one product: per add on the menu and per line in the cart


# Uploads go to the storage bucket (MEDIA_ROOT), one directory per image:
#   produtos/<nome>-<id>/original.jpg  plus its size variants (320.avif, 320.webp, ...)
# A unique key per upload means a file is never overwritten in place, so it can be cached forever.
def _chave(prefixo):
    return f"{slugify(prefixo) or 'imagem'}-{uuid.uuid4().hex[:8]}"


def _extensao(filename):
    return os.path.splitext(filename)[1].lower() or '.jpg'


def caminho_produto(instance, filename):
    return f"produtos/{_chave(instance.nome)}/original{_extensao(filename)}"


def caminho_avatar(instance, filename):
    return f"avatars/{_chave(f'utilizador-{instance.user_id}')}/original{_extensao(filename)}"


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    morada = models.TextField(null=True, max_length=MORADA_MAX)
    telemovel = models.IntegerField(null=True)
    image = models.ImageField(upload_to=caminho_avatar, null=True, blank=True)


class Categoria(models.Model):
    nome= models.CharField(max_length=BIG_CHAR)
    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=BIG_CHAR, null=False)
    descricao= models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=caminho_produto)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    preco = models.DecimalField(decimal_places=2, max_digits=5, validators=[MinValueValidator(PRECO_MINIMO)])


    def __str__(self):
        return self.nome

class ProdutoPedido(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.quantidade} de {self.produto.nome}"

    def precoprodutos(self):
        return self.quantidade*self.produto.preco;


class Pedido(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    valorPedido = models.DecimalField(default=0, decimal_places=2, max_digits=8)   # money: Decimal, like Produto.preco
    dataPedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=SMALL_CHAR, null=False)
    ordered = models.BooleanField(default=False)
    produtos = models.ManyToManyField(ProdutoPedido)
    countprodutos= models.IntegerField(default=0)

    def __str__(self):
        return '{0} - {1}'.format(self.user, self.id)


    def subtotal(self):
        # Starts at Decimal 0.00, so an empty cart shows 0,00 € (a plain sum([]) is the int 0).
        return sum((produtoitem.quantidade * produtoitem.produto.preco for produtoitem in self.produtos.all()), Decimal('0.00'))


class Checkout(models.Model):
    metEntrega= models.TextField(null=True, max_length=MEDIUM_CHAR)
    morada = models.TextField(null=True, max_length=MORADA_MAX)
    metPagamento = models.TextField(null=True, max_length=MEDIUM_CHAR)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
