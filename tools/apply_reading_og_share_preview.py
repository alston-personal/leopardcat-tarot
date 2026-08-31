from pathlib import Path

# fortune_server.py
p = Path('website/fortune_server.py')
s = p.read_text(encoding='utf-8')
if 'import base64\n' not in s:
    s = s.replace('import http.server\n', 'import http.server\nimport base64\n', 1)

get_anchor = """        # 👑 API Endpoints\n        if path == '/api/v1/methods':\n"""
get_add = """        # 👑 API Endpoints\n        share_image_match = re.fullmatch(r'/api/v1/readings/([^/]+)/share-image\\.png', path)\n        if share_image_match:\n            reading_id = share_image_match.group(1)\n            params = urllib.parse.parse_qs(query)\n            share_token = (params.get('shareToken') or [''])[0]\n            try:\n                SESSION_STORE.get_shared(reading_id, share_token)\n                image_path = os.path.join(DATA_DIR, 'share_images', f'{reading_id}.png')\n                if not os.path.isfile(image_path):\n                    raise DivinationError('share image not found')\n                raw = open(image_path, 'rb').read()\n                self.send_response(200)\n                self.send_header('Content-type', 'image/png')\n                self.send_header('Content-Length', str(len(raw)))\n                self.send_header('Cache-Control', 'public, max-age=300')\n                self.end_headers()\n                self.wfile.write(raw)\n            except DivinationError:\n                self.send_error(404)\n            return\n        if path == '/api/v1/methods':\n"""
if get_anchor not in s:
    raise SystemExit('GET anchor missing')
s = s.replace(get_anchor, get_add, 1)

root_old = """            deck_id = (params.get('deck') or ['leopardcat'])[0]\n            card_id = (params.get('card') or [None])[0]\n            \n            index_path = os.path.join(DIRECTORY, 'index.html')\n"""
root_new = """            deck_id = (params.get('deck') or ['leopardcat'])[0]\n            card_id = (params.get('card') or [None])[0]\n            reading_id = (params.get('reading') or [None])[0]\n            share_token = (params.get('share') or [None])[0]\n            shared_reading = None\n            if reading_id and share_token:\n                try:\n                    shared_reading = SESSION_STORE.get_shared(reading_id, share_token)\n                    deck_id = shared_reading.get('deck_id') or deck_id\n                except DivinationError:\n                    shared_reading = None\n            \n            index_path = os.path.join(DIRECTORY, 'index.html')\n"""
if root_old not in s:
    raise SystemExit('root param anchor missing')
s = s.replace(root_old, root_new, 1)

meta_old = """                meta_title = brand.app_name\n                meta_desc = brand.description\n                fallback_card = active_deck.cards[0] if active_deck.cards else {}\n                selected_card = next((c for c in active_deck.cards if c.get('id') == card_id), None) if card_id else None\n                card_for_image = selected_card or fallback_card\n                image_path = str(card_for_image.get('image') or 'art/renders/card-00-the-fool.webp')\n                meta_img = image_path if image_path.startswith(('http://', 'https://')) else f\"{base_url}/{image_path.lstrip('/')}\"\n\n                if selected_card:\n"""
meta_new = """                meta_title = brand.app_name\n                meta_desc = brand.description\n                fallback_card = active_deck.cards[0] if active_deck.cards else {}\n                reading_specs = ((shared_reading or {}).get('method_result') or {}).get('cards') or []\n                reading_card_id = (reading_specs[0].get('card_id') or reading_specs[0].get('id')) if reading_specs else None\n                selected_card = next((c for c in active_deck.cards if c.get('id') == (reading_card_id or card_id)), None) if (reading_card_id or card_id) else None\n                card_for_image = selected_card or fallback_card\n                image_path = str(card_for_image.get('image') or 'art/renders/card-00-the-fool.webp')\n                meta_img = image_path if image_path.startswith(('http://', 'https://')) else f\"{base_url}/{image_path.lstrip('/')}\"\n                meta_img_type = 'image/webp' if meta_img.lower().endswith('.webp') else ('image/png' if meta_img.lower().endswith('.png') else 'image/jpeg')\n                meta_img_width, meta_img_height = 1200, 1800\n\n                if shared_reading and reading_specs:\n                    labels = []\n                    for spec in reading_specs[:3]:\n                        cid = spec.get('card_id') or spec.get('id')\n                        card = next((c for c in active_deck.cards if c.get('id') == cid), None) or {}\n                        titles = card.get('title') or {}\n                        title = (titles.get('zh') or titles.get('zh-TW') or titles.get('en') or cid) if isinstance(titles, dict) else str(titles or cid or '')\n                        if spec.get('orientation') == 'reversed':\n                            title += '（逆位）'\n                        labels.append(title)\n                    spread = ((shared_reading.get('method_result') or {}).get('spread') or 'tarot')\n                    meta_title = f\"{brand.app_name}｜{'、'.join(labels)}\"\n                    meta_desc = f\"{spread} · {'、'.join(labels)}\"\n                    persisted = os.path.join(DATA_DIR, 'share_images', f'{reading_id}.png')\n                    if os.path.isfile(persisted):\n                        meta_img = f\"{base_url}/api/v1/readings/{urllib.parse.quote(reading_id)}/share-image.png?shareToken={urllib.parse.quote(share_token)}\"\n                        meta_img_type = 'image/png'\n                        meta_img_width = meta_img_height = 600\n\n                if selected_card and not shared_reading:\n"""
if meta_old not in s:
    raise SystemExit('meta anchor missing')
