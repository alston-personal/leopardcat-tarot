#!/usr/bin/env python3
import json
import sys
import subprocess
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dual_layer_generate.py <path/to/card.json>...")
        sys.exit(1)

    style_path = Path("generator/style_presets.json")
    with open(style_path, "r") as f:
        styles = json.load(f)
    
    preset = styles["presets"][styles["active_preset"]]
    
    for card_file in sys.argv[1:]:
        card_path = Path(card_file)
        with open(card_path, "r") as f:
            card = json.load(f)
            
        base_prompt = card["generation"]["image_prompt"]
        
        combined_prompt = f"{preset['technical_prefix']} {preset['style_baseline']} {preset['character_baseline']} Scene: {base_prompt} {preset['composition_baseline']}"
        
        output_rel = card["main_image"]
        print(f"Generating image for {card['id']}...")
        print(f"Combined Prompt:\n{combined_prompt}\n")
        
        # 1. Run generate_main_image.py
        result = subprocess.run([
            "python3", "generator/generate_main_image.py",
            "--prompt", combined_prompt,
            "--output", output_rel
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Generation failed for {card['id']}:\n{result.stderr}")
            continue
            
        print(f"Successfully generated main image for {card['id']}: {result.stdout.strip()}")
        
        # 2. Run render_card.py
        print(f"Rendering card {card['id']}...")
        render_result = subprocess.run([
            "python3", "generator/render_card.py", str(card_path)
        ], capture_output=True, text=True)
        
        if render_result.returncode != 0:
            print(f"Rendering failed for {card['id']}:\n{render_result.stderr}")
        else:
            print(f"Rendered successfully for {card['id']}: {render_result.stdout.strip()}")

if __name__ == "__main__":
    main()
