import os
import shutil
from PIL import Image

def process_and_deploy(source_name, target_filename):
    GEN_DIR = "/home/ubuntu/.gemini/antigravity/brain/cf2685e1-9c36-4540-8310-7626a6ffd324/"
    LOCAL_RENDER_DIR = "/home/ubuntu/leopardcat-tarot/art/renders/"
    WEB_RENDER_DIR = "/home/ubuntu/leopardcat-tarot/website/public/art/renders/"
    
    # 1. Find the latest generated image
    files = [f for f in os.listdir(GEN_DIR) if f.startswith(source_name) and f.endswith(".png")]
    if not files:
        print(f"❌ Error: Could not find source image starting with {source_name}")
        return
    
    latest_file = sorted(files)[-1]
    src_path = os.path.join(GEN_DIR, latest_file)
    
    # 2. Copy Original to Local Renders
    dest_local = os.path.join(LOCAL_RENDER_DIR, target_filename)
    shutil.copy(src_path, dest_local)
    print(f"✅ Saved Original to Local: {dest_local}")
    
    # 3. Perform 2:3 Vertical Crop for Website
    img = Image.open(src_path)
    w, h = img.size
    new_w = int(h * (2/3))
    left = (w - new_w) // 2
    right = left + new_w
    cropped_img = img.crop((left, 0, right, h))
    
    dest_web = os.path.join(WEB_RENDER_DIR, target_filename)
    cropped_img.save(dest_web)
    print(f"✂️ Saved 2:3 Cropped to Website: {dest_web}")

if __name__ == "__main__":
    # Deploy the latest fixed cards
    process_and_deploy("card_cu_10_ten_of_cups_final_v6", "card-cu-10-ten-of-cups.png")
    process_and_deploy("card_cu_01_ace_of_cups_safe_zone_v4", "card-cu-01-ace-of-cups.png")
    process_and_deploy("card_pe_05_five_of_pentacles_safe_v4", "card-pe-05-five-of-pentacles.png")
