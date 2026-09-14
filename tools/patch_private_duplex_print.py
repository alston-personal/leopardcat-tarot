from pathlib import Path
import re

SERVER = Path("website/fortune_server.py")
text = SERVER.read_text(encoding="utf-8")

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

SERVER.write_text(text, encoding="utf-8")

PRINT = Path("website/print_service.py")
p = PRINT.read_text(encoding="utf-8")

constant_anchor = 'CREDENTIAL_FILE = Path(os.environ.get("LEOPARDCAT_PRINT_CREDENTIAL_FILE", PROJECT_ROOT / ".print-credentials"))\n'
card_back_constant = 'CARD_BACK_PATH = Path(os.environ.get("LEOPARDCAT_PRINT_CARD_BACK", PROJECT_ROOT / "website" / "public" / "art" / "card-back.svg"))\n'
if card_back_constant not in p:
    if constant_anchor not in p:
        raise SystemExit("guard failed: credential constant anchor missing")
    p = p.replace(constant_anchor, constant_anchor + card_back_constant, 1)

new_back = '''def _back_svg() -> bytes:\n    # One canonical design for both the public deck animation and physical print.\n    # Do not silently synthesize another back: if the canonical asset disappears,\n    # fail closed so a prototype design cannot leak into production printing.\n    try:\n        return CARD_BACK_PATH.read_bytes()\n    except OSError:\n        return b\"\"\n\n\n'''
p, count = re.subn(r'def _back_svg\(\) -> bytes:\n.*?(?=def _admin_page)', new_back, p, count=1, flags=re.S)
if count != 1:
    raise SystemExit("guard failed: _back_svg function not found")

old_route = '''    if path == "/admin/print/back.svg":\n        _send(handler, 200, _back_svg(), "image/svg+xml; charset=utf-8")\n        return True\n'''
new_route = '''    if path == "/admin/print/back.svg":\n        back = _back_svg()\n        if not back:\n            _send(handler, 503, b"Canonical card back is unavailable.", "text/plain; charset=utf-8")\n        else:\n            _send(handler, 200, back, "image/svg+xml; charset=utf-8")\n        return True\n'''
if old_route in p:
    p = p.replace(old_route, new_route, 1)
elif new_route not in p:
    raise SystemExit("guard failed: back route anchor missing")

PRINT.write_text(p, encoding="utf-8")
print("private print integration present; canonical card back wired")
