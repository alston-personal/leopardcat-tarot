from pathlib import Path

TARGET = Path("website/fortune_server.py")
text = TARGET.read_text(encoding="utf-8")

IMPORT = "from print_service import handle_print_get\n"
if IMPORT not in text:
    anchor = "from divination.tarot import plan_spread, spread_catalog\n"
    if anchor not in text:
        raise SystemExit("guard failed: tarot import anchor missing")
    text = text.replace(anchor, anchor + IMPORT, 1)

HOOK = """        if handle_print_get(self, path, query, CARD_MANIFEST):\n            return\n\n"""
if HOOK not in text:
    anchor = "        query = url_parts[1] if len(url_parts) > 1 else \"\"\n\n"
    if anchor not in text:
        raise SystemExit("guard failed: do_GET query anchor missing")
    text = text.replace(anchor, anchor + HOOK, 1)

TARGET.write_text(text, encoding="utf-8")
print("private print integration present")
