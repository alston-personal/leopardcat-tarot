import json
import os

BASE_DIR = "/home/ubuntu/leopardcat-tarot/generator/cards"

REWORKS = {
    "card-wa-02-two-of-wands.json": {
        "subtitle": "Planning & Evaluation",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: A Taiwan leopard cat standing upright on two legs on a cliff overlook. He holds EXACTLY TWO wooden wands: one held firmly in his hand, and another one standing vertically beside him on the ground. In his other hand, he holds a small, glowing world-globe orb. Slender build, sharp facial structure, white ear spots, forehead stripes. High-fidelity biological markers. 2:3 vertical crop compatible composition.",
    },
    "card-wa-03-three-of-wands.json": {
        "subtitle": "Expansion & Foresight",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: A Taiwan leopard cat standing upright on two legs, back to the viewer, looking out over the sea from a ridge. He stands between EXACTLY THREE wooden wands that are planted firmly in the ground close together in a narrow arrangement. All three wands must be fully visible and centered. Slender build, sharp facial structure, white ear spots, forehead stripes. High-fidelity biological markers.",
    },
    "card-wa-04-four-of-wands.json": {
        "subtitle": "Celebration & Harmony",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: Two Taiwan leopard cats standing upright on two legs, celebrating. They are framed by EXACTLY FOUR wooden wands that are arranged in a narrow, close-packed square/rectangle (two on left, two on right) with a garland of flowers between them. All four wands must be fully visible within the 2:3 center area. Slender build, sharp facial structure, white ear spots, forehead stripes.",
    },
    "card-wa-05-five-of-wands.json": {
        "subtitle": "Competition & Struggle",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: EXACTLY FIVE Taiwan leopard cats. EACH CAT IS STANDING UPRIGHT ON TWO LEGS (human-like posture). Each cat holds exactly one wooden wand (Total 5 wands). They are sparring and clashing their wands in a narrow central group. All cats and all 5 wands must be visible. Slender build, sharp facial structure, white ear spots, forehead stripes. High-fidelity biological markers.",
    },
    "card-wa-06-six-of-wands.json": {
        "subtitle": "Victory & Recognition",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: A Taiwan leopard cat standing upright on two legs, triumphantly riding a deer-like animal (sambar deer) through a cheering forest crowd. He holds a golden-crowned wand. Behind him, EXACTLY FIVE other wooden wands are held up by invisible or partially visible cats, making EXACTLY SIX wands total. All wands must be narrow and centered. Slender build, sharp facial structure, white ear spots, forehead stripes.",
    },
    "card-wa-07-seven-of-wands.json": {
        "subtitle": "Defense & Perseverance",
    },
    "card-wa-08-eight-of-wands.json": {
        "subtitle": "Swiftness & Alignment",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: A Taiwan leopard cat standing upright on two legs, pointing toward the sky as EXACTLY EIGHT wooden wands fly through the air in a narrow parallel formation. The cat must be standing upright on two legs (not on four legs). Slender build, sharp facial structure, white ear spots, forehead stripes. High-fidelity biological markers.",
    },
    "card-wa-09-nine-of-wands.json": {
        "subtitle": "Resilience & Persistence",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: A Taiwan leopard cat standing upright on two legs, head bandaged, holding one wooden wand firmly. Behind him, EXACTLY EIGHT more wooden wands are arranged in a narrow, dense semi-circle (Total 9 wands). All wands must be visible and close to the cat to avoid being cut off in vertical crop. Slender build, sharp facial structure, white ear spots, forehead stripes.",
    },
    "card-wa-10-ten-of-wands.json": {
        "subtitle": "Burden & Responsibility",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: A Taiwan leopard cat standing upright on two legs but bent over, carrying a bundle of EXACTLY TEN wooden wands on his back. The wands must be countable and not a messy blur. Walking toward a distant ridge at twilight. Slender build, sharp facial structure, white ear spots, forehead stripes. High-fidelity biological markers.",
    },
    "card-wa-11-page-of-wands.json": {
        "subtitle": "Ambition & Energy",
    },
    "card-wa-12-knight-of-wands.json": {
        "subtitle": "Passion & Adventure",
    },
    "card-wa-13-queen-of-wands.json": {
        "subtitle": "Confidence & Vitality",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: A regal Taiwan leopard cat queen standing upright on two legs, sitting on a throne of sunflowers. She holds one wooden wand in her hand. Slender build, sharp facial structure, white ear spots, forehead stripes. No baked-in text. High-fidelity biological markers.",
    },
    "card-wa-14-king-of-wands.json": {
        "subtitle": "Leadership & Innovation",
        "image_prompt": "Mystical 1900s lithography tarot card illustration. Clean bold black ink outlines. NO BORDERS. FULL BLEED IMAGE. WIDE FIELD OF VIEW. ANTHROPOMORPHIC: A majestic Taiwan leopard cat king standing upright on two legs, sitting on a throne carved with rosettes. He holds a large wooden wand blooming with fire. Slender build (small cat, not a lion), sharp facial structure, white ear spots, forehead stripes. No baked-in text. High-fidelity biological markers.",
    },
}

for filename, updates in REWORKS.items():
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Update subtitle
        if "subtitle" in updates:
            data["subtitle"] = updates["subtitle"]
        
        # Update prompt and status
        if "image_prompt" in updates:
            data["generation"]["image_prompt"] = updates["image_prompt"]
            data["status"] = "rework_needed"
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Prepared {filename}")
    else:
        print(f"❌ Could not find {filename}")
