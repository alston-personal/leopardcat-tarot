from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
web=ROOT/'website'
js_path=web/'main.js'
server_path=web/'fortune_server.py'
index_path=web/'index.html'
css_path=web/'style.css'
locales_path=web/'public/locales_v10.json'

js=js_path.read_text(encoding='utf-8')

needle="window.currentQuestionLanguage = null; // latest user/question language, independent from UI locale\n"
insert="""window.currentQuestionLanguage = null; // latest user/question language, independent from UI locale
window.readingRequestState = { inFlight: false, clientRequestId: null };

function newReadingClientRequestId() {
    if (crypto?.randomUUID) return crypto.randomUUID();
    return `${Date.now().toString(36)}-${freshShuffleSeed()}`;
}

function setPrimaryReadingBusy(busy) {
    const btn = document.getElementById('btn-primary-draw');
    const question = document.getElementById('fortune-question');
    const spread = document.getElementById('spread-select');
    const drawDetails = document.getElementById('draw-mode-details');
    if (btn) {
        btn.disabled = Boolean(busy);
        btn.setAttribute('aria-busy', busy ? 'true' : 'false');
        btn.classList.toggle('is-reading-pending', Boolean(busy));
        btn.textContent = busy ? uiText('reading_in_progress', '大師正在感應…') : uiText('btn_draw', '祈請大師開牌');
    }
    if (question) question.readOnly = Boolean(busy);
    if (spread) spread.disabled = Boolean(busy);
    if (drawDetails) drawDetails.classList.toggle('is-reading-pending', Boolean(busy));
}

function beginReadingRequest() {
    const state = window.readingRequestState;
    if (state.inFlight) return false;
    state.inFlight = true;
    state.clientRequestId = state.clientRequestId || newReadingClientRequestId();
    setPrimaryReadingBusy(true);
    return true;
}

function endReadingRequest({ preserveRequestId = false } = {}) {
    const state = window.readingRequestState;
    state.inFlight = false;
    if (!preserveRequestId) state.clientRequestId = null;
    setPrimaryReadingBusy(false);
}

function isStandaloneLaunch() {
    return window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

function cleanRefreshMarker() {
    const u = new URL(location.href);
    if (!u.searchParams.has('_lc_refresh')) return;
    u.searchParams.delete('_lc_refresh');
    history.replaceState(null, '', u);
}

window.forceAppRefresh = function() {
    const u = new URL(location.href);
    u.searchParams.set('_lc_refresh', String(Date.now()));
    location.replace(u.toString());
};

async function checkForAppUpdate() {
    if (!isStandaloneLaunch() || document.visibilityState === 'hidden') return false;
    try {
        const probe = new URL(location.origin + location.pathname);
        probe.searchParams.set('_lc_update_probe', String(Date.now()));
        const response = await fetch(probe.toString(), { cache: 'no-store', headers: { 'Cache-Control': 'no-cache' } });
        if (!response.ok) return false;
        const html = await response.text();
        const latestDoc = new DOMParser().parseFromString(html, 'text/html');
        const latest = latestDoc.querySelector('script[type="module"][src]')?.getAttribute('src') || '';
        const current = document.querySelector('script[type="module"][src]')?.getAttribute('src') || '';
        if (!latest || !current || latest === current) return false;
        const guard = `leopardcat.reload-for:${latest}`;
        if (sessionStorage.getItem(guard) === '1') return false;
        sessionStorage.setItem(guard, '1');
        window.forceAppRefresh();
        return true;
    } catch (error) {
        console.warn('[App update] check unavailable', error);
        return false;
    }
}

function initStandaloneUpdateControls() {
    cleanRefreshMarker();
    const btn = document.getElementById('standalone-refresh');
    if (btn && isStandaloneLaunch()) {
        btn.classList.remove('hidden');
        btn.title = uiText('reload_app', '重新載入');
        btn.setAttribute('aria-label', uiText('reload_app', '重新載入'));
    }
    if (!isStandaloneLaunch()) return;
    setTimeout(checkForAppUpdate, 600);
    window.addEventListener('pageshow', () => setTimeout(checkForAppUpdate, 250));
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') setTimeout(checkForAppUpdate, 250);
    });
}

document.addEventListener('DOMContentLoaded', initStandaloneUpdateControls);
"""
assert needle in js
js=js.replace(needle,insert,1)