s = s.replace(meta_old, meta_new, 1)

og_old = """    <meta property=\"og:image:type\" content=\"image/webp\">\n    <meta property=\"og:image:width\" content=\"1200\">\n    <meta property=\"og:image:height\" content=\"1800\">\n"""
og_new = """    <meta property=\"og:image:type\" content=\"{meta_img_type}\">\n    <meta property=\"og:image:width\" content=\"{meta_img_width}\">\n    <meta property=\"og:image:height\" content=\"{meta_img_height}\">\n"""
if og_old not in s:
    raise SystemExit('OG dimensions anchor missing')
s = s.replace(og_old, og_new, 1)

post_anchor = """    def do_POST(self):\n        path = self.path.split('?', 1)[0]\n"""
post_new = """    def do_POST(self):\n        path = self.path.split('?', 1)[0]\n        share_image_match = re.fullmatch(r'/api/v1/readings/([^/]+)/share-image', path)\n        if share_image_match:\n            reading_id = share_image_match.group(1)\n            content_length = int(self.headers.get('Content-Length', 0))\n            if content_length <= 0 or content_length > 4 * 1024 * 1024:\n                self.send_error(413); return\n            try:\n                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))\n                SESSION_STORE.get(reading_id, str(payload.get('session_token') or ''))\n                image = str(payload.get('image') or '')\n                match = re.fullmatch(r'data:image/png;base64,([A-Za-z0-9+/=\\s]+)', image)\n                if not match:\n                    raise DivinationError('invalid share image')\n                raw = base64.b64decode(match.group(1), validate=False)\n                if not raw.startswith(b'\\x89PNG\\r\\n\\x1a\\n') or len(raw) > 3 * 1024 * 1024:\n                    raise DivinationError('invalid share image')\n                share_dir = os.path.join(DATA_DIR, 'share_images')\n                os.makedirs(share_dir, exist_ok=True)\n                tmp = os.path.join(share_dir, f'.{reading_id}.tmp')\n                final = os.path.join(share_dir, f'{reading_id}.png')\n                with open(tmp, 'wb') as f:\n                    f.write(raw)\n                os.replace(tmp, final)\n                self.send_response(201)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Cache-Control', 'no-store')\n                self.end_headers()\n                self.wfile.write(json.dumps({'stored': True, 'reading_id': reading_id}).encode('utf-8'))\n            except (DivinationError, ValueError, TypeError):\n                self.send_response(403)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.end_headers()\n                self.wfile.write(json.dumps({'error':'share_image_denied'}).encode('utf-8'))\n            return\n"""
if post_anchor not in s:
    raise SystemExit('POST anchor missing')
s = s.replace(post_anchor, post_new, 1)
p.write_text(s, encoding='utf-8')

