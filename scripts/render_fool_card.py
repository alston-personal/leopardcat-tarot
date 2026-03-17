#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path("/home/ubuntu/leopardcat-tarot")
OUTPUT_DIR = ROOT / "art" / "renders"
OUTPUT_PATH = OUTPUT_DIR / "card-00-the-fool-v1.png"

WIDTH = 1400
HEIGHT = 2420


def load_font(size: int, bold: bool = False):
    if bold:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    else:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size=size)


def vertical_gradient(size, top_color, bottom_color):
    width, height = size
    image = Image.new("RGB", size, top_color)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        blend = y / max(height - 1, 1)
        color = tuple(
            int(top_color[i] * (1 - blend) + bottom_color[i] * blend)
            for i in range(3)
        )
        draw.line((0, y, width, y), fill=color)
    return image


def draw_forest(draw: ImageDraw.ImageDraw):
    trunks = [
        (150, 280),
        (220, 250),
        (310, 300),
        (410, 230),
        (520, 260),
    ]
    for x, top in trunks:
        draw.rectangle((x, top, x + 34, HEIGHT - 520), fill=(28, 41, 29))
        draw.ellipse((x - 90, top - 20, x + 150, top + 250), fill=(20, 46, 34))
        draw.ellipse((x - 40, top + 30, x + 180, top + 280), fill=(26, 58, 41))


def draw_road(draw: ImageDraw.ImageDraw):
    road = [(820, 640), (1280, 520), (1330, 1760), (700, 2050)]
    draw.polygon(road, fill=(43, 47, 56))
    shoulder = [(760, 670), (825, 640), (705, 2050), (620, 2080)]
    draw.polygon(shoulder, fill=(214, 216, 211))

    for i in range(7):
        x1 = 995 + i * 18
        y1 = 860 + i * 150
        x2 = x1 + 34
        y2 = y1 + 84
        draw.polygon(
            [(x1, y1), (x2, y1 - 8), (x2 + 6, y2), (x1 + 4, y2 + 8)],
            fill=(240, 226, 165),
        )


def draw_grass(draw: ImageDraw.ImageDraw):
    for i in range(0, 760, 18):
        base_x = 50 + i
        draw.line((base_x, 1950, base_x - 25, 1500), fill=(69, 106, 62), width=4)
        draw.line((base_x + 5, 1950, base_x + 30, 1540), fill=(95, 131, 68), width=3)
        draw.line((base_x - 8, 1950, base_x - 40, 1600), fill=(54, 88, 50), width=3)


def draw_headlights(base: Image.Image):
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((1040, 720, 1380, 1040), fill=(255, 209, 96, 70))
    gdraw.ellipse((1120, 780, 1450, 1100), fill=(255, 153, 72, 55))
    gdraw.polygon([(1085, 860), (1330, 760), (1180, 1350)], fill=(255, 214, 106, 48))
    gdraw.polygon([(1110, 890), (1270, 840), (1120, 1440)], fill=(255, 141, 72, 42))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    base.alpha_composite(glow)


def draw_leopard_cat(draw: ImageDraw.ImageDraw):
    body = [(430, 1520), (555, 1465), (660, 1490), (700, 1570), (620, 1645), (470, 1655)]
    draw.polygon(body, fill=(193, 149, 92))
    chest = [(590, 1515), (720, 1450), (785, 1505), (735, 1605), (640, 1628)]
    draw.polygon(chest, fill=(224, 192, 145))
    head = (700, 1385, 840, 1510)
    draw.ellipse(head, fill=(201, 159, 101))
    ear_left = [(720, 1388), (750, 1328), (785, 1396)]
    ear_right = [(785, 1396), (820, 1334), (840, 1410)]
    draw.polygon(ear_left, fill=(101, 67, 46))
    draw.polygon(ear_right, fill=(101, 67, 46))
    draw.ellipse((730, 1360, 752, 1384), fill=(242, 237, 220))
    draw.ellipse((798, 1368, 820, 1392), fill=(242, 237, 220))
    draw.ellipse((770, 1425, 780, 1435), fill=(34, 27, 25))
    draw.line((772, 1435, 765, 1452), fill=(34, 27, 25), width=3)
    draw.line((778, 1435, 785, 1452), fill=(34, 27, 25), width=3)
    draw.line((742, 1442, 694, 1434), fill=(41, 31, 28), width=2)
    draw.line((744, 1455, 696, 1462), fill=(41, 31, 28), width=2)
    draw.line((800, 1442, 848, 1434), fill=(41, 31, 28), width=2)
    draw.line((798, 1455, 846, 1464), fill=(41, 31, 28), width=2)

    legs = [
        (490, 1620, 525, 1930),
        (560, 1612, 595, 1890),
        (640, 1610, 675, 1830),
    ]
    for leg in legs:
        draw.rectangle(leg, fill=(186, 142, 91))
    lifted_leg = [(715, 1612), (748, 1600), (770, 1835), (733, 1842)]
    draw.polygon(lifted_leg, fill=(191, 147, 92))

    tail = [(415, 1580), (335, 1622), (250, 1696), (210, 1772)]
    draw.line(tail, fill=(177, 133, 84), width=34, joint="curve")
    for spot_x, spot_y in [
        (500, 1515), (560, 1535), (620, 1520), (545, 1585), (615, 1590),
        (745, 1455), (790, 1452), (510, 1680), (585, 1675), (655, 1670),
    ]:
        draw.ellipse((spot_x, spot_y, spot_x + 26, spot_y + 18), fill=(74, 52, 42))


def draw_frame(draw: ImageDraw.ImageDraw):
    draw.rounded_rectangle((36, 36, WIDTH - 36, HEIGHT - 36), radius=36, outline=(219, 203, 156), width=8)
    draw.rounded_rectangle((90, 90, WIDTH - 90, HEIGHT - 90), radius=26, outline=(171, 149, 102), width=3)
    draw.rounded_rectangle((150, 120, WIDTH - 150, 320), radius=24, fill=(20, 26, 24), outline=(219, 203, 156), width=3)
    draw.rounded_rectangle((240, HEIGHT - 340, WIDTH - 240, HEIGHT - 160), radius=22, fill=(20, 26, 24), outline=(219, 203, 156), width=3)


def draw_text(draw: ImageDraw.ImageDraw):
    title_font = load_font(84, bold=True)
    subtitle_font = load_font(42, bold=False)
    numeral_font = load_font(64, bold=True)

    title = "THE FOOL"
    numeral = "0"
    subtitle = "Threshold / Curiosity / Risk"

    title_w = draw.textlength(title, font=title_font)
    draw.text(((WIDTH - title_w) / 2, 168), title, font=title_font, fill=(243, 233, 201))

    numeral_w = draw.textlength(numeral, font=numeral_font)
    draw.text(((WIDTH - numeral_w) / 2, HEIGHT - 315), numeral, font=numeral_font, fill=(243, 233, 201))

    subtitle_w = draw.textlength(subtitle, font=subtitle_font)
    draw.text(((WIDTH - subtitle_w) / 2, HEIGHT - 235), subtitle, font=subtitle_font, fill=(198, 186, 151))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_rgb = vertical_gradient((WIDTH, HEIGHT), (12, 22, 36), (42, 69, 51))
    base = base_rgb.convert("RGBA")
    draw = ImageDraw.Draw(base)

    draw_forest(draw)
    draw_road(draw)
    draw_grass(draw)
    draw_leopard_cat(draw)
    draw_frame(draw)
    draw_text(draw)
    draw_headlights(base)

    final = base.convert("RGB")
    final.save(OUTPUT_PATH, quality=95)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