old="""async function performReading(q, drawIndices = null, seed = null) {
    const common = window.siteData[window.currentLang].common;
    if (!q.trim()) {
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(common.err_empty_question);
    }
    try {
        const resolvedInput = await resolveQuestionInput(q);
        q = resolvedInput.question;
        window.currentQuestionSource = resolvedInput.source;
        window.currentQuestionLanguage = getQuestionLanguageTag(q);
    } catch (error) {
        console.warn('[Threads source] unable to resolve public post', error);
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(uiText('err_threads_source_unavailable', '無法讀取這則 Threads 公開貼文，請確認網址與公開狀態後再試。'));
    }
    const debug = q.toUpperCase() === 'DEBUG' || q.toUpperCase() === 'FORCE_DEBUG';
    if (!debug && !chargeLocalMana()) {
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(common.err_mana_depleted);
    }

    document.querySelectorAll('.modular-retry-bubble').forEach(el => el.remove());
    document.getElementById('fortune-ritual-area').classList.add('hidden');
    document.getElementById('fortune-chat-area').classList.remove('hidden');
    appendBubble('user', q);
    window.pendingDrawOptions = Array.isArray(drawIndices) ? {drawIndices: drawIndices.slice(), seed} : {};
    try {
        await window.getModularReading(q, window.pendingDrawOptions);
    } catch (e) {
        console.warn('[Divination v1] modular reading unavailable; preserving the same reading for retry:', e);
        if (!debug) refundLocalMana();
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        showModularRetry(q, e);
    }
}
"""
new="""async function performReading(q, drawIndices = null, seed = null) {
    const common = window.siteData[window.currentLang].common;
    if (!q.trim()) {
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(common.err_empty_question);
    }
    if (!beginReadingRequest()) return;
    let preserveRequestId = false;
    let debug = false;
    try {
        try {
            const resolvedInput = await resolveQuestionInput(q);
            q = resolvedInput.question;
            window.currentQuestionSource = resolvedInput.source;
            window.currentQuestionLanguage = getQuestionLanguageTag(q);
        } catch (error) {
            console.warn('[Threads source] unable to resolve public post', error);
            if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
            alert(uiText('err_threads_source_unavailable', '無法讀取這則 Threads 公開貼文，請確認網址與公開狀態後再試。'));
            return;
        }
        debug = q.toUpperCase() === 'DEBUG' || q.toUpperCase() === 'FORCE_DEBUG';
        if (!debug && !chargeLocalMana()) {
            if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
            alert(common.err_mana_depleted);
            return;
        }

        document.querySelectorAll('.modular-retry-bubble').forEach(el => el.remove());
        document.getElementById('fortune-ritual-area').classList.add('hidden');
        document.getElementById('fortune-chat-area').classList.remove('hidden');
        appendBubble('user', q);
        window.pendingDrawOptions = Array.isArray(drawIndices) ? {drawIndices: drawIndices.slice(), seed} : {};
        try {
            await window.getModularReading(q, window.pendingDrawOptions);
        } catch (e) {
            console.warn('[Divination v1] modular reading unavailable; preserving the same reading for retry:', e);
            preserveRequestId = !e.responseReceived;
            if (!debug) refundLocalMana();
            if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
            showModularRetry(q, e);
        }
    } finally {
        endReadingRequest({ preserveRequestId });
    }
}
"""
assert old in js
js=js.replace(old,new,1)

old_body="""            method: 'tarot', persona: window.activePersonaId || undefined, question: q,
            input: {
"""
new_body="""            method: 'tarot', persona: window.activePersonaId || undefined, question: q,
            clientRequestId: window.readingRequestState?.clientRequestId || undefined,
            input: {
"""
assert old_body in js
js=js.replace(old_body,new_body,1)

old_err="""        const err = new Error(errData.message || `DIVINATION_V1_${resp.status}`);
        err.status = resp.status;
        err.code = errData.code || errData.error;
        throw err;
"""
new_err="""        const err = new Error(errData.message || `DIVINATION_V1_${resp.status}`);
        err.status = resp.status;
        err.code = errData.code || errData.error;
        err.responseReceived = true;
        throw err;
"""
assert old_err in js
js=js.replace(old_err,new_err,1)

reset_needle="""    window.pendingDrawOptions = null;
    lastShareFile = null;
"""
reset_new="""    window.pendingDrawOptions = null;
    window.readingRequestState = { inFlight: false, clientRequestId: null };
    setPrimaryReadingBusy(false);
    lastShareFile = null;
"""
assert reset_needle in js
js=js.replace(reset_needle,reset_new,1)
js_path.write_text(js,encoding='utf-8')

index=index_path.read_text(encoding='utf-8')
needle='''    <div id="bg-overlay"></div>\n    \n    <div id="app">'''
repl='''    <div id="bg-overlay"></div>\n    <button id="standalone-refresh" type="button" class="standalone-refresh hidden" onclick="forceAppRefresh()" aria-label="重新載入" title="重新載入">↻</button>\n    \n    <div id="app">'''
assert needle in index
index=index.replace(needle,repl,1)
index_path.write_text(index,encoding='utf-8')

