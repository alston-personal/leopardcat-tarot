import json
import os
import glob
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path("/home/ubuntu/leopardcat-tarot")
CARDS_SRC = PROJECT_ROOT / "generator/cards"
WEBSITE_CONTENT = PROJECT_ROOT / "website/src/data/cards_db.json"
WEBSITE_MANIFEST = PROJECT_ROOT / "website/public/manifest.json"

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
                # Note: We keep some extra fields for the manifest if needed by the fortune server
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
                    "meaning": data.get("meaning", {}) # Translation support
                }
                deck.append(entry)
                print(f"✅ Aggregated: {entry['title']} ({entry['number']})")
        except Exception as e:
            print(f"❌ Error reading {p.name}: {e}")

    # Ensure output directories exist
    WEBSITE_CONTENT.parent.mkdir(parents=True, exist_ok=True)
    WEBSITE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to cards_db.json
    with open(WEBSITE_CONTENT, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    
    # Save to manifest.json (Public source of truth)
    with open(WEBSITE_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    
    print("-" * 50)
    print(f"🚀 Success: {len(deck)} cards compiled into:")
    print(f"   - {WEBSITE_CONTENT}")
    print(f"   - {WEBSITE_MANIFEST}")
    print("-" * 50)

if __name__ == "__main__":
    aggregate_cards()
