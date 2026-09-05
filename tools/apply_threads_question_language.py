from pathlib import Path
import json
import re

main_path = Path('website/main.js')
server_path = Path('website/fortune_server.py')
cap_path = Path('governance/capabilities.json')

s = main_path.read_text(encoding='utf-8')

old = """function getAILanguageTag(lang = window.currentLang) {
    const resolved = resolveLocale(lang);
    return ({ zh: 'zh-TW', en: 'en', ja: 'ja', ko: 'ko', es: 'es' })[resolved] || resolved || 'en';
}
"""
new = old + """
function detectQuestionLanguage(text, fallback = window.currentQuestionLanguage || getAILanguageTag()) {
    const value = String(text || '').trim();
    if (!value) return fallback || getAILanguageTag();
    if (/[ぁ-ゖァ-ヺー]/.test(value)) return 'ja';
    if (/[가-힣]/.test(value)) return 'ko';
    if (/[\u3400-\u9fff]/.test(value)) return 'zh-TW';
    if (/[¿¡ñáéíóúü]/i.test(value) || /\b(?:que|qué|para|por|una|uno|como|cómo|cuando|cuándo|donde|dónde|gracias|quiero|puede|puedo|será|futuro)\b/i.test(value)) return 'es';
    if (/[A-Za-z]/.test(value)) return 'en';
    return fallback || getAILanguageTag();
}

function getQuestionLanguageTag(text) {
    const detected = detectQuestionLanguage(text);
    window.currentQuestionLanguage = detected;
    return detected;
}
"""
if old not in s:
    raise SystemExit('language anchor missing')
s = s.replace(old, new, 1)

old = """window.pendingDrawOptions = null; // preserves manual seed/indices until a reading receipt exists
"""
new = old + """window.currentQuestionSource = null; // explicit public source metadata; never sent as a raw URL to the Master
window.currentQuestionLanguage = null; // latest user/question language, independent from UI locale

const THREADS_POST_URL_RE = /^https:\/\/(?:www\.)?threads\.(?:com|net)\/@[^/]+\/post\/[A-Za-z0-9_-]+\/?(?:[?#].*)?$/i;

async function resolveQuestionInput(rawQuestion) {
    const raw = String(rawQuestion || '').trim();
    if (!THREADS_POST_URL_RE.test(raw)) return { question: raw, source: null };
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55000);
    try {
        const response = await fetch('/api/v1/sources/threads', {
            method: 'POST', signal: controller.signal,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url: raw})
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok || !payload?.source?.text) throw new Error(payload?.error || 'THREADS_SOURCE_UNAVAILABLE');
        return { question: String(payload.source.text).trim(), source: payload.source };
    } finally {
        clearTimeout(timeoutId);
    }
}
"""
if old not in s:
    raise SystemExit('state anchor missing')
s = s.replace(old, new, 1)

old = """        chat_history: currentChatHistory,
"""
new = """        chat_history: currentChatHistory,
        question_source: window.currentQuestionSource,
        question_language: window.currentQuestionLanguage,
"""
if old not in s:
    raise SystemExit('snapshot anchor missing')
s = s.replace(old, new, 1)

old = """    window._lastQuestion = question;
    window.pendingReadingSession = local && data.session_token ? {reading_id:data.reading_id, session_token:data.session_token} : null;
"""
new = """    window._lastQuestion = question;
    window.currentQuestionSource = local ? (snapshot?.question_source || null) : null;
    window.currentQuestionLanguage = local ? (snapshot?.question_language || (question ? detectQuestionLanguage(question) : null)) : null;
    window.pendingReadingSession = local && data.session_token ? {reading_id:data.reading_id, session_token:data.session_token} : null;
"""
if old not in s:
    raise SystemExit('restore anchor missing')
s = s.replace(old, new, 1)

old = """function buildSocialShareText(shareMsg, shareUrl) {
    if (window.shareContentMode !== 'full') return `${shareMsg} ${shareUrl}`;
    const answer = latestMasterInterpretation();
    if (!answer) return `${shareMsg} ${shareUrl}`;
    const parts = [];
    if (window.shareIncludeQuestion && window._lastQuestion) {
        parts.push(`${uiText('share_question_heading', '我的提問')}\n${normalizeMasterShareText(window._lastQuestion)}`);
    }
    parts.push(answer);
    parts.push(shareUrl);
    return parts.join('\n\n');
}
"""
new = """function buildSocialShareText(shareMsg, shareUrl) {
    if (window.shareContentMode !== 'full') return `${shareMsg} ${shareUrl}`;
    const answer = latestMasterInterpretation();
    if (!answer) return `${shareMsg} ${shareUrl}`;
    const source = window.currentQuestionSource;
    const parts = [];
    if (source?.type === 'threads' && source.text && source.url) {
        parts.push(`${uiText('share_threads_question_heading', '該文作者提問：')}\n${normalizeMasterShareText(source.text)}`);
        parts.push(`${uiText('share_source_heading', '原文：')}\n${source.url}`);
        parts.push(`${uiText('share_master_heading', '大師解讀：')}\n${answer}`);
    } else {
        if (window.shareIncludeQuestion && window._lastQuestion) {
            parts.push(`${uiText('share_question_heading', '我的提問')}\n${normalizeMasterShareText(window._lastQuestion)}`);
        }
        parts.push(answer);
    }
    parts.push(shareUrl);
    return parts.join('\n\n');
}
"""
if old not in s:
    raise SystemExit('share anchor missing')
