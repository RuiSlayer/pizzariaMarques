"""Build the English versions of the home-page banners from the Portuguese ones.

    python tools/banners-en.py      # needs: npm install, pip install pillow numpy opencv-contrib-python-headless

The banners have their copy set into the image, so the English set is made from the Portuguese
masters (the largest size of each): the Portuguese lines are erased and the English ones are set
in the same place, typeface, size, colour and drop shadow.

- Each Portuguese line is measured first: its typeface settings were matched once against the
  artwork (Fraunces opsz 14 / wght 790, Source Sans 3), and the size and baseline of every line are
  fitted again here from its ink, so the English line sits exactly where the Portuguese one was.
- Erasing: on the flat red backgrounds the text area is filled with the background colour; on the
  stone wall of "online" the letters and their shadows are inpainted (OpenCV shift-map) before the new
  text goes on top. The "FRESHLY MADE" badge and the photo labels are redrawn at their size.
- Output: sitepizza/static/img/banners/<name>-en/, same widths and formats (AVIF, WebP, JPEG) as
  the Portuguese set. home.html picks the set that matches the page language.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNERS = os.path.join(RAIZ, "sitepizza", "static", "img", "banners")
NM = os.path.join(RAIZ, "node_modules", "@fontsource-variable")
FRAUNCES = (os.path.join(NM, "fraunces", "files", "fraunces-latin-full-normal.woff2"), [14, 790, 0, 0])
SOURCE_SANS = (os.path.join(NM, "source-sans-3", "files", "source-sans-3-latin-wght-normal.woff2"), [700])

CREME = (255, 244, 226)
AMARELO = (254, 196, 0)
TINTA_SELO = (63, 3, 0)          # text on the yellow badge
VERMELHO = (139, 3, 3)           # photo labels
SOMBRA = (9, 1, 0)

# Same encoders and settings as the rest of the site's images (sitepizza/imagens.py).
FORMATOS = (
    ("avif", "AVIF", {"quality": 58, "speed": 4}),
    ("webp", "WEBP", {"quality": 80, "method": 6}),
    ("jpg", "JPEG", {"quality": 82, "optimize": True, "progressive": True}),
)


def mascara(a, tipo):
    """Pixels of a text colour (cream, yellow, or the badge's dark ink)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if tipo == "creme":
        return (r > 200) & (g > 185) & (b > 160)
    if tipo == "amarelo":
        return (r > 200) & (g > 140) & (b < 120)
    return (r < 110) & (g < 40)


def fonte(familia, tamanho):
    caminho, eixos = familia
    f = ImageFont.truetype(caminho, round(tamanho * 4) / 4)
    f.set_variation_by_axes(eixos)
    return f


def tinta(familia, tamanho, texto):
    """Ink box of the text relative to its left-baseline origin."""
    return fonte(familia, tamanho).getbbox(texto, anchor="ls")


class Linha:
    """One line of copy: where the Portuguese one is, and what replaces it."""

    def __init__(self, caixa, tipo, familia, pt, en, alinhar="esquerda", cor=None, sombra=True):
        self.caixa, self.tipo, self.familia = caixa, tipo, familia
        self.pt, self.en, self.alinhar, self.sombra = pt, en, alinhar, sombra
        self.cor = cor or {"creme": CREME, "amarelo": AMARELO, "escuro": TINTA_SELO}[tipo]

    def medir(self, a):
        """Fit size and baseline to the Portuguese ink; returns the fitted ink box for QA."""
        x0, y0, x1, y1 = self.caixa
        m = mascara(a[y0:y1, x0:x1].astype(int), self.tipo)
        ys, xs = np.where(m)
        self.ink = (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)
        largura = self.ink[2] - self.ink[0]
        lo, hi = 8.0, 400.0
        for _ in range(20):
            meio = (lo + hi) / 2
            l, t, r, b = tinta(self.familia, meio, self.pt)
            lo, hi = (meio, hi) if r - l < largura else (lo, meio)
        self.tamanho = lo
        l, t, r, b = tinta(self.familia, lo, self.pt)
        self.base = self.ink[3] - b               # baseline y
        return (r - l, b - t), (largura, self.ink[3] - self.ink[1])

    def desenhar(self, img, sombra_px):
        f = fonte(self.familia, self.tamanho)
        l, t, r, b = f.getbbox(self.en, anchor="ls")
        if self.alinhar == "esquerda":
            x = self.ink[0] - l
        elif self.alinhar == "direita":
            x = self.ink[2] - r
        else:
            x = (self.ink[0] + self.ink[2]) / 2 - (l + r) / 2
        d = ImageDraw.Draw(img)
        if self.sombra:
            d.text((x + sombra_px, self.base + sombra_px), self.en, font=f, fill=SOMBRA, anchor="ls")
        d.text((x, self.base), self.en, font=f, fill=self.cor, anchor="ls")


def apagar_cor(img, caixa, cor):
    ImageDraw.Draw(img).rectangle(caixa, fill=cor)


def apagar_textura(img, linhas, sombra_px):
    """Inpaint the letters (and their drop shadow) of the given lines out of a textured background.

    Shift-map inpainting fills the holes with pieces of the same wall instead of blurring them,
    so the stone stays sharp where the English text is shorter than the Portuguese.
    """
    a = np.asarray(img)
    m = np.zeros(a.shape[:2], np.uint8)
    for ln in linhas:
        x0, y0, x1, y1 = ln.caixa
        reg = a[y0:y1, x0:x1].astype(int)
        r, g = reg[..., 0], reg[..., 1]
        m[y0:y1, x0:x1] |= ((r > 135) & (g > 95)).astype(np.uint8)   # cream + yellow, with antialiasing
    k = np.ones((3, 3), np.uint8)
    m = cv2.dilate(m, k, iterations=2)
    sombra = np.zeros_like(m)
    sombra[sombra_px:, sombra_px:] = m[:-sombra_px, :-sombra_px]
    m = cv2.dilate(m | sombra, k, iterations=3)
    lab = cv2.cvtColor(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2Lab)   # shift-map works in Lab
    saida = np.zeros_like(lab)
    cv2.xphoto.inpaint(lab, (1 - m).astype(np.uint8), saida, cv2.xphoto.INPAINT_SHIFTMAP)  # non-zero = keep
    img.paste(Image.fromarray(cv2.cvtColor(cv2.cvtColor(saida, cv2.COLOR_Lab2BGR), cv2.COLOR_BGR2RGB)))


def selo(img, a, caixa, fundo, texto_pt, texto_en, escala):
    """Yellow badge with dark text: erase it, redraw it at the width of the English text."""
    x0, y0, x1, y1 = caixa
    amarelo = mascara(a[y0:y1, x0:x1].astype(int), "amarelo")
    ys, xs = np.where(amarelo)
    bx0, by0, bx1, by1 = x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1
    linha = Linha((bx0, by0, bx1, by1), "escuro", SOURCE_SANS, texto_pt, texto_en, sombra=False)
    linha.medir(a)
    folga = linha.ink[0] - bx0
    l, t, r, b = tinta(SOURCE_SANS, linha.tamanho, texto_en)
    apagar_cor(img, (bx0 - 2, by0 - 2, bx1 + 2, by1 + 2), fundo)
    ImageDraw.Draw(img).rounded_rectangle((bx0, by0, bx0 + 2 * folga + (r - l), by1 - 1),
                                          radius=round(12 * escala), fill=AMARELO)
    linha.desenhar(img, 0)


def etiqueta(img, a, caixa, texto_pt, texto_en):
    """Red label on a photo: redraw it over the old one, never narrower (it has to cover it)."""
    x0, y0, x1, y1 = caixa
    linha = Linha(caixa, "creme", SOURCE_SANS, texto_pt, texto_en, sombra=False)
    linha.medir(a)
    folga = linha.ink[0] - x0
    l, t, r, b = tinta(SOURCE_SANS, linha.tamanho, texto_en)
    largura = max(x1 - x0, 2 * folga + (r - l))
    raio = (y1 - y0) // 2 - 4
    ImageDraw.Draw(img).rounded_rectangle((x0 - 1, y0 - 1, x0 + largura, y1), radius=raio, fill=VERMELHO)
    linha.desenhar(img, 0)


F, S = FRAUNCES, SOURCE_SANS
BANNERS_EN = {
    "forno-largo": dict(
        larguras=(1260, 1890, 2520), fundo=(178, 20, 19), sombra=6,
        selo=((120, 145, 660, 240), "ACABADA DE FAZER", "FRESHLY MADE"),
        apagar=[(120, 290, 1430, 880)],
        linhas=[
            Linha((150, 300, 1300, 445), "creme", F, "Saída do forno", "From the oven"),
            Linha((150, 500, 1370, 660), "amarelo", F, "para a tua mesa", "to your table"),
            Linha((160, 712, 905, 782), "creme", S, "Massa fresca, ingredientes de", "Fresh dough, quality ingredients"),
            Linha((160, 792, 805, 866), "creme", S, "qualidade e muito queijo.", "and plenty of cheese."),
        ]),
    "forno": dict(
        larguras=(480, 630, 720, 945, 1260), fundo=(178, 20, 19), sombra=3,
        selo=((30, 75, 445, 142), "ACABADA DE FAZER", "FRESHLY MADE"),
        apagar=[(40, 195, 650, 695)],
        linhas=[
            Linha((55, 200, 520, 300), "creme", F, "Saída do", "From the"),
            Linha((55, 318, 640, 440), "creme", F, "forno para", "oven to"),
            Linha((55, 448, 632, 532), "amarelo", F, "a tua mesa", "your table"),
            Linha((60, 585, 530, 637), "creme", S, "Massa fresca, ingredientes", "Fresh dough, quality ingredients"),
            Linha((60, 640, 560, 692), "creme", S, "de qualidade e muito queijo.", "and plenty of cheese."),
        ]),
    "entradas-largo": dict(
        larguras=(1260, 1890, 2520), fundo=(120, 10, 9), sombra=6,
        apagar=[(300, 90, 2220, 330), (700, 835, 1820, 925)],
        linhas=[
            Linha((900, 95, 1620, 168), "amarelo", S, "NÃO TE ESQUEÇAS DAS", "DON’T FORGET THE", "centro"),
            Linha((780, 180, 1740, 312), "creme", F, "ENTRADAS!", "STARTERS!", "centro"),
            Linha((800, 840, 1720, 915), "creme", S, "Junta uma entrada ao teu pedido", "Add a starter to your order", "centro"),
        ],
        etiquetas=[((325, 695, 447, 738), "Asas", "Wings"), ((1622, 691, 1866, 738), "Pão de alho", "Garlic bread")]),
    "entradas": dict(
        larguras=(480, 630, 720, 945, 1260), fundo=(120, 10, 9), sombra=3,
        apagar=[(200, 55, 1060, 262), (290, 688, 975, 752)],
        linhas=[
            Linha((400, 62, 860, 125), "amarelo", S, "NÃO TE ESQUEÇAS DAS", "DON’T FORGET THE", "centro"),
            Linha((230, 140, 1030, 255), "creme", F, "ENTRADAS!", "STARTERS!", "centro"),
            Linha((300, 692, 960, 745), "creme", S, "Junta uma entrada ao teu pedido", "Add a starter to your order", "centro"),
        ],
        etiquetas=[((57, 546, 155, 580), "Asas", "Wings"), ((850, 543, 1045, 580), "Pão de alho", "Garlic bread")]),
    "online-largo": dict(
        larguras=(1260, 1890, 2520), sombra=6,
        linhas=[
            Linha((400, 140, 1120, 262), "creme", F, "Encomenda", "Order"),
            Linha((400, 275, 800, 385), "creme", F, "online", "online"),
            Linha((140, 540, 880, 660), "creme", F, "Escolhe, paga e", "Choose, pay and"),
            Linha((140, 662, 880, 752), "amarelo", F, "recebe em casa", "get it delivered"),
            Linha((1740, 845, 2400, 922), "creme", S, "Rápido · Quente · Saboroso", "Fast · Hot · Tasty", "direita"),
        ]),
    "online": dict(
        larguras=(480, 630, 720, 945, 1260), sombra=3,
        linhas=[
            Linha((50, 305, 830, 398), "creme", F, "Encomenda online", "Order online"),
            Linha((50, 520, 600, 612), "creme", F, "Escolhe, paga e", "Choose, pay and"),
            Linha((50, 612, 600, 682), "amarelo", F, "recebe em casa", "get it delivered"),
            Linha((760, 755, 1212, 812), "creme", S, "Rápido · Quente · Saboroso", "Fast · Hot · Tasty", "direita"),
        ]),
}


def gerar(nome, cfg, so_mestre=False):
    larguras = cfg["larguras"]
    mestre = Image.open(os.path.join(BANNERS, nome, f"{max(larguras)}.jpg")).convert("RGB")
    a = np.asarray(mestre)
    escala = mestre.width / (2520 if "largo" in nome else 1260)
    for ln in cfg["linhas"]:
        (wr, hr), (wo, ho) = ln.medir(a)
        print(f"  {ln.pt!r:40} size {ln.tamanho:6.1f}  ink {wo}x{ho}, fitted {wr}x{hr}")
    img = mestre.copy()
    if "fundo" in cfg:
        for caixa in cfg.get("apagar", []):
            apagar_cor(img, caixa, cfg["fundo"])
    else:
        apagar_textura(img, cfg["linhas"], cfg["sombra"])
    if "selo" in cfg:
        selo(img, a, cfg["selo"][0], cfg["fundo"], cfg["selo"][1], cfg["selo"][2], escala)
    for caixa, pt, en in cfg.get("etiquetas", []):
        etiqueta(img, a, caixa, pt, en)
    for ln in cfg["linhas"]:
        ln.desenhar(img, cfg["sombra"])

    destino = os.path.join(BANNERS, f"{nome}-en")
    os.makedirs(destino, exist_ok=True)
    for largura in larguras:
        altura = round(img.height * largura / img.width)
        redim = img if largura == img.width else img.resize((largura, altura), Image.LANCZOS)
        for ext, formato, opcoes in FORMATOS:
            redim.save(os.path.join(destino, f"{largura}.{ext}"), formato, **opcoes)
    return img


if __name__ == "__main__":
    for nome, cfg in BANNERS_EN.items():
        print(nome)
        gerar(nome, cfg)
