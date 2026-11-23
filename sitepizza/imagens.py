"""Responsive image variants.

Every upload has its own directory in the storage bucket (MEDIA_ROOT), holding the original
and its resized copies:

    produtos/dom-manuel-1a2b3c4d/original.jpg
    produtos/dom-manuel-1a2b3c4d/160.avif  160.webp  160.jpg  320.avif ...

up to the largest width that does not exceed the original (we never upscale).
AVIF is ~40% smaller than WebP at the same visual quality; it is only produced when the
installed Pillow supports it (Pillow >= 11.3), and the template falls back to WebP/JPEG.

Templates render them with ``{% imagem_responsiva %}`` (see
``templatetags/imagens.py``), which emits a ``<picture>`` with ``srcset`` so the
browser picks the smallest file that is sharp enough for the screen: a budget
phone downloads the 320/480 file, a 4K monitor the 960/1280 one.
"""
import os

from django.core.files.storage import default_storage
from PIL import Image, ImageOps, features

LARGURAS = (160, 320, 480, 640, 960, 1280)
try:
    # Pillow < 11.3 doesn't know the feature and only warns; treat that as "no AVIF".
    AVIF = "avif" in features.get_supported_modules()
except Exception:
    AVIF = False
FORMATOS = ((("avif", "AVIF", {"quality": 58, "speed": 4}),) if AVIF else ()) + (
    ("webp", "WEBP", {"quality": 80, "method": 6}),
    ("jpg", "JPEG", {"quality": 82, "optimize": True, "progressive": True}),
)


def _nome_variante(nome, largura, ext):
    return f"{os.path.dirname(nome)}/{largura}.{ext}"


def apagar_grupo(nome):
    """Delete an upload's directory (original + variants) from the bucket.
    Only touches directories under MEDIA_ROOT that contain an ``original.*`` file."""
    if not nome or os.path.splitext(os.path.basename(nome))[0] != "original":
        return
    pasta = os.path.dirname(default_storage.path(nome))
    raiz = os.path.realpath(default_storage.location)
    if not os.path.realpath(pasta).startswith(raiz + os.sep) or not os.path.isdir(pasta):
        return
    for f in os.listdir(pasta):
        os.remove(os.path.join(pasta, f))
    os.rmdir(pasta)


def gerar_variantes(nome, forcar=False):
    """Create the resized copies for the stored image ``nome``. Returns how many files were written."""
    if not nome or not default_storage.exists(nome):
        return 0
    caminho = default_storage.path(nome)
    escritos = 0
    with Image.open(caminho) as original:
        img = ImageOps.exif_transpose(original)
        if img.mode in ("RGBA", "LA", "P"):
            fundo = Image.new("RGB", img.size, (255, 255, 255))
            img = img.convert("RGBA")
            fundo.paste(img, mask=img.getchannel("A"))
            img = fundo
        else:
            img = img.convert("RGB")
        for largura in LARGURAS:
            if largura > img.width:
                break
            altura = round(img.height * largura / img.width)
            redim = None
            for ext, formato, opcoes in FORMATOS:
                destino = default_storage.path(_nome_variante(nome, largura, ext))
                # Uploads get a unique key and are never overwritten in place, so an existing variant is
                # always current. (No timestamp check: git checkouts don't preserve modification times.)
                if not forcar and os.path.exists(destino):
                    continue
                if redim is None:
                    redim = img.resize((largura, altura), Image.LANCZOS)
                redim.save(destino, formato, **opcoes)
                escritos += 1
    return escritos


def variantes(nome):
    """Existing variants of ``nome``: {"avif": [(w, url)...], "webp": [...], "jpg": [...]}, smallest first.
    A width is only listed for a format if that file exists (AVIF may be missing on old Pillow)."""
    resultado = {"avif": [], "webp": [], "jpg": []}
    if not nome:
        return resultado
    for largura in LARGURAS:
        for ext in resultado:
            v = _nome_variante(nome, largura, ext)
            if default_storage.exists(v):
                resultado[ext].append((largura, default_storage.url(v)))
    return resultado


def dimensoes(nome):
    """(width, height) of the stored original, read from the file header only."""
    try:
        with Image.open(default_storage.path(nome)) as img:
            return ImageOps.exif_transpose(img).size
    except (OSError, ValueError):
        return None
