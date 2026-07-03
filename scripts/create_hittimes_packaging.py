from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUT_IMG = ROOT / "output" / "packaging"
OUT_PDF = ROOT / "output" / "pdf"
OUT_IMG.mkdir(parents=True, exist_ok=True)
OUT_PDF.mkdir(parents=True, exist_ok=True)

DPI = 300
PX_PER_MM = DPI / 25.4
PANEL_MM = 200
SIDE_MM = 35
PANEL = round(PANEL_MM * PX_PER_MM)
SIDE = round(SIDE_MM * PX_PER_MM)
NET = PANEL + SIDE * 2

CREAM = (253, 241, 207, 255)
INK = (37, 36, 34, 255)
BLUE = (154, 220, 232, 255)
BLUE_DARK = (89, 177, 195, 255)
YELLOW = (255, 212, 74, 255)
GREEN = (160, 201, 132, 255)
ORANGE = (247, 146, 0, 255)
PINK = (214, 110, 167, 255)
WHITE = (255, 255, 255, 255)
BLACK = (16, 16, 16, 255)

TIMES = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
TIMES_BOLD = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
HELVETICA = "/System/Library/Fonts/Helvetica.ttc"


def px(mm_value):
    return round(mm_value * PX_PER_MM)


def font(path, size_mm):
    return ImageFont.truetype(path, px(size_mm))


def text_size(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def centered(draw, xy, text, fnt, fill, anchor="mm", **kwargs):
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor, **kwargs)


