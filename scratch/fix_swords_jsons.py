import json
import os
import glob

def fix_swords_jsons():
    files = glob.glob('generator/cards/card-sw-*.json')
    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get filename part like 'card-sw-05-five-of-swords'
        fname = os.path.basename(fpath).replace('.json', '')
        
        # Fix ID
        data['id'] = fname
        
        # Fix Output
        data['output'] = f'art/renders/{fname}.png'
        
        # Fix Title (ZH/EN)
        # Assuming the titles are already there and mostly correct, but let's check
        
        # Fix SEO Title
        if 'website' in data:
            title_parts = fname.split('-')
            # title_parts like ['card', 'sw', '05', 'five', 'of', 'swords']
            # We want 'Five of Swords'
            title_str = ' '.join(title_parts[3:]).title()
            data['website']['seo_title'] = f"{title_str} - LeopardCat Tarot"
            
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Fixed {fname}")

if __name__ == "__main__":
    fix_swords_jsons()
