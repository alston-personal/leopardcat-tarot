from pathlib import Path

root = Path(__file__).resolve().parents[1]
web = root / 'website'

THEMES = r'''from __future__ import annotations

import base64
import json
import re
import secrets
from pathlib import Path
from typing import Any

from .core import DivinationError

_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
_ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_MAX_ASSET = 8 * 1024 * 1024

BUILTIN_THEMES = {
    "leopardcat": {
        "theme_id": "leopardcat", "name": "靈山石虎", "source": "builtin",
        "colors": {"background": "#030504", "surface": "#111714", "accent": "#d4af37", "text": "#f4efe4"},
        "background_image": None, "card_back": None,
    },
    "midnight": {
        "theme_id": "midnight", "name": "午夜星空", "source": "builtin",
        "colors": {"background": "#080b17", "surface": "#12182c", "accent": "#9fa8ff", "text": "#f3f5ff"},
        "background_image": None, "card_back": None,
    },
    "minimal-light": {
        "theme_id": "minimal-light", "name": "極簡晨光", "source": "builtin",
        "colors": {"background": "#f5f1e8", "surface": "#ffffff", "accent": "#6e5138", "text": "#28231e"},
        "background_image": None, "card_back": None,
    },
}


def _clean(v: Any, n: int) -> str:
    return re.sub(r"[<>\x00]", "", str(v or "")).strip()[:n]


def _color(v: Any, fallback: str) -> str:
    s = str(v or "").strip()
    return s if re.fullmatch(r"#[0-9a-fA-F]{6}", s) else fallback


class ThemeRegistry:
    def __init__(self, custom_root: str | Path) -> None:
        self.root = Path(custom_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, theme_id: str | None) -> dict[str, Any]:
        tid = theme_id or "leopardcat"
        if tid in BUILTIN_THEMES:
            return dict(BUILTIN_THEMES[tid])
        if not _SAFE_ID.fullmatch(tid):
            raise DivinationError("invalid theme id")
        p = self.root / tid / "theme.json"
        if not p.exists():
            raise DivinationError("unknown theme")
        return json.loads(p.read_text(encoding="utf-8"))

    def list_builtin(self) -> list[dict[str, Any]]:
        return [{"theme_id": x["theme_id"], "name": x["name"], "source": "builtin"} for x in BUILTIN_THEMES.values()]

    def asset_path(self, theme_id: str, filename: str) -> Path:
        if not _SAFE_ID.fullmatch(theme_id) or not re.fullmatch(r"(?:background|card-back)\.(?:jpg|png|webp)", filename):
            raise DivinationError("invalid theme asset")
        p = self.root / theme_id / "assets" / filename
        if not p.exists():
            raise DivinationError("theme asset not found")
        return p


class ThemePublisher:
    def __init__(self, custom_root: str | Path) -> None:
        self.root = Path(custom_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _save_asset(self, raw_value: Any, asset_dir: Path, stem: str, theme_id: str) -> str | None:
        value = str(raw_value or "")
        if not value:
            return None
        m = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\s]+)", value)
        if not m:
            raise DivinationError("主題圖片格式不支援")
        mime, enc = m.groups()
        raw = base64.b64decode(enc, validate=False)
        if not raw or len(raw) > _MAX_ASSET:
            raise DivinationError("主題圖片單張請小於 8MB")
        ext = _ALLOWED[mime]
        fn = stem + ext
        (asset_dir / fn).write_bytes(raw)
        return f"/api/v1/themes/{theme_id}/assets/{fn}"

    def publish(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = _clean(payload.get("name"), 100) or "我的主題"
        theme_id = f"theme-{secrets.token_hex(4)}"
        td = self.root / theme_id
        assets = td / "assets"
        assets.mkdir(parents=True, exist_ok=False)
        try:
            colors = payload.get("colors") or {}
            background = self._save_asset(payload.get("background_image"), assets, "background", theme_id)
            card_back = self._save_asset(payload.get("card_back"), assets, "card-back", theme_id)
            data = {
                "schema_version": 1, "theme_id": theme_id, "name": name, "source": "custom",
                "colors": {
                    "background": _color(colors.get("background"), "#0b0b10"),
                    "surface": _color(colors.get("surface"), "#171721"),
                    "accent": _color(colors.get("accent"), "#d4af37"),
                    "text": _color(colors.get("text"), "#f5f2ea"),
                },
                "background_image": background, "card_back": card_back,
            }
            (td / "theme.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return data
        except Exception:
            import shutil
            shutil.rmtree(td, ignore_errors=True)
            raise
'''

