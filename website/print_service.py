"""Private browser-based duplex print service for LeopardCat Tarot.

No print-master assets are exposed through the public static tree.  The owner
opens /admin/print, authenticates with HTTP Basic auth, selects cards, then
prints the generated A4 front/back sheet at 100% / Actual Size.
"""
from __future__ import annotations

import base64
import html
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import parse_qs, quote

PROJECT_ROOT = Path(os.environ.get("LEOPARDCAT_PROJECT_ROOT", "/home/ubuntu/leopardcat-tarot"))
MASTER_RENDER_DIR = Path(os.environ.get("LEOPARDCAT_PRINT_MASTER_DIR", PROJECT_ROOT / "art" / "renders"))
PRINT_USER = os.environ.get("LEOPARDCAT_PRINT_USER", "")
PRINT_PASSWORD = os.environ.get("LEOPARDCAT_PRINT_PASSWORD", "")


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
    # Fail closed.  A missing credential configuration must never turn the
    # high-resolution print endpoint into an anonymous public endpoint.
    if not PRINT_USER or not PRINT_PASSWORD:
        _send(
            handler,
            503,
            "Print service credentials are not configured.".encode(),
            "text/plain; charset=utf-8",
        )
        return False
    header = handler.headers.get("Authorization", "")
    expected = "Basic " + base64.b64encode(f"{PRINT_USER}:{PRINT_PASSWORD}".encode()).decode()
    if header != expected:
        _send(
            handler,
            401,
            "Authentication required.".encode(),
            "text/plain; charset=utf-8",
            {"WWW-Authenticate": 'Basic realm="LeopardCat Tarot Print"'},
        )
        return False
    return True


def _card_index(manifest):
    return {str(card.get("id")): card for card in manifest if card.get("id")}


def _master_path(card_id: str, manifest) -> Path | None:
    if card_id not in _card_index(manifest):
        return None
    # Prefer lossless PNG print master.  Fall back to webp only for legacy cards.
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
    # Deliberately 180-degree rotationally symmetric so reversed readings and
    # long/short-edge duplex settings cannot create an upside-down card back.
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="1200" viewBox="0 0 700 1200">
<defs>
 <radialGradient id="g"><stop stop-color="#173b31"/><stop offset="1" stop-color="#071713"/></radialGradient>
 <pattern id="p" width="120" height="120" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <ellipse cx="28" cy="30" rx="18" ry="28" fill="none" stroke="#bca86e" stroke-width="5" opacity=".40"/>
  <ellipse cx="88" cy="90" rx="14" ry="22" fill="none" stroke="#bca86e" stroke-width="4" opacity=".28"/>
 </pattern>
</defs>
<rect width="700" height="1200" fill="url(#g)"/>
<rect width="700" height="1200" fill="url(#p)"/>
<rect x="30" y="30" width="640" height="1140" rx="30" fill="none" stroke="#d8c58b" stroke-width="8"/>
<rect x="52" y="52" width="596" height="1096" rx="24" fill="none" stroke="#7c704b" stroke-width="3"/>
<g fill="none" stroke="#d8c58b" stroke-width="7" opacity=".90">
 <circle cx="350" cy="600" r="145"/><circle cx="350" cy="600" r="105"/>
 <path d="M350 455L390 545L488 555L414 620L436 716L350 666L264 716L286 620L212 555L310 545Z"/>
</g>
<g fill="#e3d39d" font-family="serif" text-anchor="middle">
 <text x="350" y="110" font-size="34" letter-spacing="7">LEOPARDCAT TAROT</text>
 <text x="350" y="1110" font-size="34" letter-spacing="7" transform="rotate(180 350 600)">LEOPARDCAT TAROT</text>
