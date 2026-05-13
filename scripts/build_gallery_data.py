import json
import os
import glob
import shutil
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path("/home/ubuntu/leopardcat-tarot")
CARDS_SRC = PROJECT_ROOT / "generator/cards"
WEBSITE_CONTENT = PROJECT_ROOT / "website/src/data/cards_db.json"
WEBSITE_MANIFEST = PROJECT_ROOT / "website/public/manifest.json"
SOURCE_RENDERS = PROJECT_ROOT / "art/renders"
TARGET_RENDERS = PROJECT_ROOT / "website/public/art/renders"

def aggregate_cards():
    print(f"🔍 Scanning for tarot card data in {CARDS_SRC}...")
    card_files = sorted(glob.glob(str(CARDS_SRC / "*.json")))
    
    deck = []
    for cf in card_files:
        p = Path(cf)
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Extract only necessary fields for the website
                entry = {
                    "id": data.get("id"),
                    "arcana": data.get("arcana"),
                    "number": data.get("number"),
                    "title": data.get("title", ""),
                    "subtitle": data.get("subtitle", ""),
                    "slug": data.get("slug", ""),
                    "image": f"art/renders/{p.stem}.png",
                    "ecology": data.get("ecology", {}),
                    "meanings": data.get("meanings", {}),
                    "palette": data.get("palette", {}),
                    "meaning": data.get("meaning", {}) 
                }
                deck.append(entry)
                # print(f"✅ Aggregated: {entry['title']} ({entry['number']})")
        except Exception as e:
            print(f"❌ Error reading {p.name}: {e}")

    # --- 1. Save Data ---
    WEBSITE_CONTENT.parent.mkdir(parents=True, exist_ok=True)
    WEBSITE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    
    with open(WEBSITE_CONTENT, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    
    with open(WEBSITE_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    
    # --- 2. Sync Images ---
    print(f"📦 Syncing assets to website gallery...")
    TARGET_RENDERS.mkdir(parents=True, exist_ok=True)
    
    sync_count = 0
    for card in deck:
        img_name = Path(card["image"]).name
        src_img = SOURCE_RENDERS / img_name
        dest_img = TARGET_RENDERS / img_name
        
        if src_img.exists():
            # Only copy if different or doesn't exist to save time
            if not dest_img.exists() or src_img.stat().st_mtime > dest_img.stat().st_mtime:
                shutil.copy2(src_img, dest_img)
                sync_count += 1
        else:
            print(f"⚠️ Warning: Render missing for {card['id']} at {src_img}")

    print("-" * 50)
    print(f"🚀 Success: {len(deck)} cards compiled.")
    print(f"📂 Assets Synced: {sync_count} images updated.")
    print(f"📍 Location: {WEBSITE_MANIFEST}")
    print("-" * 50)

if __name__ == "__main__":
    aggregate_cards()
