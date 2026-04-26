import json
from pathlib import Path

CARDS_DIR = Path("/home/ubuntu/leopardcat-tarot/generator/cards")

REWORKS = {
    "card-cu-07-seven-of-cups.json": {
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. 2:3 vertical. FULL BLEED: No borders, no text. ANTHROPOMORPHIC: A Taiwan leopard cat standing upright on two legs, wearing a scholar's robe, looking in wonder at EXACTLY SEVEN golden cups floating in a cloud of mist. CENTERED COMPOSITION: All cups must be fully visible and contained within the image frame, nothing cut off. Slender build, sharp facial structure, white ear spots, forehead stripes. Ethereal atmosphere. Full bleed. No borders.",
    },
    "card-cu-09-nine-of-cups.json": {
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. 2:3 vertical. FULL BLEED: No borders, no text. ANTHROPOMORPHIC: A satisfied Taiwan leopard cat standing upright on two legs, wearing a rich golden embroidered robe. He stands with arms crossed, nine golden cups arranged clearly behind him in a semi-circle. Slender build, sharp facial structure, white ear spots, forehead stripes. Warm, rich forest textures. Full bleed. No borders.",
    },
    "card-cu-11-page-of-cups.json": {
        "subtitle": "Curiosity & Discovery",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. 2:3 vertical. FULL BLEED: No borders, no text, no labels. ANTHROPOMORPHIC: A curious young Taiwan leopard cat standing upright on two legs, wearing a simple blue tunic. He stands by a stream bank, looking up as a dream-fish pops out of a golden cup he holds. Slender juvenile build, sharp facial structure, white ear spots, forehead stripes. Full bleed. No borders.",
    },
    "card-cu-12-knight-of-cups.json": {
        "subtitle": "The Romantic Messenger",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. 2:3 vertical. FULL BLEED: No borders, no text. ANTHROPOMORPHIC: An elegant Taiwan leopard cat standing upright on two legs, wearing a silver knightly tunic and a flowing teal cape. He holds a golden cup forward as if offering a toast. Slender build, sharp facial structure, white ear spots, forehead stripes. Misty morning river background. Full bleed. No borders.",
    },
    "card-cu-13-queen-of-cups.json": {
        "subtitle": "Intuition & Compassion",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. 2:3 vertical. FULL BLEED: No borders, no text. ANTHROPOMORPHIC: A serene Taiwan leopard cat queen standing upright on two legs, wearing a flowing gown of sea-foam green and a simple crown. She holds a closed, ornate golden cup. Slender build, sharp facial structure, white ear spots, forehead stripes. Calm seaside background. Full bleed. No borders.",
    },
    "card-cu-14-king-of-cups.json": {
        "subtitle": "Stability & Wisdom",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. 2:3 vertical. FULL BLEED: No borders, no text. ANTHROPOMORPHIC: A dignified Taiwan leopard cat king standing upright on two legs, wearing a royal purple robe with a thick collar. He sits on a throne shaped like a shell, holding a golden cup. Slender build (not a lion), sharp small-cat facial structure, white ear spots, forehead stripes. Stormy sea background. Full bleed. No borders.",
    }
}

for filename, updates in REWORKS.items():
    path = CARDS_DIR / filename
    if path.exists():
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Update fields
        if "image_prompt" in updates:
            data["generation"]["image_prompt"] = updates["image_prompt"]
        if "subtitle" in updates:
            data["subtitle"] = updates["subtitle"]
        
        # Set status back to rework_needed
        data["status"] = "rework_needed"
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Prepared {filename}")