</g>
</svg>'''
    return svg.encode("utf-8")


def _admin_page(manifest) -> str:
    cards = []
    for card in manifest:
        cid = str(card.get("id") or "")
        if not cid:
            continue
        title = card.get("title") or {}
        cards.append({"id": cid, "zh": title.get("zh") or cid, "en": title.get("en") or ""})
    data = json.dumps(cards, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>石虎塔羅 · 私人試印</title>
<style>body{{font-family:system-ui,sans-serif;background:#091813;color:#eee;max-width:1100px;margin:30px auto;padding:0 18px}}h1{{color:#dfce98}}.note{{line-height:1.7;color:#c9c5b9}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}}label{{border:1px solid #4f604f;border-radius:10px;padding:8px;background:#10231c;cursor:pointer}}label.sel{{outline:2px solid #dfce98}}img{{width:100%;aspect-ratio:70/120;object-fit:cover;border-radius:6px}}button{{padding:12px 18px;margin:14px 8px 14px 0;font-size:16px}}#count{{font-weight:700;color:#dfce98}}</style></head><body>
<h1>石虎塔羅 · 私人雙面試印</h1><p class="note">只供管理員使用。先選 4 張測試最方便：A4 2×2、成品 70×120 mm、正面一頁＋統一牌背一頁。列印時選「雙面」及「100% / 實際大小」，不要使用符合頁面。</p>
<p>已選 <span id="count">0</span> 張　<button id="first4">選前 4 張</button><button id="clear">清除</button><button id="print">產生雙面試印頁</button></p><div class="grid" id="grid"></div>
<script>const cards={data};const sel=new Set();const g=document.querySelector('#grid');function render(){{g.innerHTML='';cards.forEach(c=>{{const l=document.createElement('label');if(sel.has(c.id))l.className='sel';l.innerHTML=`<input type="checkbox" ${{sel.has(c.id)?'checked':''}}> <b>${{c.zh}}</b><br><small>${{c.en}}</small><img loading="lazy" src="/admin/print/card/${{encodeURIComponent(c.id)}}">`;l.onclick=e=>{{if(e.target.tagName==='IMG')return;e.preventDefault();sel.has(c.id)?sel.delete(c.id):sel.add(c.id);render()}};g.appendChild(l)}});document.querySelector('#count').textContent=sel.size}}render();document.querySelector('#first4').onclick=()=>{{sel.clear();cards.slice(0,4).forEach(c=>sel.add(c.id));render()}};document.querySelector('#clear').onclick=()=>{{sel.clear();render()}};document.querySelector('#print').onclick=()=>{{if(!sel.size)return alert('請至少選一張牌');location.href='/admin/print/sheet?cards='+encodeURIComponent([...sel].join(','))}};</script></body></html>'''


def _sheet_page(card_ids, manifest) -> str:
    valid = [cid for cid in card_ids if _master_path(cid, manifest)]
    if not valid:
        return ""
    # 4 cards per physical A4 sheet. Every front page is immediately followed
    # by its matching back page. The common back is symmetric, so slot reversal
    # is unnecessary for the prototype and both duplex flip modes remain usable.
    chunks = [valid[i:i + 4] for i in range(0, len(valid), 4)]
    pages = []
    for chunk in chunks:
        fronts = ''.join(f'<div class="slot"><img src="/admin/print/card/{quote(cid)}"></div>' for cid in chunk)
        backs = ''.join('<div class="slot"><img src="/admin/print/back.svg"></div>' for _ in chunk)
        pages.append(f'<section class="sheet fronts">{fronts}</section><section class="sheet backs">{backs}</section>')
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>石虎塔羅雙面試印</title><style>
@page{{size:A4 portrait;margin:0}}*{{box-sizing:border-box}}body{{margin:0;background:#ddd;font-family:system-ui,sans-serif}}.toolbar{{position:sticky;top:0;background:#111;color:#fff;padding:10px;z-index:2}}.sheet{{width:210mm;height:297mm;background:white;margin:8mm auto;display:grid;grid-template-columns:70mm 70mm;grid-template-rows:120mm 120mm;column-gap:4mm;row-gap:4mm;justify-content:center;align-content:center;break-after:page;page-break-after:always}}.slot{{width:70mm;height:120mm;position:relative;outline:.15mm solid #777}}.slot img{{display:block;width:70mm;height:120mm;object-fit:fill}}.slot:before,.slot:after{{content:"";position:absolute;pointer-events:none}}@media print{{body{{background:#fff}}.toolbar{{display:none}}.sheet{{margin:0;break-after:page;page-break-after:always}}}}
</style></head><body><div class="toolbar"><b>石虎塔羅雙面試印</b>　頁序：正面 → 牌背。請選雙面列印、A4、100% / 實際大小。 <button onclick="window.print()">列印</button></div>{''.join(pages)}</body></html>'''


def handle_print_get(handler, path: str, query: str, manifest) -> bool:
    if not (path == "/admin/print" or path.startswith("/admin/print/")):
        return False
    if not _authorized(handler):
        return True

    if path == "/admin/print":
        _send(handler, 200, _admin_page(manifest).encode("utf-8"), "text/html; charset=utf-8")
        return True
    if path == "/admin/print/back.svg":
        _send(handler, 200, _back_svg(), "image/svg+xml; charset=utf-8")
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
