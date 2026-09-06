import http.server
import base64
import socketserver
import json
import urllib.request
import urllib.error
import urllib.parse
import html
import os
import ssl
import traceback
import sys
import re
import threading
import time

from divination import ReadingRequest, build_default_engine
from divination.core import DivinationError
from divination.sessions import ReadingSessionStore
from divination.publishing import DeckPublisher
from divination.themes import ThemeRegistry, ThemePublisher
from divination.ai_gateway import ZeroCostGeminiGateway, ZeroCostGroqGateway, ZeroCostOpenRouterGateway, ZeroCostProviderPool, AIUnavailable
from divination.brands import BrandRegistry
from divination.personas import persona_public_info, ConfigurablePersona
from divination.persona_publishing import PersonaPublisher
from divination.capsules import build_capsule, public_handoff
from divination.lenormand import public_method_info as lenormand_public_method_info

PORT = 8088
DIRECTORY = "dist"

# 📚 Manifest Cache for Dynamic SEO/OG Tags
CARD_MANIFEST = []
try:
    manifest_path = os.path.join(DIRECTORY, 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            CARD_MANIFEST = json.load(f)
        print(f"✅ Loaded {len(CARD_MANIFEST)} cards into memory for dynamic OG tags.")
except Exception as e:
    print(f"❌ Failed to load manifest: {e}")

def log(msg):
    print(msg, flush=True)

def update_stats(divination=False):
    try:
        if not os.path.exists('stats.json'):
            with open('stats.json', 'w') as f: 
                json.dump({"total_visitors": 2026, "total_divinations": 888}, f)
        
        with open('stats.json', 'r+') as sf:
            sdata = json.load(sf)
            if divination:
                sdata['total_divinations'] = sdata.get('total_divinations', 0) + 1
            else:
                sdata['total_visitors'] = sdata.get('total_visitors', 0) + 1
            sf.seek(0)
            json.dump(sdata, sf)
            sf.truncate()
            return sdata
    except Exception as e:
        log(f"Error updating stats: {e}")
        return {"total_visitors": 2026, "total_divinations": 888, "error": str(e)}

def load_env_value(name):
    value = os.environ.get(name)
    if value:
        return value
    env_path = "/home/ubuntu/agentmanager/.env"
    if os.path.exists(env_path):
        try:
            with open(env_path) as f:
                for line in f:
                    if line.startswith(name + "="):
                        return line.strip().split("=", 1)[1]
        except Exception as e:
            log(f"Error reading runtime env file: {e}")
    return None


def build_ai_gateway():
    groq_key = load_env_value("GROQ_API_KEY")
    providers = [
        ZeroCostGeminiGateway(load_env_value("GEMINI_API_KEY")),
        ZeroCostGroqGateway(groq_key, load_env_value("GROQ_MODEL") or "openai/gpt-oss-120b"),
        ZeroCostGroqGateway(groq_key, "openai/gpt-oss-20b"),
        ZeroCostGroqGateway(groq_key, "qwen/qwen3.6-27b"),
    ]
    openrouter_key = load_env_value("OPENROUTER_API_KEY")
    openrouter_model = load_env_value("OPENROUTER_MODEL")
    if openrouter_key or openrouter_model:
        providers.append(ZeroCostOpenRouterGateway(openrouter_key, openrouter_model))
    return ZeroCostProviderPool(providers)


AI_GATEWAY = build_ai_gateway()

DIVINATION_ENGINE = build_default_engine(os.path.dirname(os.path.abspath(__file__)))
BRANDS = BrandRegistry(DIVINATION_ENGINE.decks)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
SESSION_STORE = ReadingSessionStore(os.path.join(DATA_DIR, 'reading_sessions.sqlite3'), ttl_seconds=86400)
DECK_PUBLISHER = DeckPublisher(os.path.join(DATA_DIR, 'custom_decks'))
THEME_ROOT = os.path.join(DATA_DIR, 'custom_themes')
THEMES = ThemeRegistry(THEME_ROOT)
THEME_PUBLISHER = ThemePublisher(THEME_ROOT)
PERSONA_ROOT = os.path.join(DATA_DIR, 'custom_personas')
PERSONA_PUBLISHER = PersonaPublisher(PERSONA_ROOT)
THREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'

READING_REQUEST_LOCK = threading.Lock()
READING_REQUESTS_IN_FLIGHT = {}
READING_REQUEST_TTL_SECONDS = 180

def begin_reading_request(client_request_id):
    if not client_request_id:
        return True
    now = time.time()
    with READING_REQUEST_LOCK:
        stale = [key for key, started in READING_REQUESTS_IN_FLIGHT.items() if now - started > READING_REQUEST_TTL_SECONDS]
        for key in stale:
            READING_REQUESTS_IN_FLIGHT.pop(key, None)
        if client_request_id in READING_REQUESTS_IN_FLIGHT:
            return False
        READING_REQUESTS_IN_FLIGHT[client_request_id] = now
        return True

def end_reading_request(client_request_id):
    if not client_request_id:
        return
    with READING_REQUEST_LOCK:
        READING_REQUESTS_IN_FLIGHT.pop(client_request_id, None)

THREADS_ALLOWED_HOSTS = {'threads.com','www.threads.com','threads.net','www.threads.net'}
THREADS_CANONICAL_PATH_RE = re.compile(r'/@[^/]+/post/[A-Za-z0-9_-]+/?$')
THREADS_SHARE_PATH_RE = re.compile(r'/share/[A-Za-z0-9_-]+/?$')

class ThreadsSafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != 'https' or (parsed.hostname or '').lower() not in THREADS_ALLOWED_HOSTS:
            raise urllib.error.HTTPError(newurl, 403, 'threads_redirect_not_allowed', headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def canonicalize_threads_source_url(source_url):
    parsed = urllib.parse.urlsplit(str(source_url or '').strip())
    if parsed.scheme != 'https' or (parsed.hostname or '').lower() not in THREADS_ALLOWED_HOSTS:
        raise ValueError('invalid_threads_post_url')
    if THREADS_CANONICAL_PATH_RE.fullmatch(parsed.path):
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ''))
    if not THREADS_SHARE_PATH_RE.fullmatch(parsed.path):
        raise ValueError('invalid_threads_post_url')
    opener = urllib.request.build_opener(ThreadsSafeRedirectHandler())
    request = urllib.request.Request(source_url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; LeopardCat-Tarot/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
    })
    with opener.open(request, timeout=12) as response:
        final_url = response.geturl()
        response.read(1)
    final = urllib.parse.urlsplit(final_url)
    if final.scheme != 'https' or (final.hostname or '').lower() not in THREADS_ALLOWED_HOSTS or not THREADS_CANONICAL_PATH_RE.fullmatch(final.path):
        raise ValueError('threads_share_redirect_unresolved')
    return urllib.parse.urlunsplit((final.scheme, final.netloc, final.path, final.query, ''))

