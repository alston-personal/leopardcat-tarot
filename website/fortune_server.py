import http.server
import socketserver
import json
import urllib.request
import urllib.error
import os
import ssl
import traceback
import sys
import re

from divination import ReadingRequest, build_default_engine
from divination.core import DivinationError
from divination.sessions import ReadingSessionStore
from divination.publishing import DeckPublisher
from divination.themes import ThemeRegistry, ThemePublisher
from divination.ai_gateway import ZeroCostGeminiGateway, AIUnavailable

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

def load_env_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        env_path = "/home/ubuntu/agentmanager/.env"
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            key = line.strip().split("=", 1)[1]
                            break
            except Exception as e:
                log(f"Error reading .env: {e}")
    return key

API_KEY = load_env_key()
AI_GATEWAY = ZeroCostGeminiGateway(API_KEY)

DIVINATION_ENGINE = build_default_engine(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
SESSION_STORE = ReadingSessionStore(os.path.join(DATA_DIR, 'reading_sessions.sqlite3'), ttl_seconds=86400)
DECK_PUBLISHER = DeckPublisher(os.path.join(DATA_DIR, 'custom_decks'))
THEME_ROOT = os.path.join(DATA_DIR, 'custom_themes')
THEMES = ThemeRegistry(THEME_ROOT)
THEME_PUBLISHER = ThemePublisher(THEME_ROOT)

def call_master_prompt(prompt):
    return AI_GATEWAY.generate(prompt)

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        url_parts = self.path.split('?', 1)
        path = url_parts[0]
        query = url_parts[1] if len(url_parts) > 1 else ""

        # 👑 API Endpoints
        if path == '/api/v1/ai-policy':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(AI_GATEWAY.policy(), ensure_ascii=False).encode('utf-8'))
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
            card_id = None
            if 'card=' in query:
                match = re.search(r'card=([^&]+)', query)
                if match:
                    card_id = match.group(1)
            
            index_path = os.path.join(DIRECTORY, 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 🌿 Construction of Metadata
                host = 'leopardcat-tarot.milkcat.org'
                base_url = f"https://{host}"
                # 🖼️ Default Fallback Image (PNG for best FB stability)
                meta_img = f"{base_url}/art/renders/card-00-the-fool.webp"
                meta_title = "靈山靈貓 · 石虎塔羅 LeopardCat Tarot"
                meta_desc = "連結淺山靈魂，傾聽大師開示。讓石虎為您指引生命的方向。"
                
                if card_id:
                    card = next((c for c in CARD_MANIFEST if c['id'] == card_id), None)
                    if card:
                        meta_title = f"我在石虎塔羅抽到了：{card['title']['zh']} | {card['title']['en']}"
                        meta_desc = f"{card['ecology']['zh'][:100]}..."
                        meta_img = f"{base_url}/{card['image']}?v=v44"

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
    <meta property="og:image" content="https://leopardcat-tarot.milkcat.org/spirit-vision/{os.path.splitext(os.path.basename(meta_img))[0]}.webp?v=v999">
    <meta property="og:image:secure_url" content="https://leopardcat-tarot.milkcat.org/spirit-vision/{os.path.splitext(os.path.basename(meta_img))[0]}.webp?v=v999">
    <meta property="og:image:type" content="image/webp">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="1800">
    <meta property="og:image:alt" content="{meta_title}">
    <meta property="og:url" content="{base_url}{self.path}">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="https://leopardcat-tarot.milkcat.org/spirit-vision/{os.path.splitext(os.path.basename(meta_img))[0]}.webp?v=v999">"""
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

    def do_POST(self):
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

                if reading_id and session_token:
                    saved = SESSION_STORE.get(reading_id, session_token)
                    persona_id = saved['persona']
                    method_id = saved['method']
                    method_result = saved['method_result']
                    persona = DIVINATION_ENGINE.personas.get(persona_id)
                    master_prompt = persona.build_prompt(method_result=method_result, question=question, lang=lang)
                    expires_at = saved['expires_at']
                    issued_token = session_token
                    seed_fingerprint = None
                else:
                    persona_id = str(req_data.get('persona') or 'leopardcat')
                    request = ReadingRequest(
                        method=str(req_data.get('method') or 'tarot'),
                        persona=persona_id,
                        question=question,
                        input=req_data.get('input') or {},
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
                    expires_at = issued['expires_at']

                if history:
                    master_prompt += "\n\nConversation history supplied by the client for continuity only. It is not persisted by this service and must never change the immutable divination result:\n" + json.dumps(history[-10:], ensure_ascii=False)
                update_stats(divination=True)
                reading = call_master_prompt(master_prompt)
                response_body = {
                    'reading_id': reading_id,
                    'session_token': issued_token,
                    'expires_at': expires_at,
                    'privacy': {'question_stored': False, 'answer_stored': False, 'symbolic_state_ttl_hours': 24},
                    'method': method_id,
                    'persona': persona_id,
                    'question': question,
                    'lang': lang,
                    'seed_fingerprint': seed_fingerprint,
                    'method_result': method_result,
                    'reading': reading,
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
            return

        if self.path == '/api/v1/decks':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 160 * 1024 * 1024:
                self.send_error(413)
                return
            try:
                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))
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
