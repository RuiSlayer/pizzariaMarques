from django import template
from django.utils.html import format_html

from sitepizza.icones_svg import ICONES

register = template.Library()


@register.simple_tag
def icone(nome, classe=""):
    """Inline SVG icon, e.g. {% icone "phone" %}. Decorative: hidden from screen readers."""
    viewbox, d = ICONES[nome]
    return format_html(
        '<svg class="icone {}" viewBox="{}" aria-hidden="true" focusable="false"><path d="{}"/></svg>',
        classe, viewbox, d)
