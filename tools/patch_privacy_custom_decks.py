from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
server_path = ROOT / 'website' / 'fortune_server.py'
main_path = ROOT / 'website' / 'main.js'

server = server_path.read_text(encoding='utf-8')
main = main_path.read_text(encoding='utf-8')

# --- fortune_server imports / globals ---
anchor = "from divination.core import DivinationError\n"
insert = "from divination.core import DivinationError\nfrom divination.sessions import ReadingSessionStore\nfrom divination.publishing import DeckPublisher\n"
if 'ReadingSessionStore' not in server:
    server = server.replace(anchor, insert)

anchor = "DIVINATION_ENGINE = build_default_engine(os.path.dirname(os.path.abspath(__file__)))\n"
insert = "DIVINATION_ENGINE = build_default_engine(os.path.dirname(os.path.abspath(__file__)))\nDATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')\nSESSION_STORE = ReadingSessionStore(os.path.join(DATA_DIR, 'reading_sessions.sqlite3'), ttl_seconds=86400)\nDECK_PUBLISHER = DeckPublisher(os.path.join(DATA_DIR, 'custom_decks'))\n"
if 'SESSION_STORE = ReadingSessionStore' not in server:
    server = server.replace(anchor, insert)

# --- GET routes for public custom deck metadata/images ---
anchor = "        # 👑 API Endpoints\n        if path == '/api/stats':\n"
insert = "        # 👑 API Endpoints\n        if path.startswith('/api/v1/decks/'):\n            parts = [p for p in path.split('/') if p]\n            try:\n                if len(parts) == 4:\n                    deck_id = parts[3]\n                    info = DIVINATION_ENGINE.decks.public_info(deck_id)\n                    self.send_response(200)\n                    self.send_header('Content-type', 'application/json; charset=utf-8')\n                    self.send_header('Cache-Control', 'public, max-age=60')\n                    self.end_headers()\n                    self.wfile.write(json.dumps(info, ensure_ascii=False).encode('utf-8'))\n                    return\n                if len(parts) == 6 and parts[4] == 'images':\n                    deck_id, filename = parts[3], parts[5]\n                    image_path = DECK_PUBLISHER.image_path(deck_id, filename)\n                    ext = image_path.suffix.lower()\n                    mime = {'.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp'}[ext]\n                    raw = image_path.read_bytes()\n                    self.send_response(200)\n                    self.send_header('Content-type', mime)\n                    self.send_header('Content-Length', str(len(raw)))\n                    self.send_header('Cache-Control', 'public, max-age=86400')\n                    self.end_headers()\n                    self.wfile.write(raw)\n                    return\n            except DivinationError:\n                self.send_error(404)\n                return\n        if path == '/api/stats':\n"
if "path.startswith('/api/v1/decks/')" not in server:
    server = server.replace(anchor, insert)

# --- replace v1 reading route with privacy-safe session logic ---
start = server.index("        if self.path == '/api/v1/readings':")
end = server.index("        if self.path == '/api/fortune':", start)
replacement = '''        if self.path == '/api/v1/readings':
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
                    master_prompt += "\\n\\nConversation history supplied by the client for continuity only. It is not persisted by this service and must never change the immutable divination result:\\n" + json.dumps(history[-10:], ensure_ascii=False)
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
'''
server = server[:start] + replacement + server[end:]

# --- main.js: select deck from URL, generic persona for custom decks ---
needle = "window.getModularReading = async function(q) {\n"
if 'window.activeDeckId' not in main:
    main = main.replace(needle, "window.activeDeckId = new URLSearchParams(window.location.search).get('deck') || 'leopardcat';\n\n" + needle)

main = main.replace(
    "method: 'tarot', persona: 'leopardcat', question: q,\n                input: { spread: 'auto' },",
    "method: 'tarot', persona: window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'master', question: q,\n                input: { spread: 'auto', deck_id: window.activeDeckId },"
)

main = main.replace(
    "const resolved = specs.map(spec => ({spec, card: window.cardData.find(c => c.id === spec.card_id)})).filter(x => x.card);",
    "const resolved = specs.map(spec => ({spec, card: window.cardData.find(c => c.id === spec.card_id) || spec})).filter(x => x.card);"
)

main = main.replace(
    "const title = card.title[window.currentLang];",
    "const title = card.title?.[window.currentLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id;"
)
main = main.replace(
    "return `<div class=\"pinned-card-content\" style=\"max-width:150px;\"><img src=\"art/renders/${card.id}.webp\" class=\"pinned-card-img\" style=\"${rotate}\"><div class=\"pinned-card-title\">【${title}】<br><small>${pos} · ${orientation}</small></div></div>`;",
    "const imageSrc = card.image || `art/renders/${card.id}.webp`; return `<div class=\"pinned-card-content\" style=\"max-width:150px;\"><img src=\"${imageSrc}\" class=\"pinned-card-img\" style=\"${rotate}\"><div class=\"pinned-card-title\">【${title}】<br><small>${pos} · ${orientation}</small></div></div>`;"
)
main = main.replace(
    "return `${spec.position_label || spec.position}: ${card.title[window.currentLang]}（${orientation}）`;",
    "const title = card.title?.[window.currentLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id; return `${spec.position_label || spec.position}: ${title}（${orientation}）`;"
)

old_follow = "method: modular.method || 'tarot', persona: modular.persona || 'leopardcat',\n                readingId: modular.reading_id, question: text,\n                methodResult: modular.method_result,\n                lang: window.currentLang === 'zh' ? 'zh-TW' : 'en', history: currentChatHistory"
new_follow = "method: modular.method || 'tarot', persona: modular.persona || 'leopardcat',\n                readingId: modular.reading_id, sessionToken: modular.session_token, question: text,\n                lang: window.currentLang === 'zh' ? 'zh-TW' : 'en', history: currentChatHistory"
main = main.replace(old_follow, new_follow)

# custom deck fallback must not silently switch to LeopardCat deck
main = main.replace(
    "console.warn('[Divination v1] Falling back to legacy fortune API:', e);\n        const card = window.cardData[Math.floor(Math.random() * window.cardData.length)];",
    "console.warn('[Divination v1] Falling back to legacy fortune API:', e);\n        if (window.activeDeckId !== 'leopardcat') { alert('這副自訂牌暫時無法連線，請稍後再試。'); return; }\n        const card = window.cardData[Math.floor(Math.random() * window.cardData.length)];"
)

server_path.write_text(server, encoding='utf-8')
main_path.write_text(main, encoding='utf-8')
print('privacy_custom_decks_patch=applied')