AI_GATEWAY = r'''from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request


class AIUnavailable(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = True):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ZeroCostGeminiGateway:
    """Fail-closed gateway: one explicitly allowed model, no paid fallback.

    IMPORTANT: code cannot discover whether the Google Cloud project behind an API key
    has billing enabled. Operational zero-cost still requires a key from a billing-disabled
    Free Tier project. This class prevents silent provider/model fallback and treats quota/
    upstream failures as temporary unavailability.
    """

    ALLOWED_MODELS = {"gemini-2.5-flash"}

    def __init__(self, api_key: str | None, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        if self.model not in self.ALLOWED_MODELS:
            raise RuntimeError(f"model not allowed by zero-cost policy: {self.model}")
        self.context = ssl.create_default_context()

    def policy(self) -> dict:
        return {
            "cost_policy": "zero-cost-required",
            "provider": "gemini",
            "model": self.model,
            "paid_fallback": False,
            "billing_state_detectable_by_runtime": False,
            "requirement": "API key must belong to a billing-disabled Free Tier project",
        }

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise AIUnavailable("not_configured", "AI service is not configured", False)
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, context=self.context, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise AIUnavailable("free_quota_exhausted", "免費 AI 額度暫時用完，請稍後再試") from e
            if e.code in (500, 502, 503, 504):
                raise AIUnavailable("provider_busy", "AI 大師目前忙碌，請稍後重新解讀") from e
            raise AIUnavailable("provider_error", f"AI provider error {e.code}") from e
        except TimeoutError as e:
            raise AIUnavailable("provider_timeout", "AI 大師回應逾時，請稍後重新解讀") from e
'''

(web / 'divination' / 'themes.py').write_text(THEMES, encoding='utf-8')
(web / 'divination' / 'ai_gateway.py').write_text(AI_GATEWAY, encoding='utf-8')

# fortune_server.py
p = web / 'fortune_server.py'
s = p.read_text(encoding='utf-8')
s = s.replace('from divination.publishing import DeckPublisher\n', 'from divination.publishing import DeckPublisher\nfrom divination.themes import ThemeRegistry, ThemePublisher\nfrom divination.ai_gateway import ZeroCostGeminiGateway, AIUnavailable\n')
old_ctx = '''API_KEY = load_env_key()\nctx = ssl.create_default_context()\nctx.check_hostname = False\nctx.verify_mode = ssl.CERT_NONE\n'''
s = s.replace(old_ctx, '''API_KEY = load_env_key()\nAI_GATEWAY = ZeroCostGeminiGateway(API_KEY)\n''')
s = s.replace("DECK_PUBLISHER = DeckPublisher(os.path.join(DATA_DIR, 'custom_decks'))\n", "DECK_PUBLISHER = DeckPublisher(os.path.join(DATA_DIR, 'custom_decks'))\nTHEME_ROOT = os.path.join(DATA_DIR, 'custom_themes')\nTHEMES = ThemeRegistry(THEME_ROOT)\nTHEME_PUBLISHER = ThemePublisher(THEME_ROOT)\n")
start = s.index('def call_master_prompt(prompt):')
end = s.index('\nclass MyHttpRequestHandler', start)
s = s[:start] + 'def call_master_prompt(prompt):\n    return AI_GATEWAY.generate(prompt)\n' + s[end:]

