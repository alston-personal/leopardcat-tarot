from pathlib import Path

p = Path('website/fortune_server.py')
text = p.read_text(encoding='utf-8')


def replace_once(old: str, new: str) -> None:
    global text
    if new in text:
        return
    if old not in text:
        raise SystemExit(f'anchor not found: {old[:120]!r}')
    text = text.replace(old, new, 1)


replace_once(
    "from divination.persona_publishing import PersonaPublisher\n",
    "from divination.persona_publishing import PersonaPublisher\nfrom divination.capsules import build_capsule, public_handoff\nfrom divination.lenormand import public_method_info as lenormand_public_method_info\n",
)

replace_once(
    "def call_master_prompt(prompt):\n    return AI_GATEWAY.generate(prompt)\n",
    """def call_master_prompt(prompt):
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
""",
)

replace_once(
    "        # 👑 API Endpoints\n        if path == '/api/v1/ai-policy':\n",
    """        # 👑 API Endpoints
        if path == '/api/v1/methods':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'public, max-age=60')
            self.end_headers()
            self.wfile.write(json.dumps({'methods': method_catalog()}, ensure_ascii=False).encode('utf-8'))
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
""",
)

# Make method-specific default Persona explicit instead of treating every method as Tarot.
replace_once(
    """                    input_data = req_data.get('input') or {}
                    deck_id = str(input_data.get('deck_id') or 'leopardcat')
                    requested_persona = str(req_data.get('persona') or '').strip()
                    persona_id = requested_persona or DIVINATION_ENGINE.decks.get(deck_id).default_persona
                    request = ReadingRequest(
                        method=str(req_data.get('method') or 'tarot'),
""",
    """                    input_data = req_data.get('input') or {}
                    deck_id = str(input_data.get('deck_id') or 'leopardcat')
                    method_requested = str(req_data.get('method') or 'tarot')
                    requested_persona = str(req_data.get('persona') or '').strip()
                    persona_id = requested_persona or (DIVINATION_ENGINE.decks.get(deck_id).default_persona if method_requested == 'tarot' else 'master')
                    request = ReadingRequest(
                        method=method_requested,
""",
)

replace_once(
    """                update_stats(divination=True)
                reading = call_master_prompt(master_prompt)
                response_body = {
""",
    """                update_stats(divination=True)
                capsule = build_capsule(
                    reading_id=reading_id, method=method_id, persona=persona_id,
                    question=question, lang=lang, method_result=method_result,
                )
                handoff = public_handoff(capsule)
                try:
                    reading = call_master_prompt(master_prompt)
                except AIUnavailable as e:
                    response_body = {
                        'error': 'ai_unavailable', 'code': e.code, 'message': str(e), 'retryable': e.retryable,
                        'reading_id': reading_id, 'session_token': issued_token, 'expires_at': expires_at,
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
""",
)

replace_once(
    """                    'method_result': method_result,
                    'reading': reading,
                }
""",
    """                    'method_result': method_result,
                    'reading': reading,
                    'capsule': capsule,
                    'handoff': handoff,
                }
""",
)

# Management mutation methods are intentionally separate from public publishing routes.
anchor = "    def do_POST(self):\n"
management_methods = """    def do_PATCH(self):
        path = self.path.split('?', 1)[0]
        token = self.headers.get('X-Management-Token', '')
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 128 * 1024:
            self.send_error(413); return
        try:
            payload = json.loads(self.rfile.read(content_length).decode('utf-8') or '{}')
            if path.startswith('/api/v1/manage/decks/'):
                deck_id = path.rsplit('/', 1)[-1]
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
"""
if management_methods not in text:
    if anchor not in text:
        raise SystemExit('do_POST anchor missing')
    text = text.replace(anchor, management_methods, 1)

# self.path checks below remain valid for public routes because query strings are not used there.

p.write_text(text, encoding='utf-8')
print('divination_os_v1_server_patch=passed')
