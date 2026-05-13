from PIL import Image, ImageChops
import sys
from pathlib import Path

def auto_crop(image_path, output_path):
    img = Image.open(image_path).convert("RGB")
    # Detect the background color (usually off-white/beige for lithography)
    # We'll use the corner pixel as a hint
    bg_color = img.getpixel((5, 5))
    
    bg = Image.new("RGB", img.size, bg_color)
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    
    if bbox:
        # Give a small margin (10px)
        margin = 10
        new_bbox = (
            max(0, bbox[0] - margin),
            max(0, bbox[1] - margin),
            min(img.size[0], bbox[2] + margin),
            min(img.size[1], bbox[3] + margin)
        )
        img = img.crop(new_bbox)
        img.save(output_path)
        print(f"Cropped {image_path.name} to {new_bbox}")
    else:
        img.save(output_path)
        print(f"No crop needed for {image_path.name}")

if __name__ == "__main__":
    src_dir = Path("/home/ubuntu/.gemini/antigravity/brain/c3c258f9-ab90-490a-a0be-684eea849447")
    dest_dir = Path("/home/ubuntu/leopardcat-tarot/art/generated")
    
    mapping = {
        "card_pe_01_ace_of_pentacles_v5_no_card_1777367923161.png": "card-pe-01-ace-of-pentacles.png",
        "card_pe_02_two_of_pentacles_v5_no_card_1777367940746.png": "card-pe-02-two-of-pentacles.png",
        "card_pe_05_five_of_pentacles_v5_no_card_1777367955398.png": "card-pe-05-five-of-pentacles.png"
    }
    
    for src_name, dest_name in mapping.items():
        src_path = src_dir / src_name
        dest_path = dest_dir / dest_name
        if src_path.exists():
            auto_crop(src_path, dest_path)