# main.js
p = Path('website/main.js')
s = p.read_text(encoding='utf-8')
helper_anchor = """// 📸 Share Image Generator\nwindow.generateShareImage = async function() {\n"""
helper = """async function persistReadingSharePreview(blob) {\n    const envelope = window.currentReadingEnvelope;\n    if (!blob || !envelope?.reading_id || !envelope?.session_token) return false;\n    try {\n        const image = await new Promise((resolve, reject) => {\n            const reader = new FileReader();\n            reader.onload = () => resolve(reader.result);\n            reader.onerror = reject;\n            reader.readAsDataURL(blob);\n        });\n        const response = await fetch(`/api/v1/readings/${encodeURIComponent(envelope.reading_id)}/share-image`, {\n            method: 'POST',\n            headers: {'Content-Type': 'application/json'},\n            body: JSON.stringify({session_token: envelope.session_token, image})\n        });\n        if (!response.ok) throw new Error(`share preview persist ${response.status}`);\n        return true;\n    } catch (error) {\n        console.warn('[Share] OG preview persistence unavailable', error);\n        return false;\n    }\n}\n\n// 📸 Share Image Generator\nwindow.generateShareImage = async function() {\n"""
if helper_anchor not in s:
    raise SystemExit('main helper anchor missing')
s = s.replace(helper_anchor, helper, 1)
blob_old = """        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));\n        const filePrefix = window.activeBrand?.file_prefix || 'tarot';\n"""
blob_new = """        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));\n        await persistReadingSharePreview(blob); // social crawlers can now resolve the actual deck-owned share card.\n        const filePrefix = window.activeBrand?.file_prefix || 'tarot';\n"""
if blob_old not in s:
    raise SystemExit('blob anchor missing')
s = s.replace(blob_old, blob_new, 1)
p.write_text(s, encoding='utf-8')

# tests
Path('website/tests/test_reading_og_share_preview.py').write_text(r'''from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_share_png_is_session_authorized_and_public_read_is_share_token_authorized():
    server = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')
    assert "SESSION_STORE.get(reading_id, str(payload.get('session_token') or ''))" in server
    assert "SESSION_STORE.get_shared(reading_id, share_token)" in server
    assert "share-image.png?shareToken=" in server
    assert "data:image/png;base64" in server


def test_reading_og_uses_persisted_deck_owned_share_card_without_private_text():
    server = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')
    assert "shared_reading = SESSION_STORE.get_shared(reading_id, share_token)" in server
    assert "meta_img_type = 'image/png'" in server
    assert "meta_img_width = meta_img_height = 600" in server
    og_section = server[server.index('# 🔮 Dynamic SEO / Open Graph Injection'):server.index('super().do_GET()')]
    assert 'question' not in og_section.lower()
    assert "shared_reading.get('reading')" not in og_section


def test_browser_uploads_rendered_png_before_social_share():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    assert 'async function persistReadingSharePreview(blob)' in js
    assert "body: JSON.stringify({session_token: envelope.session_token, image})" in js
    assert "await persistReadingSharePreview(blob);" in js
    assert js.index('await persistReadingSharePreview(blob);') < js.index('navigator.share({', js.index('await persistReadingSharePreview(blob);'))
''', encoding='utf-8')

# capability ledger
p = Path('governance/capabilities.json')
data = p.read_text(encoding='utf-8')
needle = '    "sharing.deck-owned-share-theme": {'
pos = data.find(needle)
if pos < 0:
    raise SystemExit('capability anchor missing')
entry = '''    "sharing.reading-og-share-preview": {\n      "status": "protected",\n      "owner": "website",\n      "contract": [\n        "A reading share URL MUST expose Open Graph metadata from the immutable read-only reading receipt rather than falling back to an unrelated deck card.",\n        "When the browser has rendered the deck-owned 600x600 share card, it MAY persist that PNG using the private reading session token; the public share token grants read-only access to that image while the reading receipt remains valid.",\n        "OG metadata and persisted share images MUST NOT upload or expose the private question or AI answer.",\n        "If no persisted share image exists, social preview MUST degrade to a card image from the same reading/deck instead of a global LeopardCat fallback."\n      ],\n      "evidence": [\n        "website/fortune_server.py",\n        "website/main.js",\n        "website/tests/test_reading_og_share_preview.py"\n      ]\n    },\n'''
data = data[:pos] + entry + data[pos:]
p.write_text(data, encoding='utf-8')
