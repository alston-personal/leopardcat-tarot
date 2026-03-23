#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]



def vertical_gradient(size, top_color, bottom_color):
    width, height = size
    image = Image.new("RGB", size, tuple(top_color))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        blend = y / max(height - 1, 1)
        color = tuple(
            int(top_color[i] * (1 - blend) + bottom_color[i] * blend)
            for i in range(3)
        )
        draw.line((0, y, width, y), fill=color)
    return image


def draw_forest(draw: ImageDraw.ImageDraw, height: int):
    trunks = [(150, 280), (220, 250), (310, 300), (410, 230), (520, 260)]
    for x, top in trunks:
        draw.rectangle((x, top, x + 34, height - 520), fill=(28, 41, 29))
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


def draw_reeds(draw: ImageDraw.ImageDraw):
    for i in range(10):
        x = 180 + i * 58
        draw.line((x, 1860, x - 12, 1240), fill=(148, 146, 84), width=5)
        draw.line((x + 18, 1860, x + 4, 1320), fill=(118, 128, 73), width=4)
        draw.ellipse((x - 16, 1212, x + 20, 1262), fill=(132, 119, 72))


def draw_stream(base: Image.Image):
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.polygon(
        [(180, 1820), (380, 1450), (770, 1360), (1140, 1500), (1280, 1840), (1080, 1930), (760, 1860), (420, 1940)],
        fill=(116, 146, 170, 160),
    )
    draw.polygon(
        [(230, 1790), (415, 1490), (755, 1428), (1075, 1532), (1192, 1810), (1032, 1868), (748, 1814), (452, 1884)],
        fill=(191, 218, 229, 100),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(3))
    base.alpha_composite(overlay)


def draw_mist(base: Image.Image):
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((120, 1060, 960, 1700), fill=(206, 223, 236, 36))
    draw.ellipse((280, 1180, 1290, 1810), fill=(186, 206, 220, 28))
    draw.ellipse((40, 1360, 880, 1980), fill=(219, 229, 237, 24))
    overlay = overlay.filter(ImageFilter.GaussianBlur(34))
    base.alpha_composite(overlay)


def draw_glowing_wood(base: Image.Image):
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((520, 1650, 720, 1775), fill=(182, 230, 175, 110))
    draw.ellipse((560, 1680, 760, 1805), fill=(214, 249, 205, 72))
    overlay = overlay.filter(ImageFilter.GaussianBlur(18))
    base.alpha_composite(overlay)


def draw_arch_trees(draw: ImageDraw.ImageDraw, width: int, height: int):
    for x in (145, 1120):
        draw.rectangle((x, 360, x + 46, height - 520), fill=(34, 42, 40))
    draw.arc((120, 250, width - 120, 1320), start=194, end=346, fill=(52, 72, 66), width=24)


def draw_headlights(base: Image.Image, width: int, height: int):
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
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
    draw.polygon([(720, 1388), (750, 1328), (785, 1396)], fill=(101, 67, 46))
    draw.polygon([(785, 1396), (820, 1334), (840, 1410)], fill=(101, 67, 46))
    draw.ellipse((730, 1360, 752, 1384), fill=(242, 237, 220))
    draw.ellipse((798, 1368, 820, 1392), fill=(242, 237, 220))
    draw.ellipse((770, 1425, 780, 1435), fill=(34, 27, 25))
    draw.line((772, 1435, 765, 1452), fill=(34, 27, 25), width=3)
    draw.line((778, 1435, 785, 1452), fill=(34, 27, 25), width=3)
    draw.line((742, 1442, 694, 1434), fill=(41, 31, 28), width=2)
    draw.line((744, 1455, 696, 1462), fill=(41, 31, 28), width=2)
    draw.line((800, 1442, 848, 1434), fill=(41, 31, 28), width=2)
    draw.line((798, 1455, 846, 1464), fill=(41, 31, 28), width=2)

    for leg in [(490, 1620, 525, 1930), (560, 1612, 595, 1890), (640, 1610, 675, 1830)]:
        draw.rectangle(leg, fill=(186, 142, 91))
    draw.polygon([(715, 1612), (748, 1600), (770, 1835), (733, 1842)], fill=(191, 147, 92))
    draw.line([(415, 1580), (335, 1622), (250, 1696), (210, 1772)], fill=(177, 133, 84), width=34, joint="curve")

    for spot_x, spot_y in [
        (500, 1515), (560, 1535), (620, 1520), (545, 1585), (615, 1590),
        (745, 1455), (790, 1452), (510, 1680), (585, 1675), (655, 1670),
    ]:
        draw.ellipse((spot_x, spot_y, spot_x + 26, spot_y + 18), fill=(74, 52, 42))


