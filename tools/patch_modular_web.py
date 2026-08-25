from pathlib import Path


def patch_server():
    p = Path('website/fortune_server.py')
    s = p.read_text(encoding='utf-8')
    if 'build_default_engine' not in s:
        s = s.replace('import re\n', 'import re\n\nfrom divination import ReadingRequest, build_default_engine\nfrom divination.core import DivinationError\n')
    if 'DIVINATION_ENGINE = build_default_engine' not in s:
        anchor = 'ctx.verify_mode = ssl.CERT_NONE\n'
        insert = '''ctx.verify_mode = ssl.CERT_NONE\n\nDIVINATION_ENGINE = build_default_engine(os.path.dirname(os.path.abspath(__file__)))\n\ndef call_master_prompt(prompt):\n    if not API_KEY:\n        raise RuntimeError("GEMINI_API_KEY is not configured")\n    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}\n    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"\n    req = urllib.request.Request(gemini_url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})\n    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:\n        data = json.loads(response.read().decode("utf-8"))\n    return data["candidates"][0]["content"]["parts"][0]["text"]\n'''
        if anchor not in s:
            raise RuntimeError('server SSL anchor missing')
        s = s.replace(anchor, insert)
    if "self.path == '/api/v1/readings'" not in s:
        old = "    def do_POST(self):\n        if self.path == '/api/fortune':"
        new = '''    def do_POST(self):\n        if self.path == '/api/v1/readings':\n            content_length = int(self.headers.get('Content-Length', 0))\n            post_data = self.rfile.read(content_length)\n            try:\n                req_data = json.loads(post_data.decode('utf-8'))\n                question = str(req_data.get('question') or '').strip()\n                lang = str(req_data.get('lang') or 'zh-TW')\n                persona_id = str(req_data.get('persona') or 'leopardcat')\n                history = req_data.get('history') or []\n                supplied_result = req_data.get('methodResult')\n                if supplied_result:\n                    persona = DIVINATION_ENGINE.personas.get(persona_id)\n                    master_prompt = persona.build_prompt(method_result=supplied_result, question=question, lang=lang)\n                    reading_id = str(req_data.get('readingId') or '')\n                    method_id = str(req_data.get('method') or supplied_result.get('method') or 'tarot')\n                    method_result = supplied_result\n                    seed_fingerprint = None\n                else:\n                    request = ReadingRequest(\n                        method=str(req_data.get('method') or 'tarot'),\n                        persona=persona_id,\n                        question=question,\n                        input=req_data.get('input') or {},\n                        lang=lang,\n                        seed=req_data.get('seed'),\n                    )\n                    envelope = DIVINATION_ENGINE.prepare(request)\n                    reading_id = envelope.reading_id\n                    method_id = envelope.method\n                    method_result = envelope.method_result\n                    seed_fingerprint = envelope.seed_fingerprint\n                    master_prompt = envelope.master_prompt\n                if history:\n                    master_prompt += "\\n\\nConversation history for continuity only; never change the immutable divination result:\\n" + json.dumps(history[-10:], ensure_ascii=False)\n                update_stats(divination=True)\n                reading = call_master_prompt(master_prompt)\n                response_body = {\n                    'reading_id': reading_id,\n                    'method': method_id,\n                    'persona': persona_id,\n                    'question': question,\n                    'lang': lang,\n                    'seed_fingerprint': seed_fingerprint,\n                    'method_result': method_result,\n                    'reading': reading,\n                }\n                self.send_response(200)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Access-Control-Allow-Origin', '*')\n                self.end_headers()\n                self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode('utf-8'))\n            except DivinationError as e:\n                self.send_response(400)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Access-Control-Allow-Origin', '*')\n                self.end_headers()\n                self.wfile.write(json.dumps({'error': 'invalid_request', 'message': str(e)}, ensure_ascii=False).encode('utf-8'))\n            except Exception as e:\n                log(f"!!! MODULAR DIVINATION ERROR: {e}")\n                self.send_response(500)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Access-Control-Allow-Origin', '*')\n                self.end_headers()\n                self.wfile.write(json.dumps({'error': 'reading_failed'}, ensure_ascii=False).encode('utf-8'))\n            return\n        if self.path == '/api/fortune':'''
        if old not in s:
            raise RuntimeError('server POST anchor missing')
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')