get_marker = "        # 👑 API Endpoints\n"
get_block = '''        # 👑 API Endpoints\n        if path == '/api/v1/ai-policy':\n            self.send_response(200)\n            self.send_header('Content-type', 'application/json; charset=utf-8')\n            self.end_headers()\n            self.wfile.write(json.dumps(AI_GATEWAY.policy(), ensure_ascii=False).encode('utf-8'))\n            return\n        if path == '/api/v1/themes':\n            self.send_response(200)\n            self.send_header('Content-type', 'application/json; charset=utf-8')\n            self.end_headers()\n            self.wfile.write(json.dumps({'themes': THEMES.list_builtin()}, ensure_ascii=False).encode('utf-8'))\n            return\n        if path.startswith('/api/v1/themes/'):\n            parts = [x for x in path.split('/') if x]\n            try:\n                if len(parts) == 4:\n                    data = THEMES.get(parts[3])\n                    self.send_response(200)\n                    self.send_header('Content-type', 'application/json; charset=utf-8')\n                    self.send_header('Cache-Control', 'public, max-age=60')\n                    self.end_headers()\n                    self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))\n                    return\n                if len(parts) == 6 and parts[4] == 'assets':\n                    ap = THEMES.asset_path(parts[3], parts[5])\n                    raw = ap.read_bytes()\n                    mime = {'.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp'}[ap.suffix.lower()]\n                    self.send_response(200)\n                    self.send_header('Content-type', mime)\n                    self.send_header('Content-Length', str(len(raw)))\n                    self.send_header('Cache-Control', 'public, max-age=86400')\n                    self.end_headers()\n                    self.wfile.write(raw)\n                    return\n            except DivinationError:\n                self.send_error(404)\n                return\n'''
s = s.replace(get_marker, get_block, 1)

post_marker = "    def do_POST(self):\n"
post_block = '''    def do_POST(self):\n        if self.path == '/api/v1/themes':\n            content_length = int(self.headers.get('Content-Length', 0))\n            if content_length > 20 * 1024 * 1024:\n                self.send_response(413)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.end_headers()\n                self.wfile.write(json.dumps({'error':'theme_too_large','message':'主題圖片總量過大'}, ensure_ascii=False).encode('utf-8'))\n                return\n            try:\n                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))\n                result = THEME_PUBLISHER.publish(payload)\n                self.send_response(201)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.end_headers()\n                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))\n            except DivinationError as e:\n                self.send_response(400)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.end_headers()\n                self.wfile.write(json.dumps({'error':'invalid_theme','message':str(e)}, ensure_ascii=False).encode('utf-8'))\n            return\n'''
s = s.replace(post_marker, post_block, 1)

# AI errors should retain the reading session and tell frontend this is retryable.
needle = "            except DivinationError as e:\n                self.send_response(400)"
replacement = "            except AIUnavailable as e:\n                self.send_response(503 if e.retryable else 503)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Access-Control-Allow-Origin', '*')\n                self.end_headers()\n                self.wfile.write(json.dumps({'error': 'ai_unavailable', 'code': e.code, 'message': str(e), 'retryable': e.retryable, 'reading_id': locals().get('reading_id'), 'session_token': locals().get('issued_token')}, ensure_ascii=False).encode('utf-8'))\n            except DivinationError as e:\n                self.send_response(400)"
s = s.replace(needle, replacement, 1)
p.write_text(s, encoding='utf-8')

# create.html: optional theme section; no technical vocabulary.
p = web / 'public' / 'create.html'
s = p.read_text(encoding='utf-8')
anchor = '''  <section class="card">\n    <h2>4. 發布</h2>'''
theme_html = '''  <section class="card">\n    <h2>4. 選一個頁面風格（選填）</h2>\n    <p class="muted">不想調整就保持「靈山石虎」。也可以換成內建風格，或放一張自己的背景圖。</p>\n    <label>頁面風格</label>\n    <select id="theme-preset" style="width:100%;padding:12px;border:1px solid #cfc4b5;border-radius:10px;font:inherit">\n      <option value="leopardcat">靈山石虎</option><option value="midnight">午夜星空</option><option value="minimal-light">極簡晨光</option><option value="custom">自己設計</option>\n    </select>\n    <div id="theme-custom" class="hidden">\n      <div class="row">\n        <div><label>主色</label><input id="theme-accent" type="color" value="#d4af37" style="height:48px"></div>\n        <div><label>背景色</label><input id="theme-bg" type="color" value="#0b0b10" style="height:48px"></div>\n      </div>\n      <label>背景圖片（選填）</label><input id="theme-background" type="file" accept="image/jpeg,image/png,image/webp">\n      <label>牌背圖片（選填）</label><input id="theme-card-back" type="file" accept="image/jpeg,image/png,image/webp">\n      <p class="muted">直接選手機或電腦裡的圖片即可，系統會自動縮小。</p>\n    </div>\n  </section>\n\n  <section class="card">\n    <h2>5. 發布</h2>'''
if anchor not in s:
    raise SystemExit('create.html anchor missing')