def draw_adult_leopard_cat(draw: ImageDraw.ImageDraw):
    body = [(380, 1490), (560, 1410), (760, 1438), (860, 1538), (760, 1650), (510, 1668)]
    draw.polygon(body, fill=(176, 133, 78))
    chest = [(680, 1450), (842, 1406), (940, 1496), (860, 1612), (720, 1624)]
    draw.polygon(chest, fill=(221, 189, 144))
    head = (820, 1328, 995, 1488)
    draw.ellipse(head, fill=(189, 144, 90))
    draw.polygon([(846, 1336), (884, 1260), (916, 1350)], fill=(91, 59, 42))
    draw.polygon([(920, 1348), (965, 1268), (991, 1376)], fill=(91, 59, 42))
    draw.ellipse((864, 1312, 888, 1338), fill=(245, 239, 223))
    draw.ellipse((944, 1322, 968, 1348), fill=(245, 239, 223))
    draw.ellipse((905, 1392, 918, 1404), fill=(33, 27, 22))
    draw.line((911, 1404, 904, 1420), fill=(33, 27, 22), width=3)
    draw.line((916, 1404, 924, 1420), fill=(33, 27, 22), width=3)
    for leg in [(492, 1620, 530, 1928), (590, 1608, 628, 1888), (720, 1600, 756, 1848)]:
        draw.rectangle(leg, fill=(168, 126, 75))
    draw.polygon([(828, 1596), (866, 1584), (892, 1862), (852, 1872)], fill=(172, 129, 78))
    draw.line([(360, 1550), (270, 1592), (188, 1696), (160, 1798)], fill=(162, 120, 74), width=32, joint="curve")
    for spot_x, spot_y in [
        (472, 1492), (540, 1516), (620, 1502), (694, 1510), (575, 1582),
        (676, 1588), (858, 1424), (914, 1430), (526, 1684), (610, 1682)
    ]:
        draw.ellipse((spot_x, spot_y, spot_x + 30, spot_y + 20), fill=(70, 48, 37))


def draw_streamside_cat(draw: ImageDraw.ImageDraw):
    body = [(470, 1508), (620, 1450), (760, 1462), (840, 1540), (770, 1616), (586, 1632)]
    draw.polygon(body, fill=(180, 139, 90))
    chest = [(674, 1488), (808, 1460), (872, 1518), (822, 1596), (706, 1608)]
    draw.polygon(chest, fill=(225, 194, 151))
    head = (782, 1366, 930, 1498)
    draw.ellipse(head, fill=(190, 149, 95))
    draw.polygon([(806, 1372), (842, 1306), (878, 1382)], fill=(93, 61, 43))
    draw.polygon([(872, 1380), (918, 1308), (934, 1418)], fill=(93, 61, 43))
    draw.ellipse((824, 1350, 844, 1372), fill=(242, 238, 228))
    draw.ellipse((892, 1358, 912, 1380), fill=(242, 238, 228))
    draw.ellipse((860, 1420, 872, 1430), fill=(35, 28, 23))
    for leg in [(560, 1608, 592, 1830), (646, 1602, 680, 1802)]:
        draw.rectangle(leg, fill=(171, 131, 80))
    draw.line([(450, 1566), (376, 1610), (320, 1700), (308, 1802)], fill=(167, 126, 79), width=26, joint="curve")
    for spot_x, spot_y in [(544, 1518), (604, 1538), (672, 1528), (744, 1520), (834, 1438), (588, 1590)]:
        draw.ellipse((spot_x, spot_y, spot_x + 24, spot_y + 16), fill=(74, 51, 41))


