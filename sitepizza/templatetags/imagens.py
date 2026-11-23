from django import template
from django.utils.html import format_html, format_html_join

from sitepizza.imagens import dimensoes, variantes

register = template.Library()


def _srcset(lista):
    return ", ".join(f"{url} {w}w" for w, url in lista)


@register.simple_tag
def imagem_responsiva(imagem, sizes="100vw", alt="", classe="", lazy=True, largura=None, altura=None, prioridade=False):
    """Render an ImageField as a <picture> with AVIF / WebP / JPEG srcsets.

    Usage: {% load imagens %}
           {% imagem_responsiva produto.image sizes="(max-width: 576px) 90vw, 320px" alt=produto.nome classe="imagens-menu" %}

    The browser takes the first format it supports and, within it, the smallest width that is
    sharp enough for the slot (sizes) and the screen density. Falls back to a plain <img> when no
    variants exist (e.g. a tiny upload). largura/altura override the width/height attributes
    (e.g. a fixed-size avatar); prioridade=True marks the LCP image.
    """
    if not imagem:
        return ""
    nome = imagem.name
    vs = variantes(nome)
    if largura is None or altura is None:
        dims = dimensoes(nome)
        largura, altura = dims if dims else ("", "")
    carregamento = "lazy" if lazy else "eager"
    prioridade_attr = "high" if prioridade else "auto"

    if not vs["jpg"]:
        return format_html(
            '<img class="{}" src="{}" alt="{}" width="{}" height="{}" loading="{}" fetchpriority="{}" decoding="async">',
            classe, imagem.url, alt, largura, altura, carregamento, prioridade_attr)

    fontes = format_html_join(
        "", '<source type="{}" srcset="{}" sizes="{}">',
        ((f"image/{ext}", _srcset(vs[ext]), sizes) for ext in ("avif", "webp") if vs[ext]))
    # JPEG src for very old browsers: the 640 variant, or the largest one available.
    fallback = next((u for w, u in vs["jpg"] if w == 640), vs["jpg"][-1][1])
    return format_html(
        '<picture>{}<img class="{}" src="{}" srcset="{}" sizes="{}" alt="{}" width="{}" height="{}" '
        'loading="{}" fetchpriority="{}" decoding="async"></picture>',
        fontes, classe, fallback, _srcset(vs["jpg"]), sizes, alt, largura, altura, carregamento, prioridade_attr)
