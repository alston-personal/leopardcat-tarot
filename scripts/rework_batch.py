import json
import subprocess
import time
from pathlib import Path

ROOT = Path("/home/ubuntu/leopardcat-tarot")
CARDS_DIR = ROOT / "generator" / "cards"
GEN_SCRIPT = ROOT / "generator" / "generate_main_image.py"

def main():
    files = sorted(list(CARDS_DIR.glob("*.json")))
    for card_file in files:
        with open(card_file, 'r') as f:
            data = json.load(f)
        
        if data.get("status") == "rework_needed":
            card_id = data["id"]
            prompt = data["generation"]["image_prompt"]
            output_rel = f"art/generated/{card_id}.png"
            
            print(f"🎨 Generating {card_id}...")
            cmd = [
                "python3", str(GEN_SCRIPT),
                "--prompt", prompt,
                "--output", output_rel
            ]
            
            success = False
            retries = 5
            while not success and retries > 0:
                try:
                    subprocess.run(cmd, check=True)
                    print(f"✅ Generated {card_id}")
                    success = True
                    # Rate limit safety for free tier (5 RPM)
                    print("Waiting 20s for rate limit safety...")
                    time.sleep(20)
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to generate {card_id}, retrying in 65s (Quota cooldown)...")
                    time.sleep(65)
                    retries -= 1

if __name__ == "__main__":
    main()