css=css_path.read_text(encoding='utf-8')
css += r'''

/* Reading single-flight + iOS home-screen update guard */
#btn-primary-draw.is-reading-pending { cursor: wait; opacity: .78; }
#btn-primary-draw.is-reading-pending::after { content: ' ···'; letter-spacing: .12em; }
.draw-mode-details.is-reading-pending { pointer-events: none; opacity: .58; }
.standalone-refresh { position: fixed; left: max(14px, env(safe-area-inset-left)); bottom: max(14px, env(safe-area-inset-bottom)); width: 42px; height: 42px; border-radius: 999px; border: 1px solid var(--color-gold-glow); background: rgba(5,8,6,.88); color: var(--color-gold); z-index: 1600; font-size: 23px; line-height: 1; backdrop-filter: blur(10px); box-shadow: 0 6px 22px rgba(0,0,0,.3); }
.standalone-refresh:active { transform: scale(.95); }
'''
css_path.write_text(css,encoding='utf-8')

locales=json.loads(locales_path.read_text(encoding='utf-8'))
texts={
'zh':('大師正在感應…','重新載入'),
'en':('The Master is reading…','Reload app'),
'ja':('大師が牌を読み取っています…','再読み込み'),
'ko':('대사가 카드를 읽고 있습니다…','앱 새로고침'),
'es':('El Maestro está leyendo…','Recargar app'),
}
for lang,(pending,reload_) in texts.items():
    common=locales.setdefault(lang,{}).setdefault('common',{})
    common['reading_in_progress']=pending
    common['reload_app']=reload_
locales_path.write_text(json.dumps(locales,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

server=server_path.read_text(encoding='utf-8')
server=server.replace('import re\n','import re\nimport threading\nimport time\n',1)
needle="""THREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'\n\nTHREADS_ALLOWED_HOSTS"""
repl="""THREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'\n\nREADING_REQUEST_LOCK = threading.Lock()\nREADING_REQUESTS_IN_FLIGHT = {}\nREADING_REQUEST_TTL_SECONDS = 180\n\ndef begin_reading_request(client_request_id):\n    if not client_request_id:\n        return True\n    now = time.time()\n    with READING_REQUEST_LOCK:\n        stale = [key for key, started in READING_REQUESTS_IN_FLIGHT.items() if now - started > READING_REQUEST_TTL_SECONDS]\n        for key in stale:\n            READING_REQUESTS_IN_FLIGHT.pop(key, None)\n        if client_request_id in READING_REQUESTS_IN_FLIGHT:\n            return False\n        READING_REQUESTS_IN_FLIGHT[client_request_id] = now\n        return True\n\ndef end_reading_request(client_request_id):\n    if not client_request_id:\n        return\n    with READING_REQUEST_LOCK:\n        READING_REQUESTS_IN_FLIGHT.pop(client_request_id, None)\n\nTHREADS_ALLOWED_HOSTS"""
assert needle in server
server=server.replace(needle,repl,1)

needle="""                reading_id = str(req_data.get('readingId') or '')
                session_token = str(req_data.get('sessionToken') or '')

                if reading_id and session_token:
"""
repl="""                reading_id = str(req_data.get('readingId') or '')
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
"""
assert needle in server
server=server.replace(needle,repl,1)

needle="""            except Exception as e:
                log(f\"!!! MODULAR DIVINATION ERROR: {e}\")
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'reading_failed'}, ensure_ascii=False).encode('utf-8'))
            return

        if self.path == '/api/v1/decks':
"""
repl="""            except Exception as e:
                log(f\"!!! MODULAR DIVINATION ERROR: {e}\")
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
"""
assert needle in server
server=server.replace(needle,repl,1)
server_path.write_text(server,encoding='utf-8')

# Focused regression contract
test=(web/'tests/test_reading_singleflight_home_update.py')
test.write_text(r'''from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_primary_reading_is_single_flight_and_has_immediate_busy_feedback():
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    assert "window.readingRequestState = { inFlight: false, clientRequestId: null }" in js
    assert 'if (state.inFlight) return false' in js
    assert 'if (!beginReadingRequest()) return' in js
    assert "btn.disabled = Boolean(busy)" in js
    assert "btn.setAttribute('aria-busy'" in js
    assert "clientRequestId: window.readingRequestState?.clientRequestId" in js
    assert 'id="btn-primary-draw"' in html

def test_server_rejects_same_initial_client_request_while_in_flight():
    src=(ROOT/'fortune_server.py').read_text(encoding='utf-8')
    assert 'READING_REQUESTS_IN_FLIGHT = {}' in src
    assert 'begin_reading_request(client_request_id)' in src
    assert "'reading_in_progress'" in src
    assert 'end_reading_request' in src

def test_home_screen_has_manual_reload_and_automatic_bundle_update_check():
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    server=(ROOT/'fortune_server.py').read_text(encoding='utf-8')
    assert 'id="standalone-refresh"' in html
    assert "navigator.standalone === true" in js
    assert 'async function checkForAppUpdate()' in js
    assert "cache: 'no-store'" in js
    assert "document.addEventListener('visibilitychange'" in js
    assert "location.replace(u.toString())" in js
    assert "'Cache-Control', 'no-cache, no-store, must-revalidate'" in server
    assert 'serviceWorker.register' not in js
''',encoding='utf-8')
print('singleflight_home_update_patch=ok')
