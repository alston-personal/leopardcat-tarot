"""Private browser-based duplex print service for LeopardCat Tarot.

No print-master assets are exposed through the public static tree. The owner
opens /admin/print, authenticates with HTTP Basic auth, selects cards, then
prints the generated A4 front/back sheets at 100% / Actual Size.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import parse_qs, quote

PROJECT_ROOT = Path(os.environ.get("LEOPARDCAT_PROJECT_ROOT", "/home/ubuntu/leopardcat-tarot"))
MASTER_RENDER_DIR = Path(os.environ.get("LEOPARDCAT_PRINT_MASTER_DIR", PROJECT_ROOT / "art" / "renders"))
CREDENTIAL_FILE = Path(os.environ.get("LEOPARDCAT_PRINT_CREDENTIAL_FILE", PROJECT_ROOT / ".print-credentials"))
CARD_BACK_PATH = Path(os.environ.get("LEOPARDCAT_PRINT_CARD_BACK", PROJECT_ROOT / "website" / "public" / "art" / "card-back.svg"))


def _load_credentials():
    user = os.environ.get("LEOPARDCAT_PRINT_USER", "")
    password = os.environ.get("LEOPARDCAT_PRINT_PASSWORD", "")
    if user and password:
        return user, password
    try:
        values = {}
        for raw in CREDENTIAL_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        return values.get("LEOPARDCAT_PRINT_USER", ""), values.get("LEOPARDCAT_PRINT_PASSWORD", "")
    except OSError:
        return "", ""


def _send(handler, status: int, body: bytes, content_type: str, extra_headers=None):
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Cache-Control", "no-store, private")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
    for key, value in (extra_headers or {}).items():
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(body)


def _authorized(handler) -> bool:
    print_user, print_password = _load_credentials()
    # Fail closed. Missing credentials must never make print masters public.
    if not print_user or not print_password:
        _send(handler, 503, b"Print service credentials are not configured.", "text/plain; charset=utf-8")
        return False
    header = handler.headers.get("Authorization", "")
    expected = "Basic " + base64.b64encode(f"{print_user}:{print_password}".encode()).decode()
    if header != expected:
        _send(handler, 401, b"Authentication required.", "text/plain; charset=utf-8", {"WWW-Authenticate": 'Basic realm="LeopardCat Tarot Print"'})
        return False
    return True


def _card_index(manifest):
    return {str(card.get("id")): card for card in manifest if card.get("id")}


def _master_path(card_id: str, manifest) -> Path | None:
    if card_id not in _card_index(manifest):
        return None
    for ext in (".png", ".webp"):
        candidate = (MASTER_RENDER_DIR / f"{card_id}{ext}").resolve()
        try:
            candidate.relative_to(MASTER_RENDER_DIR.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None


def _back_svg() -> bytes:
    # One canonical design for both the public deck animation and physical print.
    # Do not silently synthesize another back: if the canonical asset disappears,
    # fail closed so a prototype design cannot leak into production printing.
    try:
        return CARD_BACK_PATH.read_bytes()
    except OSError:
        return b""


def _admin_page(manifest) -> str:
    cards = []
    for card in manifest:
        cid = str(card.get("id") or "")
        if not cid:
            continue
        title = card.get("title") or {}
        cards.append({"id": cid, "zh": title.get("zh") or cid, "en": title.get("en") or ""})
    data = json.dumps(cards, ensure_ascii=False).replace("</", "<\\/")
    html = r'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>石虎塔羅 · 私人列印</title>
<style>
body{font-family:system-ui,sans-serif;background:#091813;color:#eee;max-width:1100px;margin:30px auto;padding:0 18px}
h1{color:#dfce98}.note{line-height:1.7;color:#c9c5b9}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
label{border:1px solid #4f604f;border-radius:10px;padding:8px;background:#10231c;cursor:pointer}label.sel{outline:2px solid #dfce98}
img{width:100%;aspect-ratio:70/120;object-fit:cover;border-radius:6px}button{padding:12px 18px;margin:14px 8px 14px 0;font-size:16px}#count{font-weight:700;color:#dfce98}
</style></head><body>
<h1>石虎塔羅 · 私人雙面列印</h1>
<p class="note">Production V1：A4 2×2、成品 70×120 mm、四周 3 mm bleed、正反共用同一裁切座標。列印請選 A4、雙面、100% / 實際大小，不要 Fit to page。裁切只認 crop marks，不沿牌面或牌背邊框裁。</p>
<p>已選 <span id="count">0</span> 張　<button id="all78">全選 78 張</button><button id="first4">選前 4 張</button><button id="clear">清除</button><button id="print">產生雙面列印頁</button></p>
<div class="grid" id="grid"></div>
<script>
const cards=__CARD_DATA__;const sel=new Set();const g=document.querySelector('#grid');
function render(){g.innerHTML='';cards.forEach(c=>{const l=document.createElement('label');if(sel.has(c.id))l.className='sel';l.innerHTML=`<input type="checkbox" ${sel.has(c.id)?'checked':''}> <b>${c.zh}</b><br><small>${c.en}</small><img loading="lazy" src="/admin/print/card/${encodeURIComponent(c.id)}">`;l.onclick=e=>{if(e.target.tagName==='IMG')return;e.preventDefault();sel.has(c.id)?sel.delete(c.id):sel.add(c.id);render()};g.appendChild(l)});document.querySelector('#count').textContent=sel.size}
render();
document.querySelector('#all78').onclick=()=>{sel.clear();cards.slice(0,78).forEach(c=>sel.add(c.id));render()};
document.querySelector('#first4').onclick=()=>{sel.clear();cards.slice(0,4).forEach(c=>sel.add(c.id));render()};
document.querySelector('#clear').onclick=()=>{sel.clear();render()};
document.querySelector('#print').onclick=()=>{if(!sel.size)return alert('請至少選一張牌');location.href='/admin/print/sheet?cards='+encodeURIComponent([...sel].join(','))};
</script></body></html>'''
    return html.replace("__CARD_DATA__", data)


def _crop_marks_html() -> str:
    return ''.join(f'<i class="mark m{i}"></i>' for i in range(1, 9))


def _front_cell(card_id: str) -> str:
    src = f"/admin/print/card/{quote(card_id)}"
    return (
        '<div class="card-cell front-cell">'
        f'<div class="bleed front-bleed"></div><div class="trim front-trim"><img src="{src}"></div>'
        + _crop_marks_html() + '</div>'
    )


def _back_cell() -> str:
    return (
        '<div class="card-cell back-cell">'
        '<div class="bleed back-bleed"></div><div class="trim back-trim"><img src="/admin/print/back.svg"></div>'
        + _crop_marks_html() + '</div>'
    )


def _sheet_page(card_ids, manifest) -> str:
    valid = [cid for cid in card_ids if _master_path(cid, manifest)]
    if not valid:
        return ""
    chunks = [valid[i:i + 4] for i in range(0, len(valid), 4)]
    pages = []
    total_sheets = len(chunks)
    for sheet_no, chunk in enumerate(chunks, start=1):
        fronts = ''.join(_front_cell(cid) for cid in chunk)
        backs = ''.join(_back_cell() for _ in chunk)
        pages.append(
            f'<section class="sheet" data-side="front"><span class="page-tag">Sheet {sheet_no}/{total_sheets} · FRONT</span>{fronts}</section>'
            f'<section class="sheet" data-side="back"><span class="page-tag">Sheet {sheet_no}/{total_sheets} · BACK</span>{backs}</section>'
        )
    return '''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>石虎塔羅 Production V1</title><style>
@page{size:A4 portrait;margin:0}*{box-sizing:border-box}body{margin:0;background:#ddd;font-family:system-ui,sans-serif}.toolbar{position:sticky;top:0;background:#111;color:#fff;padding:10px;z-index:10}
.sheet{width:210mm;height:297mm;background:white;margin:8mm auto;display:grid;grid-template-columns:84mm 84mm;grid-template-rows:134mm 134mm;gap:6mm;justify-content:center;align-content:center;position:relative;break-after:page;page-break-after:always}
.page-tag{position:absolute;left:5mm;bottom:3mm;font:6pt system-ui;color:#555}.card-cell{width:84mm;height:134mm;position:relative;overflow:visible}.bleed{position:absolute;left:4mm;top:4mm;width:76mm;height:126mm;background:#151515}.trim{position:absolute;left:7mm;top:7mm;width:70mm;height:120mm;overflow:hidden;background:#151515}
.front-trim{padding:2mm 1mm}.front-trim img{display:block;width:68mm;height:116mm;object-fit:fill}.back-bleed{background:#020604 url('/admin/print/back.svg') center/76mm 126mm no-repeat}.back-trim img{display:block;width:70mm;height:120mm;object-fit:fill}
.mark{position:absolute;display:block;background:#000}.m1,.m3,.m5,.m7{width:3mm;height:.2mm}.m2,.m4,.m6,.m8{width:.2mm;height:3mm}
/* Crop marks align to the 70x120 trim box at x=7..77mm, y=7..127mm. Marks are outside the 3mm bleed. */
.m1{left:.5mm;top:7mm}.m2{left:7mm;top:.5mm}.m3{left:80.5mm;top:7mm}.m4{left:76.8mm;top:.5mm}.m5{left:.5mm;top:126.8mm}.m6{left:7mm;top:130.5mm}.m7{left:80.5mm;top:126.8mm}.m8{left:76.8mm;top:130.5mm}
@media print{body{background:#fff}.toolbar{display:none}.sheet{margin:0;break-after:page;page-break-after:always}.page-tag{display:none}}
</style></head><body><div class="toolbar"><b>石虎塔羅 Production V1</b>　70×120 mm · 3 mm bleed · 正反共用 trim · 100% / 實際大小。裁切只看 crop marks。 <button onclick="window.print()">列印</button></div>''' + ''.join(pages) + '</body></html>'


def handle_print_get(handler, path: str, query: str, manifest) -> bool:
    if not (path == "/admin/print" or path.startswith("/admin/print/")):
        return False
    if not _authorized(handler):
        return True
    if path == "/admin/print":
        _send(handler, 200, _admin_page(manifest).encode("utf-8"), "text/html; charset=utf-8")
        return True
    if path == "/admin/print/back.svg":
        back = _back_svg()
        if not back:
            _send(handler, 503, b"Canonical card back is unavailable.", "text/plain; charset=utf-8")
        else:
            _send(handler, 200, back, "image/svg+xml; charset=utf-8")
        return True
    if path.startswith("/admin/print/card/"):
        card_id = path[len("/admin/print/card/"):]
        master = _master_path(card_id, manifest)
        if not master:
            _send(handler, 404, b"Not found", "text/plain")
            return True
        mime = mimetypes.guess_type(master.name)[0] or "application/octet-stream"
        _send(handler, 200, master.read_bytes(), mime)
        return True
    if path == "/admin/print/sheet":
        raw = parse_qs(query).get("cards", [""])[0]
        requested = [x for x in raw.split(",") if x][:78]
        page = _sheet_page(requested, manifest)
        if not page:
            _send(handler, 400, "沒有有效牌面。".encode("utf-8"), "text/plain; charset=utf-8")
        else:
            _send(handler, 200, page.encode("utf-8"), "text/html; charset=utf-8")
        return True
    _send(handler, 404, b"Not found", "text/plain")
    return True
