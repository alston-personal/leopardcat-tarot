import json
from pathlib import Path
import os

CARDS_DIR = Path("/home/ubuntu/leopardcat-tarot/generator/cards")
RENDERS_DIR = Path("/home/ubuntu/leopardcat-tarot/art/renders")

def normalize_output_and_cleanup():
    # 1. Normalize JSON output paths
    files = list(CARDS_DIR.glob("*.json"))
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        id_str = data.get("id", "")
        expected_output = f"art/renders/{id_str}.png"
        
        if data.get("output") != expected_output:
            print(f"🔧 Fixing {f.name}: {data.get('output')} -> {expected_output}")
            data["output"] = expected_output
            with open(f, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

    # 2. Cleanup problematic files in renders
    renders = list(RENDERS_DIR.glob("card-*.png"))
    for r in renders:
        # If it has double numbers like card-16-16-
        name = r.name
        parts = name.split('-')
        # Check for card-XX-XX- pattern
        if len(parts) >= 4 and parts[1] == parts[2] and parts[1].isdigit():
            print(f"🗑️ Deleting duplicate: {name}")
            r.unlink()

if __name__ == "__main__":
    normalize_output_and_cleanup()
