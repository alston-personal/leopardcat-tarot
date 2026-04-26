import json
from pathlib import Path

CARDS_DIR = Path("/home/ubuntu/leopardcat-tarot/generator/cards")
SKELETONS = [
    "card-cu-11-page-of-cups.json",
    "card-cu-12-knight-of-cups.json",
    "card-cu-13-queen-of-cups.json",
    "card-cu-14-king-of-cups.json"
]

TEMPLATE_FILE = CARDS_DIR / "card-cu-10-ten-of-cups.json"

def expand_skeleton(skeleton_name):
    skeleton_path = CARDS_DIR / skeleton_name
    with open(skeleton_path, 'r') as f:
        skeleton_data = json.load(f)
    
    with open(TEMPLATE_FILE, 'r') as f:
        template_data = json.load(f)
    
    # Merge skeleton data into template
    merged = template_data.copy()
    merged.update(skeleton_data)
    
    # Ensure ID and Title are from skeleton
    merged["id"] = skeleton_data["id"]
    merged["title"] = skeleton_data["title"]
    
    # Update main_image and output paths
    merged["main_image"] = f"art/generated/{skeleton_data['id']}.png"
    merged["output"] = f"art/renders/{skeleton_data['id']}.png"
    
    # Set status to draft (assuming we are done with generation)
    merged["status"] = "draft"
    
    with open(skeleton_path, 'w') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"✅ Expanded {skeleton_name}")

def main():
    for skel in SKELETONS:
        expand_skeleton(skel)

if __name__ == "__main__":
    main()
