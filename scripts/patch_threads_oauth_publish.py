from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'website' / 'main.js'
SERVER = ROOT / 'website' / 'fortune_server.py'
TEST = ROOT / 'website' / 'tests' / 'test_threads_oauth_publish_contract.py'
DOC = ROOT / 'docs' / 'experience' / 'THREADS_OAUTH_TEXT_ATTACHMENT.md'

main = MAIN.read_text(encoding='utf-8')
server = SERVER.read_text(encoding='utf-8')

old_import = 'import time\n\nfrom divination import ReadingRequest, build_default_engine\n'
new_import = 'import time\nimport secrets\n\nfrom divination import ReadingRequest, build_default_engine\n'
if old_import not in server:
    raise SystemExit('server import anchor missing; refusing stale patch')
server = server.replace(old_import, new_import, 1)

anchor = 'from divination.lenormand import public_method_info as lenormand_public_method_info\n'
replacement = anchor + 'from divination.threads_publishing import ThreadsPublishingService, ThreadsPublishingError\n'
if server.count(anchor) != 1:
    raise SystemExit('Threads publishing import anchor not unique')
server = server.replace(anchor, replacement, 1)

anchor = "THREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'\n"
replacement = anchor + 'THREADS_PUBLISHER = ThreadsPublishingService(load_env_value)\n'
if server.count(anchor) != 1:
    raise SystemExit('Threads reader anchor not unique')
server = server.replace(anchor, replacement, 1)

old_handler = '''class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
'''
new_handler = '''class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    THREADS_SESSION_COOKIE = 'lc_threads_session'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _send_api_json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def _threads_session_id(self, create=False):
        cookie = self.headers.get('Cookie', '')
        for part in cookie.split(';'):
            key, sep, value = part.strip().partition('=')
            if sep and key == self.THREADS_SESSION_COOKIE and re.fullmatch(r'[A-Za-z0-9_-]{20,128}', value):
                return value
        return secrets.token_urlsafe(32) if create else ''

    def _set_threads_session_cookie(self, session_id):
        self.send_header(
            'Set-Cookie',
            f'{self.THREADS_SESSION_COOKIE}={session_id}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=5184000'
        )

    def do_GET(self):
'''
if old_handler not in server:
    raise SystemExit('handler anchor missing; refusing stale patch')
server = server.replace(old_handler, new_handler, 1)

get_anchor = '        # 👑 API Endpoints\n'
get_routes = '''        # 👑 API Endpoints
        if path == '/api/v1/threads/oauth/status':
            session_id = self._threads_session_id(create=False)
            self._send_api_json(200, THREADS_PUBLISHER.status(session_id))
            return
        if path == '/api/v1/threads/oauth/start':
            params = urllib.parse.parse_qs(query)
            session_id = self._threads_session_id(create=True)
            try:
                location = THREADS_PUBLISHER.issue_authorization(
                    session_id,
                    (params.get('return_to') or ['/'])[0],
                )
            except ThreadsPublishingError as e:
                self._send_api_json(e.status, {'error': e.code})
                return
            self.send_response(302)
            self._set_threads_session_cookie(session_id)
            self.send_header('Location', location)
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return
        if path == '/api/v1/threads/oauth/callback':
            params = urllib.parse.parse_qs(query)
            session_id = self._threads_session_id(create=False)
            if not session_id or params.get('error'):
                self.send_response(302)
                self.send_header('Location', '/?threads=oauth_error')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                return
            try:
                result = THREADS_PUBLISHER.complete_authorization(
                    session_id,
                    (params.get('state') or [''])[0],
                    (params.get('code') or [''])[0],
                )
                return_to = result.get('return_to') or '/'
                account = result.get('account') or {}
                marker = urllib.parse.urlencode({
                    'threads': 'connected',
                    'threads_account': account.get('username') or '',
                })
                joiner = '&' if '?' in return_to else '?'
                location = f'{return_to}{joiner}{marker}'
            except ThreadsPublishingError as e:
                location = '/?' + urllib.parse.urlencode({'threads': 'oauth_error', 'reason': e.code})
            self.send_response(302)
            self.send_header('Location', location)
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return
'''
if server.count(get_anchor) != 1:
    raise SystemExit('GET route anchor not unique')