def draw_main_image(base: Image.Image, config: dict):
    main_image = config.get("main_image")
    width, height = base.size

    if main_image:
        image_path = ROOT / main_image
        if image_path.exists():
            art = Image.open(image_path).convert("RGBA")
            
            # --- Safe Trim (Remove AI-generated margins/borders) ---
            SAFE_TRIM = 20
            img_w, img_h = art.size
            if img_w > SAFE_TRIM * 2 and img_h > SAFE_TRIM * 2:
                art = art.crop((SAFE_TRIM, SAFE_TRIM, img_w - SAFE_TRIM, img_h - SAFE_TRIM))
                img_w, img_h = art.size # Update dimensions after trim

            # --- Aspect Ratio Cover (Center Crop) Logic ---
            target_w = width - 220
            target_h = height - 700
            
            img_ratio = img_w / img_h
            target_ratio = target_w / target_h
            
            if img_ratio > target_ratio:
                # Image is relatively wider than target - crop left/right
                crop_w = int(target_ratio * img_h)
                offset = (img_w - crop_w) // 2
                art = art.crop((offset, 0, offset + crop_w, img_h))
            else:
                # Image is relatively taller than target - crop top/bottom
                crop_h = int(img_w / target_ratio)
                offset = (img_h - crop_h) // 2
                art = art.crop((0, offset, img_w, offset + crop_h))
            
            art = art.resize((target_w, target_h), Image.Resampling.LANCZOS)
            base.alpha_composite(art, (110, 360))
            return
        else:
            raise FileNotFoundError(f"Main image not found at {image_path}")

    scene = config.get("scene", {})
    draw = ImageDraw.Draw(base)
    if scene.get("forest"):
        draw_forest(draw, height)
    if scene.get("theme") == "field-edge-adaptation":
        draw_reeds(draw)
    if scene.get("theme") == "streamside-intuition":
        draw_arch_trees(draw, width, height)
        draw_stream(base)
        draw_mist(base)
    if scene.get("road"):
        draw_road(draw)
    if scene.get("grass"):
        draw_grass(draw)
    if scene.get("subject") == "juvenile-leopard-cat":
        draw_leopard_cat(draw)
    elif scene.get("subject") == "adult-leopard-cat":
        draw_adult_leopard_cat(draw)
    elif scene.get("subject") == "streamside-leopard-cat":
        draw_streamside_cat(draw)
    if scene.get("headlights"):
        draw_headlights(base, width, height)
    if scene.get("theme") == "streamside-intuition":
        draw_glowing_wood(base)


def draw_frame(base: Image.Image, width: int, height: int, palette: dict):
    draw = ImageDraw.Draw(base)
    
    # Outer Frames
    draw.rounded_rectangle((36, 36, width - 36, height - 36), radius=36, outline=tuple(palette["frame"]), width=8)
    draw.rounded_rectangle((90, 90, width - 90, height - 90), radius=26, outline=tuple(palette["frame_inner"]), width=3)
    
    # --- GLASS PANELS LOGIC (REFINED for MUSEUM-GRADE HARMONY) ---
    panels = [
        (150, 120, width - 150, 320), # Top Title Panel
        (240, height - 340, width - 240, height - 160) # Bottom Info Panel
    ]
    
    for box in panels:
        # 1. Extract the area to blur
        crop = base.crop(box)
        # 2. Apply a heavy blur for the glass effect (increase radius to 30 for deeper integration)
        blurred = crop.filter(ImageFilter.GaussianBlur(radius=30))
        # 3. Create a mask for rounded corners
        mask = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
        mask_draw = ImageDraw.Draw(mask)
        radius = 24 if box[1] < 500 else 22
        mask_draw.rounded_rectangle((0, 0, mask.size[0], mask.size[1]), radius=radius, fill=255)
        # 4. Composite the blurred background back
        base.paste(blurred, box, mask=mask)
        
        # 5. Draw the semi-transparent overlay (reduced opacity for better harmony: 100/255)
        panel_fill = list(palette["panel"])
        if len(panel_fill) == 3: panel_fill.append(100) # Slightly more translucent
        draw.rounded_rectangle(box, radius=radius, fill=tuple(panel_fill), outline=tuple(palette["frame"]), width=3)
        
        # 6. Subtle Inset Shadow feel (Darken top/left slightly)
        draw.rounded_rectangle(box, radius=radius, outline=(0, 0, 0, 60), width=1)
        
        # 7. Polished Top-Left Highlight (Beveled feel)
        highlight_color = (255, 255, 255, 65)
        draw.arc((box[0]+2, box[1]+2, box[0]+radius*2, box[1]+radius*2), start=180, end=270, fill=highlight_color, width=3)
        draw.line((box[0] + radius, box[1] + 2, box[2] - radius, box[1] + 2), fill=highlight_color, width=3)
        draw.line((box[0] + 2, box[1] + radius, box[0] + 2, box[3] - radius), fill=highlight_color, width=3)


