#!/usr/bin/env python3
"""Tarjeta de presentación (85x55 mm, 300 dpi), dos caras, estilo elegante.
   - Anverso: símbolo geométrico PSSP + wordmark + QR central + Hospital Son Llàtzer.
   - Reverso: frase  «Cuidar tu suelo pélvico es cuidar tu calidad de vida.»
"""
import segno
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------- Medidas ----------
DPI = 300
MMpx = DPI / 25.4
S = 2
W, H = round(85 * MMpx), round(55 * MMpx)
CW, CH = W * S, H * S
def mm(v): return round(v * MMpx * S)

URL = "https://65dca11464a331.lhr.life"
IMG = "app/static/images/"
DESK = "/Users/alessandroferrero/Desktop/"

# ---------- Paleta ----------
VIOLET   = (90, 79, 156)
VIOLET_S = (124, 114, 196)
INK      = (60, 54, 92)
GREY     = (138, 134, 162)
CREAM    = (252, 251, 255)
PALE     = (244, 242, 251)

# ---------- Fuentes ----------
G  = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GB = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
GI = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
AV = "/System/Library/Fonts/Avenir.ttc"
def f(path, size): return ImageFont.truetype(path, size * S)

# ---------- Utilidades ----------
def load_trim(path):
    im = Image.open(IMG + path).convert("RGBA")
    b = im.split()[3].getbbox()
    return im.crop(b) if b else im

def fit(im, w=None, h=None):
    iw, ih = im.size
    if w and not h: h = round(ih * w / iw)
    if h and not w: w = round(iw * h / ih)
    return im.resize((w, h), Image.LANCZOS)

def fit_box(im, bw_mm, bh_mm):
    bw, bh = bw_mm * MMpx * S, bh_mm * MMpx * S
    iw, ih = im.size
    k = min(bw / iw, bh / ih)
    return im.resize((max(1, round(iw * k)), max(1, round(ih * k))), Image.LANCZOS)

def paste_center(base, im, cx, cy):
    base.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))

def faded(im, factor):
    im = im.copy()
    im.putalpha(im.split()[3].point(lambda a: int(a * factor)))
    return im

def tracked(draw, cx, y, text, font, fill, track):
    ws = [draw.textlength(c, font=font) for c in text]
    total = sum(ws) + track * (len(text) - 1)
    x = cx - total / 2
    for c, wch in zip(text, ws):
        draw.text((x, y), c, font=font, fill=fill)
        x += wch + track

def text_fit(draw, cx, cy, text, path, max_mm, start_pt, fill):
    size = start_pt
    while size > 5 and draw.textlength(text, font=f(path, size)) > max_mm * MMpx * S:
        size -= 1
    draw.text((cx, cy), text, font=f(path, size), fill=fill, anchor="mm")

