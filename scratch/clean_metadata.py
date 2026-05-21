import os
import json
import re

cards_dir = "/home/ubuntu/leopardcat-tarot/generator/cards"
cleaned_count = 0

def clean_text(text):
    if not text: return text
    
    # Check if the text starts with common AI boilerplate
    if any(keyword in text[:100] for keyword in ["這段", "翻譯如下", "對應的中文", "繁體中文"]):
        # Pattern 1: Extract anything inside **「...」**
        match = re.search(r"\*\*「(.*?)」\*\*", text, re.DOTALL)
        if match: return match.group(1).strip()
        
        # Pattern 2: Extract anything inside **...** (bold but no quotes)
        # Note: We take the first bold block as it's usually the main meaning
        match = re.search(r"\*\*(.*?)\*\*", text, re.DOTALL)
        if match: 
            content = match.group(1).strip()
            # If it's just a single word like "Love", maybe keep looking? 
            # No, usually it's the whole sentence.
            return content
            
    return text

for filename in os.listdir(cards_dir):
    if filename.endswith(".json"):
        path = os.path.join(cards_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                continue
        
        zh_text = data.get("meaning", {}).get("zh", "")
        en_text = data.get("meaning", {}).get("en", "")
        
        new_zh = clean_text(zh_text)
        
        # Additional cleanup for bullet points if they survived
        if "以下是" in new_zh:
            new_zh = new_zh.split("以下是")[0].strip()
        if "在塔羅牌解說中" in new_zh:
            new_zh = new_zh.split("在塔羅牌解說中")[0].strip()
            
        # Strip final bold if it was left over
        new_zh = new_zh.replace("**", "").strip()

        if new_zh != zh_text:
            data["meaning"]["zh"] = new_zh
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Cleaned: {filename} -> {new_zh[:30]}...")
            cleaned_count += 1

print(f"Total cleaned: {cleaned_count}")
