#!/usr/bin/env python3
"""
LeopardCat Tarot - A4 DIY Print-at-Home PDF Generator
Renders the complete 78-card deck into 300 DPI A4 sheets (4 cards per page, 70x120mm standard tarot size).
Supports duplex-aligned printing, crop marks, cutting guides, and card back sheets.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "website" / "manifest.json"
DEFAULT_RENDERS_DIR = ROOT / "art" / "renders"
CARD_BACK_SVG = ROOT / "website" / "public" / "art" / "card-back.svg"
CARD_BACK_PNG = DEFAULT_RENDERS_DIR / "card-back.png"

# A4 Dimensions at 300 DPI (210mm x 297mm)
DPI = 300
MM_TO_INCH = 25.4
A4_W_MM = 210.0
A4_H_MM = 297.0
PAGE_WIDTH = round(A4_W_MM / MM_TO_INCH * DPI)   # 2480 px
PAGE_HEIGHT = round(A4_H_MM / MM_TO_INCH * DPI)  # 3508 px

# Standard Tarot Dimensions (70mm x 120mm)
CARD_W_MM = 70.0
CARD_H_MM = 120.0
CARD_WIDTH = round(CARD_W_MM / MM_TO_INCH * DPI)   # 827 px
CARD_HEIGHT = round(CARD_H_MM / MM_TO_INCH * DPI)  # 1417 px

COLS = 2
ROWS = 2
CARDS_PER_PAGE = COLS * ROWS  # 4 cards

TOTAL_GRID_W = COLS * CARD_WIDTH   # 1654 px
TOTAL_GRID_H = ROWS * CARD_HEIGHT  # 2834 px

MARGIN_X = (PAGE_WIDTH - TOTAL_GRID_W) // 2   # 413 px (35.0 mm)
MARGIN_Y = (PAGE_HEIGHT - TOTAL_GRID_H) // 2  # 337 px (28.5 mm)


def ensure_card_back_rendered() -> Path:
    """Ensure the card back PNG exists at full resolution."""
    if CARD_BACK_PNG.exists():
        return CARD_BACK_PNG
    print("🎨 Rendering card-back.svg via Playwright...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1400, "height": 2420})
            page.goto(f"file://{CARD_BACK_SVG.resolve()}")
            CARD_BACK_PNG.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(CARD_BACK_PNG))
            browser.close()
        print(f"✅ Created {CARD_BACK_PNG}")
    except Exception as err:
        print(f"⚠️ Playwright render failed ({err}), generating fallback PIL back...")
        img = Image.new("RGB", (1400, 2420), (7, 17, 12))
        draw = ImageDraw.Draw(img)
        gold = (240, 217, 138)
        draw.rectangle((40, 40, 1360, 2380), outline=gold, width=8)
        draw.rectangle((80, 80, 1320, 2340), outline=(126, 100, 39), width=4)
        draw.ellipse((500, 1010, 900, 1410), outline=gold, width=8)
        img.save(CARD_BACK_PNG)
    return CARD_BACK_PNG


def get_card_slot_bbox(col: int, row: int):
    """Return (x0, y0, x1, y1) for card slot at (col, row)."""
    x0 = MARGIN_X + col * CARD_WIDTH
    y0 = MARGIN_Y + row * CARD_HEIGHT
    x1 = x0 + CARD_WIDTH
    y1 = y0 + CARD_HEIGHT
    return x0, y0, x1, y1


def draw_crop_marks(draw: ImageDraw.ImageDraw, has_cards_mask: list):
    """
    Draw professional corner crop marks and cutting guides outside the cards.
    """
    crop_color = (90, 90, 90)
    mark_len = 36  # ~3mm at 300 DPI
    mark_gap = 12  # gap from card edge

    # Cut line coordinates
    x_cuts = [MARGIN_X + c * CARD_WIDTH for c in range(COLS + 1)]
    y_cuts = [MARGIN_Y + r * CARD_HEIGHT for r in range(ROWS + 1)]

    # Vertical cut ticks (top margin and bottom margin)
    for x in x_cuts:
        # Top tick
        draw.line([(x, MARGIN_Y - mark_gap - mark_len), (x, MARGIN_Y - mark_gap)], fill=crop_color, width=2)
        # Bottom tick
        draw.line([(x, MARGIN_Y + TOTAL_GRID_H + mark_gap), (x, MARGIN_Y + TOTAL_GRID_H + mark_gap + mark_len)], fill=crop_color, width=2)

    # Horizontal cut ticks (left margin and right margin)
    for y in y_cuts:
        # Left tick
        draw.line([(MARGIN_X - mark_gap - mark_len, y), (MARGIN_X - mark_gap, y)], fill=crop_color, width=2)
        # Right tick
        draw.line([(MARGIN_X + TOTAL_GRID_W + mark_gap, y), (MARGIN_X + TOTAL_GRID_W + mark_gap + mark_len, y)], fill=crop_color, width=2)

    # Subtle inner corner ticks for the center cross
    center_x = MARGIN_X + CARD_WIDTH
    center_y = MARGIN_Y + CARD_HEIGHT
    draw.line([(center_x - mark_len // 2, center_y), (center_x + mark_len // 2, center_y)], fill=(160, 160, 160), width=1)
    draw.line([(center_x, center_y - mark_len // 2), (center_x, center_y + mark_len // 2)], fill=(160, 160, 160), width=1)


def build_sheet_image(cards: list, card_back_img: Image.Image, is_back: bool, page_num: int, total_pages: int, subtitle: str) -> Image.Image:
    """Build a single A4 300 DPI sheet image."""
    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(page)

    has_cards_mask = []

    for i in range(CARDS_PER_PAGE):
        if i < len(cards):
            card_info = cards[i]
            col = i % COLS
            row = i // COLS
            has_cards_mask.append(True)

            # In duplex printing (flip on long edge), column 0 flips to column 1
            if is_back:
                col = (COLS - 1) - col

            x0, y0, x1, y1 = get_card_slot_bbox(col, row)

            if is_back:
                card_img = card_back_img
            else:
                card_png = DEFAULT_RENDERS_DIR / f"{card_info['id']}.png"
                if not card_png.exists():
                    card_webp = DEFAULT_RENDERS_DIR / f"{card_info['id']}.webp"
                    card_png = card_webp
                card_img = Image.open(card_png).convert("RGB")

            # High quality resize into slot
            resized = card_img.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
            page.paste(resized, (x0, y0))

            # Draw very subtle hairline border around card for cutting boundary
            draw.rectangle((x0, y0, x1, y1), outline=(220, 220, 220), width=1)
        else:
            has_cards_mask.append(False)

    # Crop marks
    draw_crop_marks(draw, has_cards_mask)

    # Footer note
    footer_text = f"LeopardCat Tarot (石虎塔羅) • A4 DIY Print • Page {page_num}/{total_pages} ({subtitle}) • Standard 70x120mm"
    draw.text((MARGIN_X, PAGE_HEIGHT - MARGIN_Y // 2), footer_text, fill=(120, 120, 120))

    return page


def generate_tarot_pdfs(output_dir: Path):
    """Generate the complete set of A4 PDF print sheets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ensure_card_back_rendered()

    # Load canonical card manifest
    with open(DEFAULT_MANIFEST, "r", encoding="utf-8") as f:
        all_cards = json.load(f)

    total_cards = len(all_cards)
    total_sheets = (total_cards + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE

    print(f"🃏 Found {total_cards} cards. Generating {total_sheets} sheets (4 cards/sheet)...")

    # Pre-render card back at target slot size
    raw_back = Image.open(CARD_BACK_PNG).convert("RGB")
    back_resized = raw_back.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)

    front_pages = []
    back_pages = []
    duplex_pages = []

    for sheet_idx in range(total_sheets):
        start_idx = sheet_idx * CARDS_PER_PAGE
        end_idx = min(start_idx + CARDS_PER_PAGE, total_cards)
        sheet_cards = all_cards[start_idx:end_idx]

        card_names = ", ".join(c.get("slug", c["id"]) for c in sheet_cards)
        print(f"  📄 Processing Sheet {sheet_idx + 1}/{total_sheets} (Cards {start_idx + 1} - {end_idx})...")

        # Build front sheet
        front_sheet = build_sheet_image(
            cards=sheet_cards,
            card_back_img=back_resized,
            is_back=False,
            page_num=sheet_idx + 1,
            total_pages=total_sheets,
            subtitle=f"Front: #{start_idx + 1:02d} - #{end_idx:02d}"
        )
        front_pages.append(front_sheet)

        # Build matching back sheet
        back_sheet = build_sheet_image(
            cards=sheet_cards,
            card_back_img=back_resized,
            is_back=True,
            page_num=sheet_idx + 1,
            total_pages=total_sheets,
            subtitle=f"Back: #{start_idx + 1:02d} - #{end_idx:02d}"
        )
        back_pages.append(back_sheet)

        # Interleave for duplex
        duplex_pages.append(front_sheet)
        duplex_pages.append(back_sheet)

    # Save Duplex PDF
    duplex_path = output_dir / "leopardcat_tarot_A4_duplex.pdf"
    print(f"\n📦 Saving Duplex PDF ({len(duplex_pages)} pages) -> {duplex_path}...")
    duplex_pages[0].save(
        duplex_path,
        "PDF",
        resolution=300.0,
        save_all=True,
        append_images=duplex_pages[1:]
    )

    # Save Fronts PDF
    fronts_path = output_dir / "leopardcat_tarot_A4_fronts.pdf"
    print(f"📦 Saving Fronts PDF ({len(front_pages)} pages) -> {fronts_path}...")
    front_pages[0].save(
        fronts_path,
        "PDF",
        resolution=300.0,
        save_all=True,
        append_images=front_pages[1:]
    )

    # Save Backs PDF
    backs_path = output_dir / "leopardcat_tarot_A4_backs.pdf"
    print(f"📦 Saving Backs PDF ({len(back_pages)} pages) -> {backs_path}...")
    back_pages[0].save(
        backs_path,
        "PDF",
        resolution=300.0,
        save_all=True,
        append_images=back_pages[1:]
    )

    # Generate sample preview images for quick inspection
    preview_front = output_dir / "preview_sheet_01_front.jpg"
    preview_back = output_dir / "preview_sheet_01_back.jpg"
    front_pages[0].save(preview_front, "JPEG", quality=85)
    back_pages[0].save(preview_back, "JPEG", quality=85)
    print(f"🖼️ Previews saved to {preview_front.name} & {preview_back.name}")

    print("\n🎉 PDF Generation Completed Successfully!")
    print(f"  • Duplex File: {duplex_path} ({os.path.getsize(duplex_path) / (1024*1024):.1f} MB)")
    print(f"  • Fronts File: {fronts_path} ({os.path.getsize(fronts_path) / (1024*1024):.1f} MB)")
    print(f"  • Backs File:  {backs_path} ({os.path.getsize(backs_path) / (1024*1024):.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Generate A4 DIY Tarot Deck PDFs.")
    parser.add_argument("--output-dir", default="print_output", help="Target directory for generated PDFs")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir

    generate_tarot_pdfs(output_dir)


if __name__ == "__main__":
    main()