def gradient_bg():
    top, bot = CREAM, PALE
    col = Image.new("RGB", (1, CH))
    for y in range(CH):
        t = y / (CH - 1)
        col.putpixel((0, y), tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return col.resize((CW, CH)).convert("RGBA")

def elegant_border(draw):
    o, i = mm(3.0), mm(4.2)
    draw.rounded_rectangle([o, o, CW - o, CH - o], radius=mm(3.2),
                           outline=VIOLET, width=max(2, mm(0.32)))
    draw.rounded_rectangle([i, i, CW - i, CH - i], radius=mm(2.3),
                           outline=VIOLET_S, width=max(1, mm(0.12)))

def soft_tile(card, cx, cy, tile, radius):
    sh = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    off = mm(0.9)
    ds.rounded_rectangle([cx - tile // 2, cy - tile // 2 + off, cx + tile // 2, cy + tile // 2 + off],
                         radius=radius, fill=(90, 79, 156, 70))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(mm(1.1))))
    ImageDraw.Draw(card).rounded_rectangle(
        [cx - tile // 2, cy - tile // 2, cx + tile // 2, cy + tile // 2],
        radius=radius, fill=(255, 255, 255, 255), outline=VIOLET_S, width=max(2, mm(0.26)))

# ---------- Versión imprenta: sangrado 3 mm + marcas de corte ----------
def imprenta(trim):
    """Recibe la cara a tamaño de corte (RGB, 85x55mm) y devuelve el archivo de
    impresión: fondo extendido 3 mm (sangrado, por replicación de bordes) y
    marcas de corte en las esquinas, sobre margen blanco."""
    px = DPI / 25.4
    bleed = round(3 * px)
    marklen = round(4 * px)
    margin = bleed + marklen
    tw, th = trim.size

    # 1) Extender el borde 3 mm hacia fuera (sangrado)
    bw, bh = tw + 2 * bleed, th + 2 * bleed
    bl = Image.new("RGB", (bw, bh))
    bl.paste(trim, (bleed, bleed))
    bl.paste(trim.crop((0, 0, 1, th)).resize((bleed, th)), (0, bleed))
    bl.paste(trim.crop((tw - 1, 0, tw, th)).resize((bleed, th)), (tw + bleed, bleed))
    bl.paste(trim.crop((0, 0, tw, 1)).resize((tw, bleed)), (bleed, 0))
    bl.paste(trim.crop((0, th - 1, tw, th)).resize((tw, bleed)), (bleed, th + bleed))
    bl.paste(trim.crop((0, 0, 1, 1)).resize((bleed, bleed)), (0, 0))
    bl.paste(trim.crop((tw - 1, 0, tw, 1)).resize((bleed, bleed)), (tw + bleed, 0))
    bl.paste(trim.crop((0, th - 1, 1, th)).resize((bleed, bleed)), (0, th + bleed))
    bl.paste(trim.crop((tw - 1, th - 1, tw, th)).resize((bleed, bleed)), (tw + bleed, th + bleed))

    # 2) Lienzo con margen blanco para las marcas
    CWp, CHp = tw + 2 * margin, th + 2 * margin
    canvas = Image.new("RGB", (CWp, CHp), (255, 255, 255))
    canvas.paste(bl, (margin - bleed, margin - bleed))

    # 3) Marcas de corte (líneas finas en las esquinas, señalando el corte)
    d = ImageDraw.Draw(canvas)
    col = (40, 40, 40)
    w = max(1, round(0.2 * px))
    g = margin - bleed                      # las marcas llegan hasta el sangrado
    L, R, T, B = margin, margin + tw, margin, margin + th
    d.line([L, 0, L, g], fill=col, width=w);            d.line([0, T, g, T], fill=col, width=w)
    d.line([R, 0, R, g], fill=col, width=w);            d.line([R + bleed, T, CWp, T], fill=col, width=w)
    d.line([L, B + bleed, L, CHp], fill=col, width=w);  d.line([0, B, g, B], fill=col, width=w)
    d.line([R, B + bleed, R, CHp], fill=col, width=w);  d.line([R + bleed, B, CWp, B], fill=col, width=w)
    return canvas

# ====================================================================
#  ANVERSO
# ====================================================================
def anverso():
    card = gradient_bg()
    draw = ImageDraw.Draw(card)
    elegant_border(draw)
    cx = CW // 2

    # ----- QR centrado (único protagonista), más reducido -----
    qy, tile, qr_px = mm(20), mm(29), mm(23.5)
    soft_tile(card, cx, qy, tile, mm(2))
    paste_center(card, fit(Image.open(DESK + "qr-tarjeta.png").convert("RGBA"), w=qr_px), cx, qy)
    draw = ImageDraw.Draw(card)
    tracked(draw, cx, qy + tile // 2 + mm(2.3), "ESCANÉAME · EMPIEZA HOY", f(AV, 7.5), VIOLET, 4 * S)

    # Filete fino separador
    draw.line([cx - mm(10), mm(40), cx + mm(10), mm(40)], fill=VIOLET_S, width=max(1, mm(0.14)))

    # ----- Hospital Son Llàtzer: discreto, centrado abajo (sin tocar el marco) -----
    tracked(draw, cx, mm(43), "EN COLABORACIÓN CON", f(AV, 5.5), GREY, 3 * S)
    paste_center(card, fit_box(load_trim("logo-son-llatzer.png"), 26, 5), cx, mm(47.3))

    return card.resize((W, H), Image.LANCZOS)

# ====================================================================
#  REVERSO
# ====================================================================
def reverso():
    card = gradient_bg()
    motivo = load_trim("motivo-pssp-lila.png")

    # Marca de agua central grande y tenue
    paste_center(card, faded(fit(motivo, h=mm(72)), 0.06), CW // 2, CH // 2)

    draw = ImageDraw.Draw(card)
    elegant_border(draw)
    cx = CW // 2

    # Símbolo pequeño arriba
    paste_center(card, fit(motivo, h=mm(12)), cx, mm(14))

    # ----- Frase en UNA sola línea, resaltada en banda (píldora) -----
    phrase = "«Cuidar tu suelo pélvico es cuidar tu calidad de vida.»"
    size = 18
    while size > 7 and draw.textlength(phrase, font=f(GB, size)) > mm(67):
        size -= 1
    fnt = f(GB, size)
    cyP = mm(28)
    tw = draw.textlength(phrase, font=fnt)
    asc, desc = fnt.getmetrics(); th = asc + desc
    padx, pady = mm(4.5), mm(2.4)
    band = [cx - tw / 2 - padx, cyP - th / 2 - pady, cx + tw / 2 + padx, cyP + th / 2 + pady]
    # sombra suave de la banda
    sh = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [band[0], band[1] + mm(0.7), band[2], band[3] + mm(0.7)],
        radius=(band[3] - band[1]) / 2, fill=(90, 79, 156, 45))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(mm(0.9))))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle(band, radius=(band[3] - band[1]) / 2,
                           fill=(237, 233, 250, 255), outline=VIOLET_S, width=max(1, mm(0.14)))
    draw.text((cx, cyP), phrase, font=fnt, fill=VIOLET, anchor="mm")

    # Filete decorativo
    yl = mm(38)
    draw.line([cx - mm(12), yl, cx + mm(12), yl], fill=VIOLET_S, width=max(1, mm(0.16)))
    draw.ellipse([cx - 3 * S, yl - 3 * S, cx + 3 * S, yl + 3 * S], fill=VIOLET_S)

    # Firma de marca
    tracked(draw, cx, mm(45.5), "PROMOCIÓN · SALUD · SUELO PÉLVICO", f(AV, 7), VIOLET, 4 * S)

    return card.resize((W, H), Image.LANCZOS)

