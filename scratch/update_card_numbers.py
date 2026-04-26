import json
from pathlib import Path

CARDS_DIR = Path("/home/ubuntu/leopardcat-tarot/generator/cards")

def update_numbers():
    files = list(CARDS_DIR.glob("*.json"))
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        changed = False
        id_str = data.get("id", "")
        
        if "card-wa-" in id_str:
            # card-wa-01-ace-of-wands
            parts = id_str.split('-')
            if len(parts) >= 3:
                try:
                    base_num = int(parts[2])
                    new_num = 100 + base_num
                    if data["number"] != new_num:
                        data["number"] = new_num
                        changed = True
                except ValueError:
                    pass
        elif "card-cu-" in id_str:
            parts = id_str.split('-')
            if len(parts) >= 3:
                try:
                    base_num = int(parts[2])
                    new_num = 200 + base_num
                    if data["number"] != new_num:
                        data["number"] = new_num
                        changed = True
                except ValueError:
                    pass
        elif "card-sw-" in id_str:
            parts = id_str.split('-')
            if len(parts) >= 3:
                try:
                    base_num = int(parts[2])
                    new_num = 300 + base_num
                    if data["number"] != new_num:
                        data["number"] = new_num
                        changed = True
                except ValueError:
                    pass
        
        if changed:
            with open(f, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            print(f"✅ Updated {f.name} -> {data['number']}")

if __name__ == "__main__":
    update_numbers()