def call_master_prompt(prompt):
    return AI_GATEWAY.generate(prompt)


def method_catalog():
    return [
        {
            'method_id': 'tarot',
            'name': '塔羅 Tarot',
            'description': '以牌陣位置與正逆位解讀；牌組可替換。',
            'spreads': [
                {'id':'single','name':'單張指引','card_count':1},
                {'id':'three_card','name':'過去・現在・未來','card_count':3},
                {'id':'decision','name':'選擇題','card_count':3},
            ],
        },
        lenormand_public_method_info(),
    ]


def persona_used_by_decks(persona_id):
    refs = []
    try:
        for directory in DECK_PUBLISHER.root.iterdir():
            manifest = directory / 'deck.json'
            if not manifest.is_file():
                continue
            data = json.loads(manifest.read_text(encoding='utf-8'))
            if str(data.get('default_persona') or 'master') == persona_id:
                refs.append(str(data.get('deck_id') or directory.name))
    except Exception:
        pass
    return refs

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        url_parts = self.path.split('?', 1)
        path = url_parts[0]
        query = url_parts[1] if len(url_parts) > 1 else ""

        # 👑 API Endpoints
        share_image_match = re.fullmatch(r'/api/v1/readings/([^/]+)/share-image\.png', path)
        if share_image_match:
            reading_id = share_image_match.group(1)
            params = urllib.parse.parse_qs(query)
            share_token = (params.get('shareToken') or [''])[0]
            try:
                SESSION_STORE.get_shared(reading_id, share_token)
                image_path = os.path.join(DATA_DIR, 'share_images', f'{reading_id}.png')
                if not os.path.isfile(image_path):
                    raise DivinationError('share image not found')
                raw = open(image_path, 'rb').read()
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.send_header('Content-Length', str(len(raw)))
                self.send_header('Cache-Control', 'public, max-age=300')
                self.end_headers()
                self.wfile.write(raw)
            except DivinationError:
                self.send_error(404)
            return
        if path == '/api/v1/methods':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'public, max-age=60')
            self.end_headers()
            self.wfile.write(json.dumps({'methods': method_catalog()}, ensure_ascii=False).encode('utf-8'))
            return
        if path.startswith('/api/v1/readings/'):
            reading_id = path.rsplit('/', 1)[-1]
            params = urllib.parse.parse_qs(query)
            share_token = (params.get('shareToken') or [''])[0]
            try:
                shared = SESSION_STORE.get_shared(reading_id, share_token)
                body = {
                    **shared,
                    'privacy': {'question_stored': False, 'answer_stored': False, 'symbolic_state_ttl_hours': 24},
                    'share_mode': 'symbolic-read-only',
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'private, no-store')
                self.end_headers()
                self.wfile.write(json.dumps(body, ensure_ascii=False).encode('utf-8'))
            except DivinationError:
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'shared_reading_not_found'}, ensure_ascii=False).encode('utf-8'))
            return
        if path.startswith('/api/v1/manage/decks/'):
            deck_id = path.rsplit('/', 1)[-1]
            try:
                data = DECK_PUBLISHER.management_info(deck_id, self.headers.get('X-Management-Token', ''))
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            except DivinationError as e:
                self.send_response(403)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'management_denied','message':str(e)}, ensure_ascii=False).encode('utf-8'))
            return
        if path.startswith('/api/v1/manage/personas/'):
            persona_id = path.rsplit('/', 1)[-1]
            try:
                data = PERSONA_PUBLISHER.management_info(persona_id, self.headers.get('X-Management-Token', ''))
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            except DivinationError as e:
                self.send_response(403)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'management_denied','message':str(e)}, ensure_ascii=False).encode('utf-8'))
            return
        if path == '/api/v1/ai-policy':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(AI_GATEWAY.policy(), ensure_ascii=False).encode('utf-8'))
            return
        if path == '/api/v1/personas':
            params = urllib.parse.parse_qs(query)
            deck_id = (params.get('deck') or ['leopardcat'])[0]
            try:
                deck = DIVINATION_ENGINE.decks.get(deck_id)
                default_persona = deck.default_persona
                items = []
                for pid in DIVINATION_ENGINE.personas.capabilities():
                    info = persona_public_info(DIVINATION_ENGINE.personas.get(pid))
                    # Custom personas are unlisted. A deck exposes only its own default custom persona.
                    if info.get('source') != 'custom' or pid == default_persona:
                        items.append(info)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'public, max-age=60')
                self.end_headers()
                self.wfile.write(json.dumps({'default_persona': default_persona, 'personas': items}, ensure_ascii=False).encode('utf-8'))
            except DivinationError:
                self.send_error(404)
            return
        if path.startswith('/api/v1/personas/'):
            persona_id = path.rsplit('/', 1)[-1]
            try:
                info = persona_public_info(DIVINATION_ENGINE.personas.get(persona_id))
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'public, max-age=60')
                self.end_headers()
                self.wfile.write(json.dumps(info, ensure_ascii=False).encode('utf-8'))
            except DivinationError:
                self.send_error(404)
            return
        if path.startswith('/api/v1/brands/'):
            deck_id = path.rsplit('/', 1)[-1]
            try:
                data = BRANDS.public_info(deck_id)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'public, max-age=60')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            except DivinationError:
                self.send_error(404)
            return
        if path == '/api/v1/themes':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'themes': THEMES.list_builtin()}, ensure_ascii=False).encode('utf-8'))
            return
        if path.startswith('/api/v1/themes/'):
            parts = [x for x in path.split('/') if x]
            try:
                if len(parts) == 4:
                    data = THEMES.get(parts[3])
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Cache-Control', 'public, max-age=60')
                    self.end_headers()
                    self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
                    return
                if len(parts) == 6 and parts[4] == 'assets':
                    ap = THEMES.asset_path(parts[3], parts[5])
                    raw = ap.read_bytes()
                    mime = {'.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp'}[ap.suffix.lower()]
                    self.send_response(200)
                    self.send_header('Content-type', mime)
                    self.send_header('Content-Length', str(len(raw)))
                    self.send_header('Cache-Control', 'public, max-age=86400')
                    self.end_headers()
                    self.wfile.write(raw)
                    return
            except DivinationError:
                self.send_error(404)
                return
        if path.startswith('/api/v1/deck-slugs/'):
            slug = path.rsplit('/', 1)[-1].lower()
            result = DECK_PUBLISHER.slug_available(slug)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            return
        if path.startswith('/api/v1/decks/'):
            parts = [p for p in path.split('/') if p]
            try:
                if len(parts) == 4:
                    deck_id = parts[3]
                    info = DIVINATION_ENGINE.decks.public_info(deck_id)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Cache-Control', 'public, max-age=60')
                    self.end_headers()
                    self.wfile.write(json.dumps(info, ensure_ascii=False).encode('utf-8'))
                    return
                if len(parts) == 6 and parts[4] == 'images':
                    deck_id, filename = parts[3], parts[5]
                    image_path = DECK_PUBLISHER.image_path(deck_id, filename)
                    ext = image_path.suffix.lower()
                    mime = {'.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp'}[ext]
                    raw = image_path.read_bytes()
                    self.send_response(200)
                    self.send_header('Content-type', mime)
                    self.send_header('Content-Length', str(len(raw)))
                    self.send_header('Cache-Control', 'public, max-age=86400')
                    self.end_headers()
                    self.wfile.write(raw)
                    return
            except DivinationError:
                self.send_error(404)
                return
        if path == '/api/stats':
            sdata = update_stats(divination=False)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(sdata).encode('utf-8'))
            return

        # 🔮 Dynamic SEO / Open Graph Injection for Social Sharing
        if path == '/' or path == '/index.html':
            params = urllib.parse.parse_qs(query)
            deck_id = (params.get('deck') or ['leopardcat'])[0]
            card_id = (params.get('card') or [None])[0]
            reading_id = (params.get('reading') or [None])[0]
            share_token = (params.get('share') or [None])[0]
            shared_reading = None
            if reading_id and share_token:
                try:
                    shared_reading = SESSION_STORE.get_shared(reading_id, share_token)
                    deck_id = shared_reading.get('deck_id') or deck_id
                except DivinationError:
                    shared_reading = None
            
            index_path = os.path.join(DIRECTORY, 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 🌿 Construction of metadata from the active Brand Pack + Deck Module.
                host = 'leopardcat-tarot.milkcat.org'
                base_url = f"https://{host}"
                try:
                    brand = BRANDS.get(deck_id)
                    active_deck = DIVINATION_ENGINE.decks.get(deck_id)
                except DivinationError:
                    brand = BRANDS.get('leopardcat')
                    active_deck = DIVINATION_ENGINE.decks.get('leopardcat')
                    deck_id = 'leopardcat'

                meta_title = brand.app_name
                meta_desc = brand.description
                fallback_card = active_deck.cards[0] if active_deck.cards else {}
                reading_specs = ((shared_reading or {}).get('method_result') or {}).get('cards') or []
                reading_card_id = (reading_specs[0].get('card_id') or reading_specs[0].get('id')) if reading_specs else None
                selected_card = next((c for c in active_deck.cards if c.get('id') == (reading_card_id or card_id)), None) if (reading_card_id or card_id) else None
                card_for_image = selected_card or fallback_card
                image_path = str(card_for_image.get('image') or 'art/renders/card-00-the-fool.webp')
                meta_img = image_path if image_path.startswith(('http://', 'https://')) else f"{base_url}/{image_path.lstrip('/')}"
                meta_img_type = 'image/webp' if meta_img.lower().endswith('.webp') else ('image/png' if meta_img.lower().endswith('.png') else 'image/jpeg')
                meta_img_width, meta_img_height = 1200, 1800

                if shared_reading and reading_specs:
                    labels = []
                    for spec in reading_specs[:3]:
                        cid = spec.get('card_id') or spec.get('id')
                        card = next((c for c in active_deck.cards if c.get('id') == cid), None) or {}
                        titles = card.get('title') or {}
                        title = (titles.get('zh') or titles.get('zh-TW') or titles.get('en') or cid) if isinstance(titles, dict) else str(titles or cid or '')
                        if spec.get('orientation') == 'reversed':
                            title += '（逆位）'
                        labels.append(title)
                    spread = ((shared_reading.get('method_result') or {}).get('spread') or 'tarot')
                    meta_title = f"{brand.app_name}｜{'、'.join(labels)}"
                    meta_desc = f"{spread} · {'、'.join(labels)}"
                    persisted = os.path.join(DATA_DIR, 'share_images', f'{reading_id}.png')
                    if os.path.isfile(persisted):
                        meta_img = f"{base_url}/api/v1/readings/{urllib.parse.quote(reading_id)}/share-image.png?shareToken={urllib.parse.quote(share_token)}"
                        meta_img_type = 'image/png'
                        meta_img_width, meta_img_height = 1200, 630

                if selected_card and not shared_reading:
                    titles = selected_card.get('title') or {}
                    if isinstance(titles, dict):
                        title_zh = titles.get('zh') or titles.get('zh-TW') or titles.get('en') or selected_card.get('id', '')
                    else:
                        title_zh = str(titles or selected_card.get('id', ''))
                    meta_title = brand.share_copy_template.get('zh', '{card}').replace('{card}', title_zh)
                    meanings = selected_card.get('meanings') or selected_card.get('meaning') or {}
                    if isinstance(meanings, dict):
                        raw_desc = meanings.get('upright') or meanings.get('zh') or meanings.get('zh-TW') or meanings.get('en') or ''
                    else:
                        raw_desc = str(meanings)
                    if raw_desc:
                        meta_desc = str(raw_desc)[:160]

                meta_title = html.escape(str(meta_title), quote=True)
                meta_desc = html.escape(str(meta_desc), quote=True)
                meta_img = html.escape(str(meta_img), quote=True)

                # 🌿 Use Placeholder Replacement (Robust & Reliable)
                # Match: <title data-i18n="hero.title">石虎塔羅 LeopardCat Tarot</title>
                content = content.replace('石虎塔羅 LeopardCat Tarot', meta_title)
                # Match: <meta name="description" content="...">
                content = content.replace('靈山靈貓：一場連結生態與心靈的塔羅之旅。讓石虎為您指引方向。', meta_desc)
                
                # 🖼️ Inject Unified OG Tags
                og_tags = f"""
    <title>{meta_title}</title>
    <meta name="description" content="{meta_desc}">
    <meta property="og:title" content="{meta_title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:image" content="{meta_img}">
    <meta property="og:image:secure_url" content="{meta_img}">
    <meta property="og:image:type" content="{meta_img_type}">
    <meta property="og:image:width" content="{meta_img_width}">
    <meta property="og:image:height" content="{meta_img_height}">
    <meta property="og:image:alt" content="{meta_title}">
    <meta property="og:url" content="{base_url}{self.path}">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="{meta_img}">"""
                content = content.replace('<!-- 🌿 Spirit Mirror: Dynamic OG Tags v45 -->', og_tags)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                return

        super().do_GET()

    def do_PATCH(self):
        path = self.path.split('?', 1)[0]
        token = self.headers.get('X-Management-Token', '')
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 128 * 1024:
            self.send_error(413); return
        try:
            payload = json.loads(self.rfile.read(content_length).decode('utf-8') or '{}')
            if path.startswith('/api/v1/manage/decks/'):
                deck_id = path.rsplit('/', 1)[-1]
                if 'theme' in payload:
                    THEMES.get(str(payload.get('theme') or '').strip())
                if 'persona' in payload:
                    pid = str(payload.get('persona') or '').strip()
                    persona = DIVINATION_ENGINE.personas.get(pid)
                    info = persona_public_info(persona)
                    if 'tarot' not in (info.get('methods') or []):
                        raise DivinationError('這位解讀師不支援塔羅')
                data = DECK_PUBLISHER.update_metadata(deck_id, token, payload)
            elif path.startswith('/api/v1/manage/personas/'):
                persona_id = path.rsplit('/', 1)[-1]
                data = PERSONA_PUBLISHER.update(persona_id, token, payload)
                DIVINATION_ENGINE.personas.replace(ConfigurablePersona(PERSONA_PUBLISHER.pack_path(persona_id)))
            else:
                self.send_error(404); return
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except DivinationError as e:
            self.send_response(403)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'error':'management_denied','message':str(e)}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            log(f'!!! MANAGEMENT PATCH ERROR: {e}')
            self.send_response(500); self.end_headers()

    def do_DELETE(self):
        path = self.path.split('?', 1)[0]
        token = self.headers.get('X-Management-Token', '')
        try:
            if path.startswith('/api/v1/manage/decks/'):
                deck_id = path.rsplit('/', 1)[-1]
                DECK_PUBLISHER.delete(deck_id, token)
            elif path.startswith('/api/v1/manage/personas/'):
                persona_id = path.rsplit('/', 1)[-1]
                refs = persona_used_by_decks(persona_id)
                if refs:
                    raise DivinationError('這位解讀師仍被牌組使用：' + ', '.join(refs[:5]))
                PERSONA_PUBLISHER.delete(persona_id, token)
                DIVINATION_ENGINE.personas.unregister(persona_id)
            else:
                self.send_error(404); return
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(json.dumps({'deleted': True}, ensure_ascii=False).encode('utf-8'))
        except DivinationError as e:
            self.send_response(403)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'error':'management_denied','message':str(e)}, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/v1/sources/threads':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0 or content_length > 16 * 1024:
                self.send_error(413); return
            try:
                payload = json.loads(self.rfile.read(content_length).decode('utf-8') or '{}')
                source_url = str(payload.get('url') or '').strip()
                source_url = canonicalize_threads_source_url(source_url)
                request = urllib.request.Request(
                    THREADS_READER_URL.rstrip('/') + '/v1/threads/resolve',
                    data=json.dumps({'url': source_url}).encode('utf-8'),
                    headers={'Content-Type':'application/json'}, method='POST'
                )
                with urllib.request.urlopen(request, timeout=52) as response:
                    body = json.loads(response.read(256 * 1024).decode('utf-8'))
                source = body.get('source') or {}
                if source.get('type') != 'threads' or not source.get('text') or not source.get('url'):
                    raise ValueError('threads_source_invalid')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(json.dumps({'source': source}, ensure_ascii=False).encode('utf-8'))
            except ValueError as exc:
                self.send_response(400); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(json.dumps({'error':str(exc)}, ensure_ascii=False).encode('utf-8'))
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                log(f'Threads source unavailable: {type(exc).__name__}')
                self.send_response(502); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(json.dumps({'error':'threads_source_unavailable'}).encode('utf-8'))
            return
        share_image_match = re.fullmatch(r'/api/v1/readings/([^/]+)/share-image', path)
        if share_image_match:
            reading_id = share_image_match.group(1)
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0 or content_length > 4 * 1024 * 1024:
                self.send_error(413); return
            try:
                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))
                SESSION_STORE.get(reading_id, str(payload.get('session_token') or ''))
                image = str(payload.get('image') or '')
                match = re.fullmatch(r'data:image/png;base64,([A-Za-z0-9+/=\s]+)', image)
                if not match:
                    raise DivinationError('invalid share image')
                raw = base64.b64decode(match.group(1), validate=False)
                if not raw.startswith(b'\x89PNG\r\n\x1a\n') or len(raw) > 3 * 1024 * 1024:
                    raise DivinationError('invalid share image')
                share_dir = os.path.join(DATA_DIR, 'share_images')
                os.makedirs(share_dir, exist_ok=True)
                tmp = os.path.join(share_dir, f'.{reading_id}.tmp')
                final = os.path.join(share_dir, f'{reading_id}.png')
                with open(tmp, 'wb') as f:
                    f.write(raw)
                os.replace(tmp, final)
                self.send_response(201)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(json.dumps({'stored': True, 'reading_id': reading_id}).encode('utf-8'))
            except (DivinationError, ValueError, TypeError):
                self.send_response(403)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'share_image_denied'}).encode('utf-8'))
            return
        if path.startswith('/api/v1/manage/decks/') and path.endswith('/rotate'):
            deck_id = path.split('/')[-2]
            try:
                token = DECK_PUBLISHER.rotate_management_token(deck_id, self.headers.get('X-Management-Token', ''))
                data = {'management_token': token, 'manage_path': f'/manage.html?deck={deck_id}'}
                self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            except DivinationError as e:
                self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(json.dumps({'error':'management_denied','message':str(e)}, ensure_ascii=False).encode('utf-8'))
            return
        if path.startswith('/api/v1/manage/personas/') and path.endswith('/rotate'):
            persona_id = path.split('/')[-2]
            try:
                token = PERSONA_PUBLISHER.rotate_management_token(persona_id, self.headers.get('X-Management-Token', ''))
                data = {'management_token': token, 'manage_path': f'/manage.html?persona={persona_id}'}
                self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            except DivinationError as e:
                self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(json.dumps({'error':'management_denied','message':str(e)}, ensure_ascii=False).encode('utf-8'))
            return
        if self.path == '/api/v1/personas':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 64 * 1024:
                self.send_response(413)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'persona_too_large','message':'解牌師設定內容過大'}, ensure_ascii=False).encode('utf-8'))
                return
            try:
                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))
                result = PERSONA_PUBLISHER.publish(payload)
                persona = ConfigurablePersona(PERSONA_PUBLISHER.pack_path(result['persona_id']))
                DIVINATION_ENGINE.personas.register(persona)
                self.send_response(201)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            except DivinationError as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'invalid_persona','message':str(e)}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                log(f"!!! PERSONA PUBLISH ERROR: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'persona_publish_failed'}, ensure_ascii=False).encode('utf-8'))
            return
        if self.path == '/api/v1/themes':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 20 * 1024 * 1024:
                self.send_response(413)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'theme_too_large','message':'主題圖片總量過大'}, ensure_ascii=False).encode('utf-8'))
                return
            try:
                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))
                result = THEME_PUBLISHER.publish(payload)
                self.send_response(201)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            except AIUnavailable as e:
                self.send_response(503 if e.retryable else 503)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'ai_unavailable', 'code': e.code, 'message': str(e), 'retryable': e.retryable, 'reading_id': locals().get('reading_id'), 'session_token': locals().get('issued_token')}, ensure_ascii=False).encode('utf-8'))
            except DivinationError as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'invalid_theme','message':str(e)}, ensure_ascii=False).encode('utf-8'))
            return
        if self.path == '/api/v1/readings':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                req_data = json.loads(post_data.decode('utf-8'))
                question = str(req_data.get('question') or '').strip()
                lang = str(req_data.get('lang') or 'zh-TW')
                history = req_data.get('history') or []
                reading_id = str(req_data.get('readingId') or '')
                session_token = str(req_data.get('sessionToken') or '')
                client_request_id = str(req_data.get('clientRequestId') or '').strip()
                request_registered = False
                if client_request_id and not re.fullmatch(r'[A-Za-z0-9_-]{16,96}', client_request_id):
                    raise DivinationError('invalid client request id')
                if not reading_id and client_request_id:
                    if not begin_reading_request(client_request_id):
                        self.send_response(409)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.send_header('Cache-Control', 'no-store')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error':'reading_in_progress','code':'reading_in_progress','retryable':True}, ensure_ascii=False).encode('utf-8'))
                        return
                    request_registered = True

                if reading_id and session_token:
                    saved = SESSION_STORE.get(reading_id, session_token)
                    persona_id = saved['persona']
                    method_id = saved['method']
                    method_result = saved['method_result']
                    persona = DIVINATION_ENGINE.personas.get(persona_id)
                    master_prompt = persona.build_prompt(method_result=method_result, question=question, lang=lang)
                    expires_at = saved['expires_at']
                    issued_token = session_token
                    issued_share_token = None
                    seed_fingerprint = None
                else:
                    input_data = req_data.get('input') or {}
                    deck_id = str(input_data.get('deck_id') or 'leopardcat')
                    method_requested = str(req_data.get('method') or 'tarot')
                    requested_persona = str(req_data.get('persona') or '').strip()
                    persona_id = requested_persona or (DIVINATION_ENGINE.decks.get(deck_id).default_persona if method_requested == 'tarot' else 'master')
                    request = ReadingRequest(
                        method=method_requested,
                        persona=persona_id,
                        question=question,
                        input=input_data,
                        lang=lang,
                        seed=req_data.get('seed'),
                    )
                    envelope = DIVINATION_ENGINE.prepare(request)
                    reading_id = envelope.reading_id
                    method_id = envelope.method
                    method_result = envelope.method_result
                    seed_fingerprint = envelope.seed_fingerprint
                    master_prompt = envelope.master_prompt
                    deck_id = ((method_result.get('deck') or {}).get('deck_id'))
                    issued = SESSION_STORE.create(
                        reading_id=reading_id, method=method_id, persona=persona_id,
                        deck_id=deck_id, method_result=method_result,
                    )
                    issued_token = issued['session_token']
                    issued_share_token = issued['share_token']
                    expires_at = issued['expires_at']

                if history:
                    master_prompt += "\n\nConversation history supplied by the client for continuity only. It is not persisted by this service and must never change the immutable divination result:\n" + json.dumps(history[-10:], ensure_ascii=False)
                update_stats(divination=True)
                capsule = build_capsule(
                    reading_id=reading_id, method=method_id, persona=persona_id,
                    question=question, lang=lang, method_result=method_result,
                )
                handoff = public_handoff(capsule)
                try:
                    reading = call_master_prompt(master_prompt)
                except AIUnavailable as e:
                    log('MASTER_PROVIDER_TRACE ' + json.dumps(AI_GATEWAY.last_trace(), ensure_ascii=False, separators=(',', ':')))
                    response_body = {
                        'error': 'ai_unavailable', 'code': e.code, 'message': str(e), 'retryable': e.retryable,
                        'reading_id': reading_id, 'session_token': issued_token, 'share_token': issued_share_token, 'expires_at': expires_at,
                        'privacy': {'question_stored': False, 'answer_stored': False, 'symbolic_state_ttl_hours': 24},
                        'method': method_id, 'persona': persona_id, 'question': question, 'lang': lang,
                        'seed_fingerprint': seed_fingerprint, 'method_result': method_result,
                        'reading': None, 'capsule': capsule, 'handoff': handoff,
                    }
                    self.send_response(503)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode('utf-8'))
                    return
                response_body = {
                    'reading_id': reading_id,
                    'session_token': issued_token,
                    'share_token': issued_share_token,
                    'expires_at': expires_at,
                    'privacy': {'question_stored': False, 'answer_stored': False, 'symbolic_state_ttl_hours': 24},
                    'method': method_id,
                    'persona': persona_id,
                    'question': question,
                    'lang': lang,
                    'seed_fingerprint': seed_fingerprint,
                    'method_result': method_result,
                    'reading': reading,
                    'capsule': capsule,
                    'handoff': handoff,
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode('utf-8'))
            except DivinationError as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'invalid_request', 'message': str(e)}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                log(f"!!! MODULAR DIVINATION ERROR: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'reading_failed'}, ensure_ascii=False).encode('utf-8'))
            finally:
                if locals().get('request_registered'):
                    end_reading_request(locals().get('client_request_id'))
            return

        if self.path == '/api/v1/decks':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 160 * 1024 * 1024:
                self.send_error(413)
                return
            try:
                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))
                persona_id = str(payload.get('persona') or 'master').strip()
                DIVINATION_ENGINE.personas.get(persona_id)
                theme_id = str(payload.get('theme') or 'minimal-light').strip()
                THEMES.get(theme_id)
                payload['theme'] = theme_id
                result = DECK_PUBLISHER.publish(payload)
                self.send_response(201)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            except DivinationError as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error':'invalid_deck','message':str(e)}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                log(f"!!! DECK PUBLISH ERROR: {e}")
                self.send_response(500)
                self.end_headers()
            return
        if self.path == '/api/fortune':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                req_data = json.loads(post_data.decode('utf-8'))
                question = req_data.get('question', '')
                card_title = req_data.get('cardTitle', 'TBD')
                card_meaning = req_data.get('cardMeaning', '')
                lang = req_data.get('lang', 'zh')
                history = req_data.get('history', [])

                # 📈 Immediate Stats Update (Count the attempt)
                update_stats(divination=True)

                # 🛠️ Spirit Simulator (Debug Mode)
                if question.upper() == 'DEBUG' or question.upper() == 'FORCE_DEBUG':
                    log(f"🛠️ Debug Mode Active: Bypassing Gemini API for {card_title}")
                    mock_reading = f"（靈力模擬中）這是一則來自淺山的測試訊息。您抽到了「{card_title}」，靈貓正守護著您的分享測試。 <div class='hidden-quote' style='display:none'>靈貓守護，測試順利。</div>"
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"reading": mock_reading}).encode('utf-8'))
                    return

                log(f"Fortune Request: Q='{question}', Card='{card_title}', Lang='{lang}'")

                contents = []
                for h in history:
                    role = "user" if h['role'] == 'user' else "model"
                    contents.append({"role": role, "parts": [{"text": h['content']}]})
                
                system_lang = "Traditional Chinese (Taiwan)" if lang == 'zh' else "English"
                system_prompt = f"You are the 'Hill Spirit Master' of a Leopard Cat Tarot deck, a wise guardian of the shallow mountains. Connect the leopard cat's survival journey to the seeker's life. "
                
                if lang == 'zh':
                    system_prompt += (
                        "你的口吻神祕、優雅且富有禪意。在解牌時，必須將石虎的現實生存困境（如棲地破碎化、路殺、犬隻攻擊、非法獵捕）與牌義結合，"
                        "引導求問者在解決自身生命難題的同時，也能感同身受淺山靈魂的艱辛。絕對禁止使用簡體中文，必須使用台灣繁體中文，且禁用中國大陸用語。"
                        "\n\n**語言規範**：請優先以求問者的提問語言回覆，展現你通曉萬物靈魂的智慧。若無法判斷語言，則預設以「台灣繁體中文」回答。"
                    )
                else:
                    system_prompt += (
                        "Your tone is mystical, elegant, and Zen-like. When reading, weave specific Leopard Cat conservation challenges "
                        "(e.g., habitat fragmentation, roadkill, stray dog attacks, illegal trapping) into the interpretation. "
                        "\n\n**LANGUAGE POLICY**: You MUST respond in the seeker's language to ensure a deep soul connection. If the seeker's language is unclear or if they are just using symbols, default to English. "
                        "\n\n**CRITICAL**: At the end of EVERY response, you MUST provide a short, profound 'Golden Quote' (max 20 words) that summarizes the core blessing or insight. "
                        "Wrap it EXACTLY like this: <div class='hidden-quote' style='display:none'>[Your Quote Here]</div>"
                    )

                system_prompt += f"\n\nThe seeker drew: {card_title} ({card_meaning})."
                
                if not contents:
                    contents.append({"role": "user", "parts": [{"text": f"{system_prompt}\n\nQuestion: {question}"}]})
                else:
                    contents.append({"role": "user", "parts": [{"text": question}]})

                payload = {"contents": contents}
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
                req = urllib.request.Request(gemini_url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                
                # ⚠️ timeout=30 必須設定：防止 Gemini API 掛掉時 server hang 死
                with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    reading = res_data['candidates'][0]['content']['parts'][0]['text']
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"reading": reading}).encode('utf-8'))
            except Exception as e:
                log(f"!!! FORTUNE ERROR: {e}")
                self.send_response(500)
                self.end_headers()
        elif self.path == '/api/cookies':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                req_data = json.loads(post_data.decode('utf-8'))
                req_token = req_data.get('token')
                cookies_content = req_data.get('cookies')
                
                # Load expected token
                expected_token = None
                env_path = "/home/ubuntu/agentmanager/.env"
                if os.path.exists(env_path):
                    with open(env_path) as f:
                        for line in f:
                            if line.startswith("COOKIE_SYNC_TOKEN="):
                                expected_token = line.strip().split("=", 1)[1].strip()
                                break
                
                if not expected_token or req_token != expected_token:
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Forbidden: Invalid Token"}).encode('utf-8'))
                    return
                
                cookies_path = "/home/ubuntu/youtube-ai-manager/cookies.txt"
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    f.write(cookies_content)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Cookies synced successfully"}).encode('utf-8'))
                log("✅ [HTTP 8088] Cookies synced successfully via Web Server")
            except Exception as e:
                log(f"❌ [HTTP 8088] Error syncing cookies: {e}")
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        else:
            self.send_error(404)

socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("", PORT), MyHttpRequestHandler) as httpd:
    log(f"LCS v45 Server running on {PORT}")
    httpd.serve_forever()
