import json
import os
import glob
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path("/home/ubuntu/leopardcat-tarot")
CARDS_SRC = PROJECT_ROOT / "generator/cards"
WEBSITE_CONTENT = PROJECT_ROOT / "website/src/data/cards_db.json"

def aggregate_cards():
    print(f"🔍 Scanning for tarot card data in {CARDS_SRC}...")
    card_files = sorted(glob.glob(str(CARDS_SRC / "*.json")))
    
    deck = []
    for cf in card_files:
        p = Path(cf)
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Extract only necessary fields for the website to keep it lightweight
                entry = {
                    "id": data.get("id"),
                    "number": data.get("number"),
                    "title": data.get("title", ""),
                    "subtitle": data.get("subtitle", ""),
                    "slug": data.get("slug", ""),
                    "image": f"art/renders/{p.stem}.png",
                    "ecology": data.get("ecology", {}),
                    "meanings": data.get("meanings", {}),
                    "palette": data.get("palette", {})
                }
                deck.append(entry)
                print(f"✅ Aggregated: {entry['title']} ({entry['number']})")
        except Exception as e:
            print(f"❌ Error reading {p.name}: {e}")

    # Ensure output directory exists
    WEBSITE_CONTENT.parent.mkdir(parents=True, exist_ok=True)
    
    with open(WEBSITE_CONTENT, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    
    print("-" * 50)
    print(f"🚀 Success: {len(deck)} cards compiled into {WEBSITE_CONTENT}")
    print("-" * 50)

if __name__ == "__main__":
    aggregate_cards()