def patch_main():
    p = Path('website/main.js')
    m = p.read_text(encoding='utf-8')
    if 'window.currentReadingEnvelope = null;' not in m[:3000]:
        m = m.replace('window.currentDrawnCard = null;\n', 'window.currentDrawnCard = null;\nwindow.currentReadingEnvelope = null;\n')
    start = m.index('window.drawFortune = async function() {')
    end = m.index('window.getAIReading = async function(q, card) {', start)
    if 'window.getModularReading = async function(q)' not in m[start:end]:
        replacement = r'''window.drawFortune = async function() {
    const common = window.siteData[window.currentLang].common;
    if (chatQuota <= 0) return alert(common.err_mana_depleted);
    const q = document.getElementById('fortune-question').value;
    if (!q.trim()) return alert(common.err_empty_question);
    if (q.toUpperCase() !== 'DEBUG' && q.toUpperCase() !== 'FORCE_DEBUG') {
        if (chatQuota === 5) {
            lastManaRegen = Date.now();
            localStorage.setItem('lastManaRegen', lastManaRegen);
        }
        chatQuota--;
        updateUIQuota();
    }
    document.getElementById('fortune-ritual-area').classList.add('hidden');
    document.getElementById('fortune-chat-area').classList.remove('hidden');
    appendBubble('user', q);
    try {
        await window.getModularReading(q);
    } catch (e) {
        console.warn('[Divination v1] Falling back to legacy fortune API:', e);
        const card = window.cardData[Math.floor(Math.random() * window.cardData.length)];
        currentDrawnCard = card;
        window.currentDrawnCard = card;
        window.currentReadingEnvelope = null;
        await window.getAIReading(q, card);
    }
};

window.getModularReading = async function(q) {
    const common = window.siteData[window.currentLang].common;
    const historyDiv = document.getElementById('chat-history');
    const sensingId = 'sensing-' + Date.now();
    appendBubble('assistant', `<div id="${sensingId}" class="spirit-thinking">${common.msg_sensing}</div>`);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    let resp;
    try {
        resp = await fetch('/api/v1/readings', {
            method: 'POST', signal: controller.signal,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'tarot', persona: 'leopardcat', question: q,
                input: { spread: 'auto' },
                lang: window.currentLang === 'zh' ? 'zh-TW' : 'en'
            })
        });
    } finally { clearTimeout(timeoutId); }
    if (!resp.ok) throw new Error(`DIVINATION_V1_${resp.status}`);
    const data = await resp.json();
    document.getElementById(sensingId)?.closest('.chat-bubble')?.remove();
    const specs = data.method_result?.cards || [];
    if (!specs.length) throw new Error('DIVINATION_V1_EMPTY_RESULT');
    const resolved = specs.map(spec => ({spec, card: window.cardData.find(c => c.id === spec.card_id)})).filter(x => x.card);
    if (!resolved.length) throw new Error('DIVINATION_V1_CARD_NOT_FOUND');
    currentDrawnCard = resolved[0].card;
    window.currentDrawnCard = currentDrawnCard;
    window.currentReadingEnvelope = data;
    window._lastQuestion = q;
    const pinnedArea = document.getElementById('pinned-card-area');
    const pinnedDisplay = document.getElementById('pinned-card-display');
    if (pinnedArea && pinnedDisplay) {
        pinnedArea.classList.remove('hidden');
        pinnedDisplay.innerHTML = `<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">${resolved.map(({spec, card}) => {
            const orientation = spec.orientation === 'reversed' ? (window.currentLang === 'zh' ? '逆位' : 'Reversed') : (window.currentLang === 'zh' ? '正位' : 'Upright');
            const pos = spec.position_label || spec.position || '';
            const title = card.title[window.currentLang];
            const rotate = spec.orientation === 'reversed' ? 'transform:rotate(180deg);' : '';
            return `<div class="pinned-card-content" style="max-width:150px;"><img src="art/renders/${card.id}.webp" class="pinned-card-img" style="${rotate}"><div class="pinned-card-title">【${title}】<br><small>${pos} · ${orientation}</small></div></div>`;
        }).join('')}</div>`;
    }
    const spreadNames = {
        single: window.currentLang === 'zh' ? '單牌指引' : 'Single Guidance',
        three_card: window.currentLang === 'zh' ? '三牌時間流' : 'Three-card Timeline',
        decision: window.currentLang === 'zh' ? '抉擇三牌' : 'Decision Spread'
    };
    const spread = data.method_result?.spread || 'single';
    const summary = resolved.map(({spec, card}) => {
        const orientation = spec.orientation === 'reversed' ? (window.currentLang === 'zh' ? '逆位' : 'Reversed') : (window.currentLang === 'zh' ? '正位' : 'Upright');
        return `${spec.position_label || spec.position}: ${card.title[window.currentLang]}（${orientation}）`;
    }).join(' / ');
    const prefix = `${window.currentLang === 'zh' ? '大師展開' : 'The Master opens'} <strong>【${spreadNames[spread] || spread}】</strong><br><small>${summary}</small><br>`;
    const bubble = appendBubble('assistant', prefix);
    const textContainer = document.createElement('div');
    textContainer.className = 'markdown-content';
    bubble.appendChild(textContainer);
    const rawReply = data.reading || '';
    const htmlReply = typeof marked !== 'undefined' ? marked.parse(rawReply) : rawReply.replace(/\n/g, '<br>');
    typeWriterHTML(textContainer, htmlReply, 35, () => {
        currentChatHistory.push({role:'user', content:q}, {role:'assistant', content:rawReply});
        updateTempleStats();
        const actions = document.getElementById('fortune-actions');
        actions.classList.remove('hidden');
        setTimeout(() => actions.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300);
    });
    historyDiv.scrollTop = historyDiv.scrollHeight;
};

'''
        m = m[:start] + replacement + m[end:]
    old_fetch = """        const apiResp = await fetch('/api/fortune', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text, cardTitle: currentDrawnCard.title[window.currentLang], cardMeaning: currentDrawnCard.meaning[window.currentLang], lang: window.currentLang, history: currentChatHistory })
        });"""
    if old_fetch in m:
        new_fetch = """        const modular = window.currentReadingEnvelope;
        const apiResp = await fetch(modular ? '/api/v1/readings' : '/api/fortune', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: modular ? JSON.stringify({
                method: modular.method || 'tarot', persona: modular.persona || 'leopardcat',
                readingId: modular.reading_id, question: text,
                methodResult: modular.method_result,
                lang: window.currentLang === 'zh' ? 'zh-TW' : 'en', history: currentChatHistory
            }) : JSON.stringify({
                question: text, cardTitle: currentDrawnCard.title[window.currentLang],
                cardMeaning: currentDrawnCard.meaning[window.currentLang],
                lang: window.currentLang, history: currentChatHistory
            })
        });"""
        m = m.replace(old_fetch, new_fetch, 1)
    reset_pos = m.index('window.resetRitual = function() {')
    if 'window.currentReadingEnvelope = null;' not in m[reset_pos:reset_pos+300]:
        m = m.replace('window.resetRitual = function() {\n    currentChatHistory = [];', 'window.resetRitual = function() {\n    currentChatHistory = [];\n    window.currentReadingEnvelope = null;')
    p.write_text(m, encoding='utf-8')


if __name__ == '__main__':
    patch_server()
    patch_main()
    print('modular_web_patch=applied')
