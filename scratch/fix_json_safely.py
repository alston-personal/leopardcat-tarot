import json
import os

configs = {
    "card-cu-06-six-of-cups.json": {"zoom": 1.02, "trim": 30},
    "card-cu-07-seven-of-cups.json": {"zoom": 1.1, "trim": 75},
    "card-cu-08-eight-of-cups.json": {"zoom": 1.0, "trim": 95, "offset_y": 0.2},
    "card-cu-11-page-of-cups.json": {"zoom": 1.0, "trim": 40}
}

base_path = "generator/cards/"

for filename, cfg in configs.items():
    full_path = os.path.join(base_path, filename)
    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["render_config"] = {
        "zoom": cfg.get("zoom", 1.0),
        "offset_x": 0.5,
        "offset_y": cfg.get("offset_y", 0.5),
        "trim": cfg.get("trim", 20)
    }
    
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {filename}")
