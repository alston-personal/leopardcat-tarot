from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


server = Path("website/fortune_server.py")
replace_once(
    server,
    "from divination.personas import persona_public_info\n",
    "from divination.personas import persona_public_info, ConfigurablePersona\nfrom divination.persona_publishing import PersonaPublisher\n",
)
replace_once(
    server,
    "THEME_PUBLISHER = ThemePublisher(THEME_ROOT)\n",
    "THEME_PUBLISHER = ThemePublisher(THEME_ROOT)\nPERSONA_ROOT = os.path.join(DATA_DIR, 'custom_personas')\nPERSONA_PUBLISHER = PersonaPublisher(PERSONA_ROOT)\n",
)
old_get = '''        if path == '/api/v1/personas':
            params = urllib.parse.parse_qs(query)
            deck_id = (params.get('deck') or ['leopardcat'])[0]
            try:
                deck = DIVINATION_ENGINE.decks.get(deck_id)
                default_persona = deck.default_persona
                items = [persona_public_info(DIVINATION_ENGINE.personas.get(pid)) for pid in DIVINATION_ENGINE.personas.capabilities()]
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'public, max-age=60')
                self.end_headers()
                self.wfile.write(json.dumps({'default_persona': default_persona, 'personas': items}, ensure_ascii=False).encode('utf-8'))
            except DivinationError:
                self.send_error(404)
            return
'''
new_get = '''        if path == '/api/v1/personas':
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
'''
replace_once(server, old_get, new_get)

post_anchor = "    def do_POST(self):\n        if self.path == '/api/v1/themes':\n"
post_block = '''    def do_POST(self):
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
'''
replace_once(server, post_anchor, post_block)

replace_once(
    server,
    "                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))\n                result = DECK_PUBLISHER.publish(payload)\n",
    "                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))\n                persona_id = str(payload.get('persona') or 'master').strip()\n                DIVINATION_ENGINE.personas.get(persona_id)\n                result = DECK_PUBLISHER.publish(payload)\n",
)

html = Path("website/public/create.html")
html_anchor = '''    <p id="persona-status" class="muted" aria-live="polite"></p>
  </section>
'''
html_new = '''    <p id="persona-status" class="muted" aria-live="polite"></p>
    <details id="custom-persona-builder" style="margin-top:16px;border-top:1px solid #eee3d4;padding-top:14px">
      <summary style="cursor:pointer"><strong>＋ 建立我的解牌師</strong> <span class="muted">（選填）</span></summary>
      <p class="muted">不用寫提示詞。用自己的話描述這位解牌師，系統會組成安全的 Persona Pack。</p>
      <div class="row">
        <div><label>解牌師名稱</label><input id="persona-name" placeholder="例如：月光園丁"></div>
        <div><label>一句角色介紹</label><input id="persona-role" placeholder="例如：溫柔但不逃避現實的夜間引路人"></div>
      </div>
      <label>說話風格</label>
      <textarea id="persona-voice" placeholder="每行一個特色，例如：\n溫柔、簡潔\n先同理，再指出盲點\n避免命令式語氣"></textarea>
      <label>解讀原則</label>
      <textarea id="persona-principles" placeholder="每行一條，例如：\n先讀牌面，再連回提問\n同時說明機會與風險\n最後給一個今天能做的行動"></textarea>
      <label>世界觀／專長（選填）</label>
      <textarea id="persona-worldview" placeholder="例如：熟悉植物、季節循環與園藝隱喻"></textarea>
      <label>每次回答怎麼收尾？（選填）</label>
      <input id="persona-closing" placeholder="例如：最後留下一句短短的月光提醒">
      <p class="muted">抽牌結果、安全規則與隱私規則由平台固定保護，你的設定不會覆蓋它們。</p>
      <button id="create-persona" type="button" class="btn secondary">建立這位解牌師</button>
      <p id="persona-create-status" class="muted" aria-live="polite"></p>
    </details>
  </section>
'''
replace_once(html, html_anchor, html_new)

js = Path("website/public/creator.js")
replace_once(
    js,
    "  const personaStatus = document.getElementById('persona-status');\n",
    "  const personaStatus = document.getElementById('persona-status');\n  const personaCreateBtn = document.getElementById('create-persona');\n  const personaCreateStatus = document.getElementById('persona-create-status');\n",
)
js_anchor = "  const optimizeImage = (file) => new Promise((resolve, reject) => {\n"
js_block = '''  async function createCustomPersona() {
    const name = document.getElementById('persona-name').value.trim();
    const role = document.getElementById('persona-role').value.trim();
    const voice = document.getElementById('persona-voice').value.trim();
    const principles = document.getElementById('persona-principles').value.trim();
    if (!name) return alert('先幫你的解牌師取一個名字。');
    if (!role) return alert('請用一句話介紹這位解牌師。');
    if (!voice) return alert('請描述至少一種說話風格。');
    if (!principles) return alert('請填至少一條解讀原則。');

    personaCreateBtn.disabled = true;
    personaCreateStatus.textContent = '正在建立你的解牌師…';
    try {
      const resp = await fetch('/api/v1/personas', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          name, role, voice, principles,
          worldview: document.getElementById('persona-worldview').value.trim(),
          closing: document.getElementById('persona-closing').value.trim()
        })
      });
      const data = await readApiResponse(resp);
      if (!resp.ok) throw new Error(data.message || '建立解牌師失敗');
      personas = personas.filter(x => x.persona_id !== data.persona_id);
      personas.push(data);
      selectedPersonaId = data.persona_id;
      renderPersonaOptions();
      personaCreateStatus.textContent = `✓ 已建立「${data.name}」，並設為這副牌的預設解牌師。`;
    } catch (e) {
      personaCreateStatus.textContent = e.message || '建立解牌師失敗，請稍後再試。';
    } finally {
      personaCreateBtn.disabled = false;
    }
  }

  if (personaCreateBtn) personaCreateBtn.addEventListener('click', createCustomPersona);

  const optimizeImage = (file) => new Promise((resolve, reject) => {
'''
replace_once(js, js_anchor, js_block)

for path, needles in {
    server: ["PersonaPublisher", "path.startswith('/api/v1/personas/')", "DIVINATION_ENGINE.personas.register(persona)", "DIVINATION_ENGINE.personas.get(persona_id)"],
    html: ["建立我的解牌師", "id=\"persona-name\"", "id=\"create-persona\""],
    js: ["createCustomPersona", "fetch('/api/v1/personas'", "selectedPersonaId = data.persona_id"],
}.items():
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"contract missing in {path}: {needle}")

print("persona_creator_runtime_patch=passed")
