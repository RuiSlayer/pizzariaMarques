"""Trim the self-hosted variable fonts to what the site uses (run after `npm install`).

    python tools/subset-fonts.py        # needs: pip install fonttools brotli

- Weight axis limited to the weights in the CSS (Fraunces 500-700, Source Sans 3 400-700).
- Glyphs limited to ASCII + Portuguese letters + the punctuation/symbols the site prints.
Anything outside the set (e.g. an unusual letter in a user name) falls back per glyph to the
metric-matched fallback font declared in style.css, so text never breaks.
Result: ~65 KB -> ~40 KB for both fonts together. Output goes to sitepizza/assets/fonts/,
which tools/build-assets.mjs copies into static/fonts/.
"""
import io
import os

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NM = os.path.join(RAIZ, "node_modules", "@fontsource-variable")
SAIDA = os.path.join(RAIZ, "sitepizza", "assets", "fonts")
CARACTERES = "".join(chr(c) for c in range(0x20, 0x7F)) + "ÁÀÂÃÇÉÊÍÓÔÕÚÜáàâãçéêíóôõúü€«»“”‘’–—…·°ºª×→←↑↓ "

FONTES = [
    ("fraunces/files/fraunces-latin-wght-normal.woff2", "fraunces-pt-wght.woff2", (500, 700)),
    ("source-sans-3/files/source-sans-3-latin-wght-normal.woff2", "source-sans-3-pt-wght.woff2", (400, 700)),
]

os.makedirs(SAIDA, exist_ok=True)
for origem, destino, pesos in FONTES:
    fonte = TTFont(os.path.join(NM, origem), lazy=False)
    fonte.flavor = None
    fonte = instantiateVariableFont(fonte, {"wght": pesos})
    tmp = io.BytesIO()
    fonte.save(tmp)
    tmp.seek(0)
    fonte = TTFont(tmp, lazy=False)  # reload: the instancer leaves lazily-loaded tables behind
    opcoes = subset.Options()
    opcoes.flavor = "woff2"
    opcoes.layout_features = ["kern", "liga", "calt", "ccmp", "locl", "mark", "mkmk", "lnum", "pnum", "tnum"]
    opcoes.name_IDs = ["*"]
    opcoes.notdef_outline = True
    s = subset.Subsetter(opcoes)
    s.populate(text=CARACTERES)
    s.subset(fonte)
    fonte.flavor = "woff2"
    caminho = os.path.join(SAIDA, destino)
    fonte.save(caminho)
    print(f"{destino}: {os.path.getsize(caminho) / 1024:.1f} KB (wght {pesos[0]}-{pesos[1]})")