def wrap_text(draw, text, fnt, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if text_size(draw, test, fnt)[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paragraph(draw, text, box, fnt, fill=INK, leading=1.25, align="left"):
    x, y, w, _h = box
    line_h = round(fnt.size * leading)
    for line in wrap_text(draw, text, fnt, w):
        if align == "center":
            draw.text((x + w / 2, y), line, font=fnt, fill=fill, anchor="ma")
        else:
            draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def draw_waves(draw, w, h, origin="bottom_left", scale=1.0):
    colors = [BLUE, YELLOW, GREEN, PINK]
    width = max(6, round(px(3.8) * scale))
    gap = max(9, round(px(4.2) * scale))
    steps = 130
    if origin == "bottom_left":
        start_x = -px(25)
        start_y = h - px(45)
        for i, color in enumerate(colors):
            pts = []
            for t in range(steps):
                u = t / (steps - 1)
                x = start_x + u * px(115)
                y = start_y + i * gap + math.sin(u * math.pi * 1.35) * px(11)
                pts.append((x, y))
            draw.line(pts, fill=color, width=width, joint="curve")
    else:
        start_x = w - px(100)
        start_y = -px(8)
        for i, color in enumerate(colors):
            pts = []
            for t in range(steps):
                u = t / (steps - 1)
                x = start_x + u * px(120)
                y = start_y + i * gap + math.sin(u * math.pi * 1.15 + 1.0) * px(13)
                pts.append((x, y))
            draw.line(pts, fill=color, width=width, joint="curve")


def recolor_logo(img, color=BLUE_DARK):
    rgba = img.convert("RGBA")
    out = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    src = rgba.load()
    dst = out.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = src[x, y]
            if a:
                dst[x, y] = (*color[:3], a)
    return out


def paste_logo(base, center_x, top_y, width_mm, color=BLUE_DARK, opacity=255):
    logo = Image.open(ASSETS / "hit-times-logo.png")
    logo = recolor_logo(logo, color)
    if opacity < 255:
        alpha = logo.getchannel("A").point(lambda a: int(a * opacity / 255))
        logo.putalpha(alpha)
    target_w = px(width_mm)
    target_h = round(target_w * logo.height / logo.width)
    logo = logo.resize((target_w, target_h), Image.LANCZOS)
    x = round(center_x - target_w / 2)
    y = round(top_y)
    base.alpha_composite(logo, (x, y))
    return x, y, target_w, target_h


def draw_cassette_icon(draw, x, y, s, color):
    r = s * 0.14
    draw.rounded_rectangle((x, y, x + s, y + s * 0.62), radius=r, outline=color, width=max(2, round(s * 0.045)), fill=None)
    draw.rounded_rectangle((x + s * 0.13, y + s * 0.14, x + s * 0.87, y + s * 0.43), radius=r * 0.65, outline=color, width=max(2, round(s * 0.035)))
    for cx in (x + s * 0.32, x + s * 0.68):
        draw.ellipse((cx - s * 0.09, y + s * 0.22, cx + s * 0.09, y + s * 0.40), outline=color, width=max(2, round(s * 0.035)))
    draw.line((x + s * 0.4, y + s * 0.31, x + s * 0.6, y + s * 0.31), fill=color, width=max(2, round(s * 0.025)))


def draw_vinyl(draw, x, y, s, color):
    draw.ellipse((x, y, x + s, y + s), fill=color)
    draw.ellipse((x + s * 0.38, y + s * 0.38, x + s * 0.62, y + s * 0.62), fill=CREAM)
    draw.ellipse((x + s * 0.47, y + s * 0.47, x + s * 0.53, y + s * 0.53), fill=color)
    for r in (0.70, 0.86):
        inset = s * (1 - r) / 2
        draw.arc((x + inset, y + inset, x + s - inset, y + s - inset), 20, 330, fill=WHITE, width=max(1, round(s * 0.015)))


def draw_headphones(draw, x, y, s, color):
    draw.arc((x + s * 0.1, y + s * 0.05, x + s * 0.9, y + s * 0.9), 180, 360, fill=color, width=max(3, round(s * 0.09)))
    draw.rounded_rectangle((x + s * 0.09, y + s * 0.46, x + s * 0.29, y + s * 0.86), radius=s * 0.08, fill=color)
    draw.rounded_rectangle((x + s * 0.71, y + s * 0.46, x + s * 0.91, y + s * 0.86), radius=s * 0.08, fill=color)


def draw_player(draw, x, y, s, color):
    draw.rounded_rectangle((x + s * 0.23, y, x + s * 0.77, y + s), radius=s * 0.09, outline=color, width=max(2, round(s * 0.055)))
    draw.rectangle((x + s * 0.34, y + s * 0.12, x + s * 0.66, y + s * 0.43), outline=color, width=max(2, round(s * 0.045)))
    draw.ellipse((x + s * 0.38, y + s * 0.58, x + s * 0.62, y + s * 0.82), outline=color, width=max(2, round(s * 0.045)))


def draw_qr(draw, x, y, s, seed=1):
    cell = s // 13
    draw.rectangle((x, y, x + cell * 13, y + cell * 13), fill=WHITE, outline=INK, width=max(1, s // 60))
    for yy in range(13):
        for xx in range(13):
            marker = (xx < 3 and yy < 3) or (xx > 9 and yy < 3) or (xx < 3 and yy > 9)
            val = ((xx * 7 + yy * 11 + seed * 5) % 5) < 2
            if marker or val:
                draw.rectangle((x + xx * cell + 1, y + yy * cell + 1, x + (xx + 1) * cell - 1, y + (yy + 1) * cell - 1), fill=BLACK)
    for mx, my in [(0, 0), (10, 0), (0, 10)]:
        draw.rectangle((x + mx * cell, y + my * cell, x + (mx + 3) * cell, y + (my + 3) * cell), outline=WHITE, width=max(1, cell // 2))


def draw_card(draw, x, y, w, h, color, label, angle=0, seed=1):
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((2, 2, w - 2, h - 2), radius=round(w * 0.08), fill=WHITE, outline=color, width=max(3, round(w * 0.018)))
    title_font = font(TIMES_BOLD, max(3.2, w / PX_PER_MM / 18))
    cd.text((w / 2, h * 0.11), label, font=title_font, fill=color, anchor="mm")
    draw_qr(cd, round(w * 0.24), round(h * 0.22), round(w * 0.52), seed)
    icon_s = round(w * 0.2)
    if label == "1980":
        draw_cassette_icon(cd, round(w * 0.09), round(h * 0.22), icon_s, color)
    elif label == "1990":
        draw_vinyl(cd, round(w * 0.09), round(h * 0.26), icon_s * 0.8, color)
    elif label == "2000":
        draw_player(cd, round(w * 0.08), round(h * 0.20), icon_s, color)
    else:
        draw_headphones(cd, round(w * 0.06), round(h * 0.20), icon_s, color)
    cd.pieslice((w * 0.16, h * 0.72, w * 0.84, h * 1.25), 180, 360, fill=color)
    cd.text((w / 2, h * 0.83), "COULEUR", font=font(TIMES_BOLD, max(2.4, w / PX_PER_MM / 22)), fill=WHITE, anchor="mm")
    if angle:
        card = card.rotate(angle, expand=True, resample=Image.BICUBIC)
    return card


def paste_shadow(base, obj, pos, shadow=(0, 0, 0, 40), blur=12, offset=(0, 8)):
    sh = Image.new("RGBA", obj.size, shadow)
    sh.putalpha(obj.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh, (pos[0] + offset[0], pos[1] + offset[1]))
    base.alpha_composite(obj, pos)


def draw_badge(draw, x, y, icon, label, color=BLUE_DARK):
    s = px(9)
    if icon == "age":
        draw.rounded_rectangle((x, y, x + s, y + s), radius=s * 0.18, outline=color, width=max(2, px(0.45)))
        draw.text((x + s / 2, y + s * 0.53), "+10", font=font(TIMES_BOLD, 2.8), fill=color, anchor="mm")
    elif icon == "time":
        draw.polygon([(x + s * 0.25, y), (x + s * 0.75, y), (x + s * 0.58, y + s * 0.48), (x + s * 0.75, y + s), (x + s * 0.25, y + s), (x + s * 0.42, y + s * 0.48)], outline=color, fill=None)
        draw.line((x + s * 0.28, y, x + s * 0.72, y), fill=color, width=max(2, px(0.35)))
        draw.line((x + s * 0.28, y + s, x + s * 0.72, y + s), fill=color, width=max(2, px(0.35)))
    else:
        for i, cx in enumerate([0.25, 0.5, 0.75]):
            draw.ellipse((x + s * cx - s * 0.09, y + s * 0.1, x + s * cx + s * 0.09, y + s * 0.28), fill=color)
            draw.rounded_rectangle((x + s * cx - s * 0.12, y + s * 0.33, x + s * cx + s * 0.12, y + s * 0.78), radius=s * 0.04, fill=color)
    draw.text((x + s / 2, y + s + px(2.2)), label, font=font(HELVETICA, 2.9), fill=color, anchor="ma")


def gigamic_mark(draw, x, y, s):
    draw.rounded_rectangle((x, y, x + s, y + s), radius=s * 0.14, fill=(30, 30, 30, 255))
    draw.ellipse((x - s * 0.1, y + s * 0.58, x + s * 0.45, y + s * 1.08), fill=(229, 56, 59, 255))
    draw.ellipse((x + s * 0.58, y + s * 0.55, x + s * 1.12, y + s * 1.05), fill=(255, 202, 58, 255))
    draw.text((x + s * 0.53, y + s * 0.47), "Gi\nGa\nMic", font=font(TIMES_BOLD, max(1.8, s / PX_PER_MM / 7)), fill=WHITE, anchor="mm", align="center", spacing=-2)


def make_front_panel():
    img = Image.new("RGBA", (PANEL, PANEL), CREAM)
    draw = ImageDraw.Draw(img)
    draw_waves(draw, PANEL, PANEL, "top_right", 1.1)
    draw_waves(draw, PANEL, PANEL, "bottom_left", 1.05)

    # Soft color records behind the main mark.
    for cx, cy, col, r in [
        (px(28), px(34), PINK, px(18)),
        (px(169), px(32), YELLOW, px(14)),
        (px(176), px(156), GREEN, px(18)),
    ]:
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*col[:3], 42))

    paste_logo(img, PANEL / 2, px(27), 86, BLUE_DARK)
    draw.text((PANEL / 2, px(112)), "DE LA CASSETTE À LA PLAYLIST !", font=font(TIMES_BOLD, 6.0), fill=PINK, anchor="mm")
    draw.text((PANEL / 2, px(123)), "Un blind test qui traverse les décennies", font=font(HELVETICA, 3.8), fill=INK, anchor="mm")

    decade_y = px(138)
    decade_items = [("80", BLUE), ("90", YELLOW), ("2000", GREEN), ("2010", PINK)]
    for i, (label, color) in enumerate(decade_items):
        chip_w = px(24 if len(label) < 4 else 31)
        chip_h = px(10)
        cx = PANEL / 2 - px(47) + i * px(32)
        draw.rounded_rectangle((cx - chip_w / 2, decade_y - chip_h / 2, cx + chip_w / 2, decade_y + chip_h / 2), radius=chip_h / 2, fill=color)
        draw.text((cx, decade_y + px(0.1)), label, font=font(TIMES_BOLD, 3.5), fill=WHITE, anchor="mm")

    c_w, c_h = px(25), px(40)
    cards = [
        ("1980", BLUE, -11, px(18), px(118), 2),
        ("1990", YELLOW, 9, px(157), px(118), 3),
        ("2000", GREEN, -6, px(161), px(65), 4),
        ("2010", PINK, 8, px(15), px(65), 5),
    ]
    for label, color, angle, x, y, seed in cards:
        card = draw_card(draw, 0, 0, c_w, c_h, color, label, angle, seed)
        paste_shadow(img, card, (x, y), blur=px(0.8), offset=(px(0.6), px(1.1)))

    gigamic_mark(draw, PANEL - px(21), px(13), px(11))
    badge_y = px(170)
    gap = px(38)
    start = PANEL / 2 - gap
    draw_badge(draw, start - px(4), badge_y, "age", "+10 ans")
    draw_badge(draw, start + gap - px(4), badge_y, "time", "30 min")
    draw_badge(draw, start + gap * 2 - px(4), badge_y, "players", "2-12")
    return img


def make_back_panel():
    img = Image.new("RGBA", (PANEL, PANEL), CREAM)
    draw = ImageDraw.Draw(img)
    draw_waves(draw, PANEL, PANEL, "top_right", 0.9)
    draw_waves(draw, PANEL, PANEL, "bottom_left", 0.9)
    paste_logo(img, PANEL / 2, px(12), 44, BLUE_DARK)

    draw.text((px(17), px(51)), "Voyagez de hit en hit", font=font(TIMES_BOLD, 8.4), fill=PINK)
    body = (
        "Retrouvez les plus grands tubes des années 80, 90, 2000 et 2010. "
        "Écoutez les extraits musicaux via les QR codes, choisissez votre défi "
        "et avancez sur le plateau. Artiste, titre ou année exacte : plus le défi "
        "est difficile, plus votre équipe progresse vite."
    )
    paragraph(draw, body, (px(17), px(64), px(82), px(54)), font(HELVETICA, 3.7), INK, 1.28)

    board = Image.open(ASSETS / "board-flat.png").convert("RGBA")
    board_w = px(77)
    board_h = round(board.height * board_w / board.width)
    board = board.resize((board_w, board_h), Image.LANCZOS)
    board_bg = Image.new("RGBA", (board_w + px(5), board_h + px(5)), (255, 255, 255, 190))
    bd = ImageDraw.Draw(board_bg)
    bd.rounded_rectangle((0, 0, board_bg.width - 1, board_bg.height - 1), radius=px(3), fill=(255, 255, 255, 190), outline=BLUE, width=px(0.5))
    board_bg.alpha_composite(board, (px(2.5), px(2.5)))
    paste_shadow(img, board_bg, (px(108), px(54)), blur=px(0.9), offset=(px(0.6), px(1)))

    step_y = px(121)
    step_w = px(51)
    steps = [
        ("1", "Scannez", "un QR code", BLUE),
        ("2", "Devinez", "l'artiste, le titre ou l'année", PINK),
        ("3", "Avancez", "selon la difficulté choisie", GREEN),
    ]
    for i, (num, title, sub, color) in enumerate(steps):
        x = px(17) + i * px(58)
        draw.rounded_rectangle((x, step_y, x + step_w, step_y + px(38)), radius=px(4), fill=(255, 255, 255, 185), outline=color, width=px(0.55))
        draw.ellipse((x + px(4), step_y + px(4), x + px(15), step_y + px(15)), fill=color)
        draw.text((x + px(9.5), step_y + px(9.9)), num, font=font(TIMES_BOLD, 4), fill=WHITE, anchor="mm")
        draw.text((x + px(25.5), step_y + px(12)), title, font=font(TIMES_BOLD, 4.7), fill=color, anchor="mm")
        paragraph(draw, sub, (x + px(5), step_y + px(20), step_w - px(10), px(16)), font(HELVETICA, 2.9), INK, 1.12, "center")

    band = (px(13), px(164), PANEL - px(13), px(195))
    draw.rounded_rectangle(band, radius=px(4), fill=(255, 255, 255, 205), outline=BLUE, width=px(0.45))
    draw.text((px(18), px(172)), "Contenu de la boîte", font=font(TIMES_BOLD, 4.7), fill=BLUE_DARK)
    draw.text((px(18), px(181)), "80 cartes • 1 plateau • des pions", font=font(HELVETICA, 3.3), fill=INK)
    draw.text((px(18), px(190)), "Édité par les éditions Gigamic - ZA Les Garennes - F-62930 Wimereux", font=font(HELVETICA, 2.05), fill=INK)

    # Demonstration barcode and compliance marks.
    bx, by = px(146), px(171)
    draw.text((bx, by - px(5)), "CE", font=font(HELVETICA, 4.2), fill=INK)
    rx, ry, rs = bx + px(15), by - px(4.2), px(3.4)
    draw.arc((rx - rs, ry - rs, rx + rs, ry + rs), 35, 310, fill=INK, width=px(0.45))
    draw.polygon([(rx + rs * 0.75, ry - rs * 0.12), (rx + rs * 1.35, ry - rs * 0.1), (rx + rs * 1.0, ry + rs * 0.38)], fill=INK)
    for i in range(28):
        line_w = px(0.35 if i % 4 else 0.8)
        xx = bx + px(18) + i * px(0.95)
        draw.line((xx, by, xx, by + px(18)), fill=INK, width=max(1, line_w))
    draw.text((bx + px(31), by + px(21)), "000000 00117", font=font(HELVETICA, 2), fill=INK, anchor="mm")
    gigamic_mark(draw, px(168), px(13), px(11))
    return img


def make_side_panel(kind, orientation="horizontal"):
    if orientation == "horizontal":
        img = Image.new("RGBA", (PANEL, SIDE), CREAM)
        draw = ImageDraw.Draw(img)
        draw_waves(draw, PANEL, SIDE, "top_right", 0.65)
        draw.text((px(12), SIDE / 2), "HIT TIMES", font=font(TIMES_BOLD, 9), fill=BLUE_DARK, anchor="lm")
        draw.text((PANEL - px(12), SIDE / 2), "DE LA CASSETTE À LA PLAYLIST !", font=font(TIMES_BOLD, 4.2), fill=PINK, anchor="rm")
    else:
        img = Image.new("RGBA", (SIDE, PANEL), CREAM)
        draw = ImageDraw.Draw(img)
        draw_waves(draw, SIDE, PANEL, "bottom_left", 0.65)
        tmp = Image.new("RGBA", (PANEL, SIDE), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((px(12), SIDE / 2), "HIT TIMES", font=font(TIMES_BOLD, 8), fill=BLUE_DARK, anchor="lm")
        td.text((PANEL - px(10), SIDE / 2), kind, font=font(HELVETICA, 3.2), fill=PINK, anchor="rm")
        tmp = tmp.rotate(90, expand=True)
        img.alpha_composite(tmp, (0, 0))
    return img


def make_net(center_panel, kind):
    img = Image.new("RGBA", (NET, NET), (0, 0, 0, 0))
    flap = Image.new("RGBA", (SIDE, SIDE), CREAM)
    img.alpha_composite(flap, (0, 0))
    img.alpha_composite(flap, (SIDE + PANEL, 0))
    img.alpha_composite(flap, (0, SIDE + PANEL))
    img.alpha_composite(flap, (SIDE + PANEL, SIDE + PANEL))
    img.alpha_composite(center_panel, (SIDE, SIDE))
    img.alpha_composite(make_side_panel(kind, "horizontal"), (SIDE, 0))
    bottom = make_side_panel(kind, "horizontal").rotate(180)
    img.alpha_composite(bottom, (SIDE, SIDE + PANEL))
    img.alpha_composite(make_side_panel(kind, "vertical"), (0, SIDE))
    right = make_side_panel(kind, "vertical").rotate(180)
    img.alpha_composite(right, (SIDE + PANEL, SIDE))
    return img


def draw_dieline(c, x, y, scale=1.0):
    side = SIDE_MM * mm * scale
    panel = PANEL_MM * mm * scale
    net = (PANEL_MM + 2 * SIDE_MM) * mm * scale
    c.saveState()
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.45)
    # Solid cut lines.
    c.rect(x, y, net, net, stroke=1, fill=0)
    c.line(x, y + side, x + side, y + side)
    c.line(x, y + side + panel, x + side, y + side + panel)
    c.line(x + side + panel, y + side, x + net, y + side)
    c.line(x + side + panel, y + side + panel, x + net, y + side + panel)

    # Fold lines: central panel, sides, and glue tabs.
    c.setDash(4, 3)
    c.setStrokeColorRGB(0.95, 0.38, 0.0)
    c.line(x + side, y + side, x + side + panel, y + side)
    c.line(x + side, y + side + panel, x + side + panel, y + side + panel)
    c.line(x + side, y + side, x + side, y + side + panel)
    c.line(x + side + panel, y + side, x + side + panel, y + side + panel)
    c.line(x + side, y, x + side, y + side)
    c.line(x + side + panel, y, x + side + panel, y + side)
    c.line(x + side, y + side + panel, x + side, y + net)
    c.line(x + side + panel, y + side + panel, x + side + panel, y + net)
    c.restoreState()


def save_pdf(front, back, lid, bottom):
    pdf_path = OUT_PDF / "hittimes_packaging_print.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=landscape(A3))
    page_w, page_h = landscape(A3)
    net_mm = PANEL_MM + 2 * SIDE_MM
    net_w = net_mm * mm
    x = (page_w - net_w) / 2
    y = (page_h - net_w) / 2
    for title, img in [("COUVERCLE", lid), ("FOND", bottom)]:
        c.drawImage(ImageReader(img), x, y, width=net_w, height=net_w, mask="auto")
        draw_dieline(c, x, y)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(10 * mm, page_h - 8 * mm, f"HIT TIMES - {title} - format central 200 x 200 mm, tranche 35 mm, pattes de collage")
        c.showPage()

    for title, img in [("FACE AVANT", front), ("DOS", back)]:
        c.setPageSize((PANEL_MM * mm, PANEL_MM * mm))
        c.drawImage(ImageReader(img), 0, 0, width=PANEL_MM * mm, height=PANEL_MM * mm, mask="auto")
        c.showPage()
    c.save()
    return pdf_path


def make_mockup(front):
    canvas_img = Image.new("RGBA", (1600, 1100), (245, 248, 248, 255))
    draw = ImageDraw.Draw(canvas_img)
    draw.ellipse((250, 860, 1320, 1035), fill=(0, 0, 0, 28))
    front_small = front.resize((700, 700), Image.LANCZOS)
    side = Image.new("RGBA", (230, 700), CREAM)
    sd = ImageDraw.Draw(side)
    draw_waves(sd, side.width, side.height, "bottom_left", 0.55)
    vertical = Image.new("RGBA", (700, 230), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vertical)
    vd.text((350, 88), "HIT TIMES", font=font(TIMES_BOLD, 30 / PX_PER_MM), fill=BLUE_DARK, anchor="mm")
    vd.text((350, 138), "DE LA CASSETTE À LA PLAYLIST !", font=font(TIMES_BOLD, 12 / PX_PER_MM), fill=PINK, anchor="mm")
    vertical = vertical.rotate(90, expand=True)
    side.alpha_composite(vertical, (0, 0))
    # Simple angled box preview.
    canvas_img.alpha_composite(side, (350, 230))
    canvas_img.alpha_composite(front_small, (545, 210))
    draw.line((545, 210, 350, 230), fill=(180, 180, 160, 255), width=3)
    draw.line((545, 910, 350, 930), fill=(180, 180, 160, 255), width=3)
    draw.line((350, 230, 350, 930), fill=(120, 120, 105, 255), width=3)
    draw.line((545, 210, 1245, 210), fill=(235, 225, 190, 255), width=3)
    draw.line((1245, 210, 1245, 910), fill=(120, 120, 105, 255), width=3)
    return canvas_img


def main():
    front = make_front_panel()
    back = make_back_panel()
    lid = make_net(front, "Couvercle")
    bottom = make_net(back, "Fond de boîte")

    front_path = OUT_IMG / "hittimes_packaging_front.png"
    back_path = OUT_IMG / "hittimes_packaging_back.png"
    lid_path = OUT_IMG / "hittimes_packaging_lid_net.png"
    bottom_path = OUT_IMG / "hittimes_packaging_bottom_net.png"
    mock_path = OUT_IMG / "hittimes_packaging_mockup.png"
    front.save(front_path)
    back.save(back_path)
    lid.save(lid_path)
    bottom.save(bottom_path)
    make_mockup(front).save(mock_path)
    pdf_path = save_pdf(front, back, lid, bottom)
    print(pdf_path)
    print(front_path)
    print(back_path)
    print(mock_path)


if __name__ == "__main__":
    main()