s = s.replace(anchor, theme_html, 1)
p.write_text(s, encoding='utf-8')

# creator.js: publish custom theme before deck and append theme to share URL.
p = web / 'public' / 'creator.js'
s = p.read_text(encoding='utf-8')
insert_after = "  reversals.addEventListener('change', render);\n"
theme_js = r'''

  const themePreset = document.getElementById('theme-preset');
  const themeCustom = document.getElementById('theme-custom');
  themePreset.addEventListener('change', () => themeCustom.classList.toggle('hidden', themePreset.value !== 'custom'));

  async function fileToThemeData(file) {
    if (!file) return '';
    return await optimizeImage(file);
  }

  async function publishThemeIfNeeded() {
    if (themePreset.value !== 'custom') return themePreset.value;
    status.textContent = '正在準備你的頁面風格…';
    const payload = {
      name: `${document.getElementById('deck-name').value.trim()} 的風格`,
      colors: {
        background: document.getElementById('theme-bg').value,
        surface: '#171721', accent: document.getElementById('theme-accent').value, text: '#f5f2ea'
      },
      background_image: await fileToThemeData(document.getElementById('theme-background').files[0]),
      card_back: await fileToThemeData(document.getElementById('theme-card-back').files[0])
    };
    const r = await fetch('/api/v1/themes', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const raw = await r.text();
    let data = {}; try { data = JSON.parse(raw); } catch (_) {}
    if (!r.ok) throw new Error(data.message || (r.status === 413 ? '主題圖片太大，請換較小的圖片。' : '建立頁面風格失敗。'));
    return data.theme_id;
  }
'''
if insert_after not in s:
    raise SystemExit('creator.js insert anchor missing')
s = s.replace(insert_after, insert_after + theme_js, 1)

old = "      const resp = await fetch('/api/v1/decks', {"
new = "      const selectedThemeId = await publishThemeIfNeeded();\n      const resp = await fetch('/api/v1/decks', {"
s = s.replace(old, new, 1)
old_url = "      const url = new URL(data.share_path, location.origin).href;"
new_url = "      const u = new URL(data.share_path, location.origin); u.searchParams.set('theme', selectedThemeId); const url = u.href;"
s = s.replace(old_url, new_url, 1)
p.write_text(s, encoding='utf-8')