server = server.replace(get_anchor, get_routes, 1)

post_anchor = '''    def do_POST(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/v1/sources/threads':
'''
post_routes = '''    def do_POST(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/v1/threads/oauth/disconnect':
            THREADS_PUBLISHER.disconnect(self._threads_session_id(create=False))
            self._send_api_json(200, {'connected': False})
            return
        if path == '/api/v1/threads/publish':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0 or content_length > 32 * 1024:
                self._send_api_json(413, {'error': 'threads_publish_payload_too_large'})
                return
            try:
                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))
                result = THREADS_PUBLISHER.publish_text(
                    self._threads_session_id(create=False),
                    payload.get('primary_text'),
                    payload.get('text_attachment'),
                )
                self._send_api_json(201, {'post': result})
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
                self._send_api_json(400, {'error': 'threads_publish_payload_invalid'})
            except ThreadsPublishingError as e:
                self._send_api_json(e.status, {'error': e.code})
            return
        if path == '/api/v1/sources/threads':
'''
if server.count(post_anchor) != 1:
    raise SystemExit('POST route anchor not unique')
server = server.replace(post_anchor, post_routes, 1)

pattern = re.compile(r"window\.prepareThreadsShare = async function\(event\) \{.*?\n\};\n\nfunction refreshSocialShareText\(\) \{", re.S)
match = pattern.search(main)
if not match:
    raise SystemExit('prepareThreadsShare block missing; refusing stale patch')
new_share = '''window.prepareThreadsShare = async function(event) {
    const link = document.getElementById('share-threads');
    if (!link || !lastShareText) return true;
    const plan = threadsSharePlan(lastShareText);
    if (!plan.isLong) return true;

    // Long-form is a separate capability. Never put >500 characters into intent
    // and never fall back to clipboard/manual paste.
    event?.preventDefault?.();
    window.pendingThreadsTextAttachment = plan.textAttachment;

    let oauth = null;
    try {
        const statusResponse = await fetch('/api/v1/threads/oauth/status', {
            credentials: 'same-origin', cache: 'no-store'
        });
        if (statusResponse.ok) oauth = await statusResponse.json();
    } catch (error) {
        console.warn('[Threads] OAuth status unavailable', error);
    }

    if (oauth?.configured && !oauth?.connected) {
        const returnTo = `${location.pathname}${location.search}${location.hash}`;
        location.href = `/api/v1/threads/oauth/start?return_to=${encodeURIComponent(returnTo)}`;
        return false;
    }

    if (oauth?.connected && plan.textAttachment) {
        const account = oauth.account || {};
        const identity = account.username ? `@${account.username}` : (account.name || '目前連線的 Threads 帳號');
        const approved = window.confirm(`要以 ${identity} 發布完整大師解讀嗎？`);
        if (!approved) return false;
        link.setAttribute('aria-busy', 'true');
        try {
            const response = await fetch('/api/v1/threads/publish', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    primary_text: plan.primaryText,
                    text_attachment: plan.textAttachment
                })
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok || !payload?.post?.id) throw new Error(payload?.error || 'threads_publish_failed');
            window.alert(`已由 ${identity} 發布完整大師解讀。`);
            return false;
        } catch (error) {
            console.warn('[Threads] API publish unavailable; using bounded intent fallback', error);
            window.alert('Threads API 發布暫時不可用，將改用一般分享視窗；完整長文不會被塞進超過 500 字的主貼文。');
        } finally {
            link.removeAttribute('aria-busy');
        }
    }

    const composer = `https://www.threads.net/intent/post?text=${encodeURIComponent(plan.primaryText)}`;
    window.open(composer, '_blank', 'noopener');
    return false;
};

function refreshSocialShareText() {'''
main = main[:match.start()] + new_share + main[match.end():]