# ---------- QR nítido en color de marca ----------
segno.make(URL, error="h").save(DESK + "qr-tarjeta.png", scale=18, border=1,
                                dark="#5a4f9c", light="#ffffff")

front, back = anverso(), reverso()
front.convert("RGB").save(DESK + "tarjeta-anverso.png", dpi=(DPI, DPI))
back.convert("RGB").save(DESK + "tarjeta-reverso.png", dpi=(DPI, DPI))

gap = 40
combo = Image.new("RGB", (W * 2 + gap * 3, H + gap * 2), (236, 234, 244))
combo.paste(front.convert("RGB"), (gap, gap))
combo.paste(back.convert("RGB"), (W + gap * 2, gap))
combo.save(DESK + "tarjeta-vista.png")

front.convert("RGB").save(DESK + "tarjeta-presentacion.pdf", "PDF", resolution=DPI,
                          save_all=True, append_images=[back.convert("RGB")])

# ---------- Archivos de IMPRENTA (sangrado 3 mm + marcas de corte) ----------
front_p = imprenta(front.convert("RGB"))
back_p = imprenta(back.convert("RGB"))
front_p.save(DESK + "tarjeta-anverso-IMPRENTA.png", dpi=(DPI, DPI))
back_p.save(DESK + "tarjeta-reverso-IMPRENTA.png", dpi=(DPI, DPI))
front_p.save(DESK + "tarjeta-IMPRENTA.pdf", "PDF", resolution=DPI,
             save_all=True, append_images=[back_p])

# ---------- Hoja A4 para imprimir EN CASA a doble cara ----------
# Rejilla 2x5 (10 tarjetas), centrada y simétrica: así, al imprimir a doble
# cara, el reverso cae justo detrás del frente sea cual sea el modo de volteo.
def a4_sheet(card):
    px = DPI / 25.4
    A4 = (round(210 * px), round(297 * px))
    cols, rows = 2, 5
    cw, ch = card.size
    gw, gh = cols * cw, rows * ch
    mx, my = (A4[0] - gw) // 2, (A4[1] - gh) // 2
    sheet = Image.new("RGB", A4, (255, 255, 255))
    for r in range(rows):
        for c in range(cols):
            sheet.paste(card, (mx + c * cw, my + r * ch))
    d = ImageDraw.Draw(sheet)
    cut, w = (175, 175, 190), max(1, round(0.18 * px))
    for c in range(cols + 1):
        x = mx + c * cw; d.line([x, my, x, my + gh], fill=cut, width=w)
    for r in range(rows + 1):
        y = my + r * ch; d.line([mx, y, mx + gw, y], fill=cut, width=w)
    return sheet

sheet_f = a4_sheet(front.convert("RGB"))
sheet_b = a4_sheet(back.convert("RGB"))
sheet_f.save(DESK + "tarjeta-A4-frente.png", dpi=(DPI, DPI))
sheet_b.save(DESK + "tarjeta-A4-retro.png", dpi=(DPI, DPI))
sheet_f.save(DESK + "tarjeta-A4-CASA.pdf", "PDF", resolution=DPI,
             save_all=True, append_images=[sheet_b])
print("OK pantalla:", W, "x", H, "| imprenta:", front_p.size, "| A4:", sheet_f.size)