s = s.replace(old, new, 1)

# Resolve a Threads URL before charging mana/drawing. Extracted post text becomes the actual question.
old = """async function performReading(q, drawIndices = null, seed = null) {
    const common = window.siteData[window.currentLang].common;
    if (!q.trim()) {
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(common.err_empty_question);
    }
"""
new = """async function performReading(q, drawIndices = null, seed = null) {
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
"""
if old not in s:
    raise SystemExit('performReading anchor missing')
s = s.replace(old, new, 1)

# Initial and retry requests follow the actual question language.
s = s.replace("lang: getAILanguageTag()\n                } : {", "lang: getQuestionLanguageTag(q)\n                } : {", 1)
s = s.replace("lang: getAILanguageTag()\n                };", "lang: getQuestionLanguageTag(q)\n                };", 1)
# Follow-up modular request.
s = s.replace("lang: getAILanguageTag(), history: currentChatHistory", "lang: getQuestionLanguageTag(text), history: currentChatHistory", 1)
# Legacy single-card path and legacy follow-up path.
s = s.replace("lang: window.currentLang,\n                    history: currentChatHistory", "lang: getQuestionLanguageTag(q),\n                    history: currentChatHistory", 1)
s = s.replace("lang: window.currentLang, history: currentChatHistory", "lang: getQuestionLanguageTag(text), history: currentChatHistory", 1)

old = """    window.currentReadingState = null;
    window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false, phase: 'idle' };
"""
new = """    window.currentReadingState = null;
    window.currentQuestionSource = null;
    window.currentQuestionLanguage = null;
    window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false, phase: 'idle' };
"""
if old not in s:
    raise SystemExit('reset anchor missing')
s = s.replace(old, new, 1)

main_path.write_text(s, encoding='utf-8')

server = server_path.read_text(encoding='utf-8')
old = """PERSONA_PUBLISHER = PersonaPublisher(PERSONA_ROOT)
def call_master_prompt(prompt):
"""
new = """PERSONA_PUBLISHER = PersonaPublisher(PERSONA_ROOT)
THREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'
def call_master_prompt(prompt):
"""
if old not in server:
    raise SystemExit('server config anchor missing')
server = server.replace(old, new, 1)

old = """    def do_POST(self):
        path = self.path.split('?', 1)[0]
        share_image_match = re.fullmatch(r'/api/v1/readings/([^/]+)/share-image', path)
"""
new = """    def do_POST(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/v1/sources/threads':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0 or content_length > 16 * 1024:
                self.send_error(413); return
            try:
                payload = json.loads(self.rfile.read(content_length).decode('utf-8') or '{}')
                source_url = str(payload.get('url') or '').strip()
                parsed = urllib.parse.urlsplit(source_url)
                allowed_hosts = {'threads.com','www.threads.com','threads.net','www.threads.net'}
                if parsed.scheme != 'https' or (parsed.hostname or '').lower() not in allowed_hosts or not re.fullmatch(r'/@[^/]+/post/[A-Za-z0-9_-]+/?', parsed.path):
                    raise ValueError('invalid_threads_post_url')
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
"""
if old not in server:
    raise SystemExit('server POST anchor missing')
server = server.replace(old, new, 1)
server_path.write_text(server, encoding='utf-8')

caps = json.loads(cap_path.read_text(encoding='utf-8'))
protected = caps.setdefault('protected_capabilities', {})
protected['reading.reply-language-follows-user'] = {
    'status': 'protected',
    'contract': [
        'Master reply language follows the current user question rather than the site UI locale.',
        'Japanese kana, Korean Hangul, Traditional/Chinese Han text, English Latin text, and Spanish markers are detected deterministically; ambiguous symbol-only turns retain the previous question language before UI fallback.',
        'Initial readings, retries, legacy calls, and follow-up questions use the same question-language rule.'
    ],
    'evidence': ['website/main.js', 'website/tests/test_threads_question_language.py']
}
protected['reading.threads-public-source'] = {
    'status': 'protected',
    'contract': [
        'A pasted public Threads post URL is resolved through the AgentOS/vendor Threads reader; the Master receives extracted post text, not the raw URL.',
        'Only HTTPS threads.com/threads.net canonical post URLs are accepted and the LeopardCat backend proxies only to the localhost reader.',
        'Full social sharing of a Threads-sourced question preserves the public original URL and labels the source text separately from the Master interpretation.',
        'Threads source metadata is session-local reading state and does not grant continuation or management authority.'
    ],
    'evidence': ['website/main.js', 'website/fortune_server.py', 'website/tests/test_threads_question_language.py']
}
cap_path.write_text(json.dumps(caps, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