TEST.write_text('''from pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nMAIN = (ROOT / 'main.js').read_text(encoding='utf-8')\nSERVER = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')\nSERVICE = (ROOT / 'divination' / 'threads_publishing.py').read_text(encoding='utf-8')\n\n\ndef test_browser_never_receives_threads_secret_or_token():\n    assert 'THREADS_APP_SECRET' not in MAIN\n    assert 'access_token' not in MAIN\n    assert "fetch('/api/v1/threads/oauth/status'" in MAIN\n    assert "fetch('/api/v1/threads/publish'" in MAIN\n    assert "credentials: 'same-origin'" in MAIN\n\n\ndef test_long_share_connects_then_publishes_typed_attachment():\n    assert '/api/v1/threads/oauth/start?return_to=' in MAIN\n    assert 'primary_text: plan.primaryText' in MAIN\n    assert 'text_attachment: plan.textAttachment' in MAIN\n    assert 'navigator.clipboard.writeText(plan.text)' not in MAIN\n\n\ndef test_server_owns_oauth_and_publish_capability():\n    for route in (\n        '/api/v1/threads/oauth/status',\n        '/api/v1/threads/oauth/start',\n        '/api/v1/threads/oauth/callback',\n        '/api/v1/threads/oauth/disconnect',\n        '/api/v1/threads/publish',\n    ):\n        assert route in SERVER\n    assert 'ThreadsPublishingService(load_env_value)' in SERVER\n    assert 'HttpOnly; Secure; SameSite=Lax' in SERVER\n\n\ndef test_tokens_are_ephemeral_and_server_only():\n    assert 'intentionally not persisted' in SERVICE\n    assert "self._sessions = {}" in SERVICE\n    assert "headers['Authorization'] = f'Bearer {token}'" in SERVICE\n    assert "'THREADS_APP_SECRET'" in SERVICE\n''', encoding='utf-8')

DOC.write_text('''# Threads OAuth + Text Attachment Capability\n\nStatus: implementation candidate for Issue #65.\n\n## Canonical capability chain\n\n`explicit user OAuth -> server-only ephemeral token -> account identity -> bounded primary post (<=500) -> official text_attachment -> explicit publish action`\n\n## Security invariants\n\n- Threads App Secret and user access tokens never enter browser JavaScript.\n- OAuth state is random, single-use, expires after ten minutes, and is bound to the HttpOnly browser session cookie.\n- Tokens are held only in process memory; restart disconnects the account instead of persisting credentials.\n- Browser can read only `configured`, `connected`, and public account identity.\n- Publishing requires an explicit confirmation naming the target Threads account.\n- Questions and Master answers are not added to server persistence by this capability.\n\n## Monotonic share invariant\n\nA long Master interpretation may be upgraded from bounded intent to OAuth `text_attachment`, but it may never regress to an over-limit intent or clipboard/manual-paste workflow.\n\n## Platform contract checked 2026-09-06\n\nMeta Threads API uses OAuth authorization code flow with `threads_basic` + `threads_content_publish`; publishing text supports `text_attachment`, and `auto_publish_text=true` can publish a text container directly. Re-check the official contract before production acceptance because platform APIs can change.\n\n## Remaining production prerequisites\n\n- Configure `THREADS_APP_ID`, `THREADS_APP_SECRET`, and exact `THREADS_REDIRECT_URI` on Oracle.\n- Register that redirect URI in the Meta App Threads use case.\n- Perform a real-account OAuth + iPhone publish acceptance before closing #65.\n''', encoding='utf-8')

MAIN.write_text(main, encoding='utf-8')
SERVER.write_text(server, encoding='utf-8')
print('Threads OAuth publishing patch applied')
