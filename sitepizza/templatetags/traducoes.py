from django import template
from django.utils.translation import get_language, gettext

register = template.Library()


@register.filter
def traduzir(texto):
    """Translate a text that comes from the database, e.g. {{ produto.nome|traduzir }}.

    The texts are listed in sitepizza/catalogo_i18n.py; anything else is returned unchanged.
    """
    return gettext(texto) if texto else texto


@register.simple_tag
def sufixo_idioma():
    """Folder suffix of images that have their text in the picture, e.g. banners/forno-en/.

    Usage: {% sufixo_idioma as sufixo %} ... {% static 'img/banners/forno'|add:sufixo|add:'/630.jpg' %}
    """
    return "-en" if get_language() == "en" else ""