def load_font(size: int, bold: bool = False):
    # Switching to Serif for 1900s lithographic historical feel
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    if not Path(path).exists():
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size=size)


def draw_text(draw: ImageDraw.ImageDraw, width: int, height: int, config: dict, palette: dict):
    # Width constraints (Panel width - absolute padding)
    title_max_w = (width - 300) - 80 
    subtitle_max_w = (width - 480) - 60
    numeral_max_w = (width - 480) - 60

    def draw_spaced_text(draw, text, y, font_size, is_bold, fill, max_w, letter_spacing=10):
        # Local recursive optimization to fit text
        current_spacing = letter_spacing
        current_font_size = font_size
        
        while True:
            font = load_font(current_font_size, bold=is_bold)
            char_widths = [draw.textlength(c, font=font) for c in text]
            total_w = sum(char_widths) + (len(text)-1)*current_spacing
            
            if total_w <= max_w or (current_font_size <= 24 and current_spacing <= 2):
                break
            
            # Step 1: Reduce spacing first
            if current_spacing > 2:
                current_spacing -= 1
            else:
                # Step 2: Reduce font size
                current_font_size -= 2

        current_x = (width - total_w) / 2
        for char in text:
            draw.text((current_x, y), char, font=font, fill=fill)
            current_x += draw.textlength(char, font=font) + current_spacing

    title = config["title"]
    if isinstance(title, dict):
        title = title.get("en", "")
    
    numeral = str(config["number"])
    subtitle = str(config["subtitle"])

    # Top Panel
    draw_spaced_text(draw, title, 168, 84, False, tuple(palette["text_primary"]), title_max_w, letter_spacing=12)
    # Bottom Panel (Numeral & Subtitle)
    draw_spaced_text(draw, numeral, height - 320, 80, True, tuple(palette["text_primary"]), numeral_max_w, letter_spacing=10)
    draw_spaced_text(draw, subtitle, height - 235, 42, False, tuple(palette["text_secondary"]), subtitle_max_w, letter_spacing=4)


def apply_paper_grain(image: Image.Image, intensity: int = 15):
    import random
    width, height = image.size
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            noise = random.randint(-intensity, intensity)
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise))
            )
    return image


def render_card(config: dict, output_override: str | None = None):
    width = config["size"]["width"]
    height = config["size"]["height"]
    palette = config["palette"]

    base_rgb = vertical_gradient((width, height), palette["top"], palette["bottom"])
    base = base_rgb.convert("RGBA")

    draw_main_image(base, config)
    draw = ImageDraw.Draw(base)
    draw_frame(base, width, height, palette)
    draw_text(draw, width, height, config, palette)

    # FINAL FINISHING: Apply paper grain to the whole card to merge AI and UI layers
    final_img = base.convert("RGB")
    final_img = apply_paper_grain(final_img, intensity=8)
    
    output_rel = output_override or config["output"]
    output_path = ROOT / output_rel
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_img.save(output_path, quality=95)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Render a tarot card from a JSON config.")
    parser.add_argument("config", help="Path to card JSON, relative to repo root or absolute path")
    parser.add_argument("--output", help="Override output path, relative to repo root or absolute path")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path

    config = json.loads(config_path.read_text())
    output = render_card(config, args.output)
    print(output)


if __name__ == "__main__":
    main()
