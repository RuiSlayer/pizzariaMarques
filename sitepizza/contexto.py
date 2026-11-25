from django.db.models import Sum

from .models import MORADA_MAX, QTD_MAXIMA, ProdutoPedido


def total_carrinho(user):
    """Number of items in the user's open cart."""
    return ProdutoPedido.objects.filter(user=user, ordered=False).aggregate(t=Sum('quantidade'))['t'] or 0


def limites(request):
    """{{ qtd_maxima }}, {{ morada_max }}: the same limits the views enforce, for the inputs."""
    return {'qtd_maxima': QTD_MAXIMA, 'morada_max': MORADA_MAX}


def carrinho(request):
    """{{ carrinho_total }}: items in the cart, for the count on the header's Carrinho button.

    Lazy: the template calls it, so pages that don't show the header don't run the query.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    cache = []

    def total():
        if not cache:
            cache.append(total_carrinho(user))
        return cache[0]
    return {'carrinho_total': total}
