#!/usr/bin/env python3
import json
import os
import shutil
import time
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path("/home/ubuntu/agent-data/projects/leopardcat-tarot")
REQUESTS_DIR = DATA_ROOT / "requests"
RESPONSES_DIR = DATA_ROOT / "responses"
CARDS_DIR = REPO_ROOT / "generator" / "cards"
ART_DIR = REPO_ROOT / "art" / "generated"

def ensure_dirs():
    REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)

def request_generation(card_id: str):
    """Creates a request for Antigravity, assembling the Dual-Layer Prompt."""
    card_file = CARDS_DIR / f"{card_id}.json"
    preset_file = REPO_ROOT / "generator" / "style_presets.json"
    
    if not card_file.exists():
        print(f"❌ Error: Card file {card_file} not found.")
        return False

    with open(card_file, 'r') as f:
        card_data = json.load(f)
    
    # Load Style Layer (Layer 1)
    with open(preset_file, 'r') as f:
        style_config = json.load(f)
        active_preset = style_config["presets"][style_config["active_preset"]]
    
    # Get Narrative Layer (Layer 2)
    narrative = card_data.get("generation", {}).get("narrative") or card_data.get("generation", {}).get("image_prompt", "")
    
    # Assembly
    full_prompt = (
        f"{active_preset['technical_prefix']} "
        f"{active_preset['style_baseline']} "
        f"{active_preset['character_baseline']} "
        f"Scene: {narrative} "
        f"{active_preset['composition_baseline']}"
    )

    request_data = {
        "card_id": card_id,
        "assembled_prompt": full_prompt,
        "status": "pending",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    request_file = REQUESTS_DIR / f"{card_id}.json"
    with open(request_file, 'w') as f:
        json.dump(request_data, f, indent=2)
    
    print(f"🚀 Dual-Layer Request sent for {card_id} using preset '{style_config['active_preset']}'.")
    return True

def sync_responses():
    """Checks for responses from Antigravity and updates the project."""
    responses = list(RESPONSES_DIR.glob("*.json"))
    if not responses:
        print("Empty: No pending responses found.")
        return

    for resp_file in responses:
        try:
            with open(resp_file, 'r') as f:
                data = json.load(f)
            
            card_id = data.get("card_id")
            optimized_prompt = data.get("optimized_prompt")
            image_path = data.get("image_path") # Path provided by Antigravity

            if not card_id:
                continue

            # 1. Update Card JSON
            card_file = CARDS_DIR / f"{card_id}.json"
            if card_file.exists() and optimized_prompt:
                with open(card_file, 'r') as f:
                    card_json = json.load(f)
                
                # Check if prompt changed
                old_prompt = card_json.get("generation", {}).get("image_prompt")
                if old_prompt != optimized_prompt:
                    card_json["generation"]["image_prompt"] = optimized_prompt
                    with open(card_file, 'w') as f:
                        json.dump(card_json, f, indent=2)
                    print(f"✅ Updated {card_id}.json with optimized prompt.")

            # 2. Move Image (if path provided and exists)
            if image_path and os.path.exists(image_path):
                target_img = ART_DIR / f"{card_id}.png"
                shutil.copy2(image_path, target_img)
                print(f"🎨 Saved generated image to {target_img}")
                
                # Also update main_image field in card json
                with open(card_file, 'r') as f:
                    card_json = json.load(f)
                card_json["main_image"] = str(target_img.relative_to(REPO_ROOT))
                with open(card_file, 'w') as f:
                    json.dump(card_json, f, indent=2)

            # 3. Cleanup response
            resp_file.unlink()
            print(f"🧹 Cleaned up response for {card_id}")

        except Exception as e:
            print(f"❌ Error processing response {resp_file.name}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LeopardCat Tarot Service Client")
    parser.add_argument("action", choices=["request", "sync"], help="Action to perform")
    parser.add_argument("--card", help="Card ID (e.g., card-00-the-fool) for request")
    
    args = parser.parse_args()
    ensure_dirs()
    
    if args.action == "request":
        if not args.card:
            print("❌ Error: --card is required for request action.")
        else:
            request_generation(args.card)
    elif args.action == "sync":
        sync_responses()