# main.js: runtime theme loader + switcher independent from deck/persona.
p = web / 'main.js'
s = p.read_text(encoding='utf-8')
active = "window.activeDeckId = new URLSearchParams(window.location.search).get('deck') || 'leopardcat';\n"
theme_runtime = r'''
window.activeThemeId = new URLSearchParams(window.location.search).get('theme') || (window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'minimal-light');

window.applyTheme = async function(themeId, updateUrl = false) {
    try {
        const resp = await fetch(`/api/v1/themes/${encodeURIComponent(themeId)}`, {cache:'no-cache'});
        if (!resp.ok) throw new Error(`THEME_${resp.status}`);
        const t = await resp.json();
        const c = t.colors || {};
        const root = document.documentElement;
        root.style.setProperty('--theme-background', c.background || '#030504');
        root.style.setProperty('--theme-surface', c.surface || '#111714');
        root.style.setProperty('--theme-accent', c.accent || '#d4af37');
        root.style.setProperty('--theme-text', c.text || '#f4efe4');
        document.body.style.backgroundColor = c.background || '#030504';
        document.body.style.color = c.text || '#f4efe4';
        if (t.background_image) {
            document.body.style.backgroundImage = `linear-gradient(#0006,#0006),url("${t.background_image}")`;
            document.body.style.backgroundSize = 'cover'; document.body.style.backgroundAttachment = 'fixed';
        } else document.body.style.backgroundImage = '';
        window.activeThemeId = t.theme_id;
        if (updateUrl) { const u = new URL(location.href); u.searchParams.set('theme', t.theme_id); history.replaceState(null,'',u); }
        const sel = document.getElementById('theme-switcher-select'); if (sel) sel.value = t.theme_id;
    } catch (e) { console.warn('Theme load failed', e); }
};

window.initThemeSwitcher = async function() {
    const box = document.createElement('div');
    box.id = 'theme-switcher';
    box.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:1200;background:#111c;border:1px solid #ffffff22;border-radius:999px;padding:6px 10px;backdrop-filter:blur(8px);font-size:12px';
    box.innerHTML = '<label style="display:flex;gap:6px;align-items:center">頁面風格 <select id="theme-switcher-select" style="border-radius:999px;padding:4px 8px"></select></label>';
    document.body.appendChild(box);
    const sel = box.querySelector('select');
    try {
        const r = await fetch('/api/v1/themes'); const d = await r.json();
        for (const t of d.themes || []) { const o=document.createElement('option'); o.value=t.theme_id; o.textContent=t.name; sel.appendChild(o); }
        if (![...sel.options].some(o=>o.value===window.activeThemeId)) { const o=document.createElement('option'); o.value=window.activeThemeId; o.textContent='這副牌的自訂風格'; sel.appendChild(o); }
        sel.value = window.activeThemeId; sel.addEventListener('change', ()=>window.applyTheme(sel.value,true));
    } catch (_) {}
    await window.applyTheme(window.activeThemeId);
};

document.addEventListener('DOMContentLoaded', () => window.initThemeSwitcher());
'''
if active not in s:
    raise SystemExit('main.js activeDeckId anchor missing')
s = s.replace(active, active + theme_runtime, 1)

# Better AI-unavailable UX: keep immutable reading ID/token for retry where returned.
old_catch = "        if (window.activeDeckId !== 'leopardcat') { alert('這副自訂牌暫時無法連線，請稍後再試。'); return; }"
new_catch = "        if (window.activeDeckId !== 'leopardcat') { alert(e?.message?.includes('503') ? 'AI 大師目前忙碌。你的牌組沒有問題，請稍後再按一次占卜。' : '這副牌目前無法完成占卜，請稍後再試。'); return; }"
s = s.replace(old_catch, new_catch, 1)
p.write_text(s, encoding='utf-8')

# tests
(root / 'tests' / 'test_themes_ai_policy.py').write_text(r'''import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'website'))

from divination.ai_gateway import ZeroCostGeminiGateway
from divination.themes import ThemePublisher, ThemeRegistry


def test_zero_cost_gateway_has_no_paid_fallback():
    g = ZeroCostGeminiGateway('fake')
    p = g.policy()
    assert p['cost_policy'] == 'zero-cost-required'
    assert p['paid_fallback'] is False
    assert p['billing_state_detectable_by_runtime'] is False


def test_custom_theme_round_trip():
    pixel = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Zl8sAAAAASUVORK5CYII='
    with tempfile.TemporaryDirectory() as td:
        pub = ThemePublisher(td)
        out = pub.publish({'name':'測試主題','colors':{'background':'#112233','accent':'#abcdef'},'background_image':pixel})
        reg = ThemeRegistry(td)
        got = reg.get(out['theme_id'])
        assert got['name'] == '測試主題'
        assert got['colors']['background'] == '#112233'
        assert got['background_image'].startswith('/api/v1/themes/')


def test_builtin_theme_switchable():
    with tempfile.TemporaryDirectory() as td:
        reg = ThemeRegistry(td)
        ids = {x['theme_id'] for x in reg.list_builtin()}
        assert {'leopardcat','midnight','minimal-light'} <= ids
''', encoding='utf-8')

print('theme_zero_cost_patch=applied')
