import json
import secrets
import threading
import time
import urllib.parse
import urllib.request
import urllib.error

from .shared_social import SharedSocialClient, SharedSocialError


THREADS_TEXT_LIMIT = 500
THREADS_ATTACHMENT_LIMIT = 10000
THREADS_SCOPES = ('threads_basic', 'threads_content_publish')


class ThreadsPublishingError(Exception):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code = code
        self.status = status


class ThreadsPublishingService:
    """Threads account/publish facade used by the LeopardCat HTTP routes.

    Preferred mode is the AgentOS shared social runtime. In that mode LeopardCat
    stores only a random local browser session plus the safe account binding and
    public profile; Meta app credentials and provider access tokens stay in Core.
    Product-local provider access tokens are intentionally not persisted.

    The legacy direct-provider mode remains as a fail-closed compatibility path
    until the governed shared write-acceptance bridge is accepted end to end.
    """

    def __init__(self, value_loader, graph_host='https://graph.threads.net', authorize_host='https://threads.net'):
        self._load = value_loader
        self.graph_host = graph_host.rstrip('/')
        self.authorize_host = authorize_host.rstrip('/')
        self._lock = threading.Lock()
        self._states = {}
        self._sessions = {}
        self._shared = SharedSocialClient(value_loader)

    def _shared_enabled(self):
        return self._shared.enabled()

    def configured(self):
        if self._shared_enabled():
            try:
                return bool(self._shared.provider_status().get('configured'))
            except SharedSocialError:
                return False
        return bool(self._load('THREADS_APP_ID') and self._load('THREADS_APP_SECRET') and self._redirect_uri())

    def _redirect_uri(self):
        return self._load('THREADS_REDIRECT_URI') or ''

    @staticmethod
    def _safe_return_to(value):
        value = str(value or '/').strip()
        if not value.startswith('/') or value.startswith('//'):
            return '/'
        return value[:1024]

    @staticmethod
    def _shared_error(exc):
        return ThreadsPublishingError(exc.code, exc.status)

    def issue_authorization(self, session_id, return_to='/'):
        if self._shared_enabled():
            try:
                provider = self._shared.provider_status()
                if not provider.get('configured'):
                    raise ThreadsPublishingError('threads_oauth_not_configured', 503)
                state = secrets.token_urlsafe(32)
                local_callback = '/api/v1/threads/oauth/callback?' + urllib.parse.urlencode({
                    'state': state,
                    'shared': '1',
                })
                handoff = self._shared.begin_connect(local_callback)
                connection_id = str(handoff.get('connection_id') or '')
                browser_start_url = str(handoff.get('browser_start_url') or '')
                if not connection_id or not browser_start_url:
                    raise ThreadsPublishingError('threads_shared_handoff_invalid', 502)
                with self._lock:
                    now = time.time()
                    self._states = {k: v for k, v in self._states.items() if v['expires_at'] > now}
                    self._states[state] = {
                        'mode': 'shared',
                        'session_id': session_id,
                        'connection_id': connection_id,
                        'return_to': self._safe_return_to(return_to),
                        'expires_at': now + 600,
                    }
                return browser_start_url
            except SharedSocialError as exc:
                raise self._shared_error(exc) from exc

        if not self.configured():
            raise ThreadsPublishingError('threads_oauth_not_configured', 503)
        state = secrets.token_urlsafe(32)
        with self._lock:
            now = time.time()
            self._states = {k: v for k, v in self._states.items() if v['expires_at'] > now}
            self._states[state] = {
                'mode': 'direct',
                'session_id': session_id,
                'return_to': self._safe_return_to(return_to),
                'expires_at': now + 600,
            }
        query = urllib.parse.urlencode({
            'client_id': self._load('THREADS_APP_ID'),
            'redirect_uri': self._redirect_uri(),
            'scope': ','.join(THREADS_SCOPES),
            'response_type': 'code',
            'state': state,
        })
        return f'{self.authorize_host}/oauth/authorize?{query}'

    def _consume_state(self, state, session_id):
        with self._lock:
            record = self._states.pop(str(state or ''), None)
        if not record or record['expires_at'] <= time.time() or record['session_id'] != session_id:
            raise ThreadsPublishingError('threads_oauth_state_invalid', 400)
        return record

    def _request_json(self, url, method='GET', token=None, body=None, timeout=15):
        headers = {'Accept': 'application/json', 'User-Agent': 'LeopardCat-Tarot/1.0'}
        data = None
        if token:
            headers['Authorization'] = f'Bearer {token}'
        if body is not None:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            data = urllib.parse.urlencode(body).encode('utf-8')
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            raise ThreadsPublishingError('threads_api_unavailable', 502) from exc
        if not isinstance(payload, dict) or payload.get('error'):
            raise ThreadsPublishingError('threads_api_rejected', 502)
        return payload

    def complete_authorization(self, session_id, state, code):
        record = self._consume_state(state, session_id)
        if record.get('mode') == 'shared':
            try:
                result = self._shared.status(connection_id=record.get('connection_id'))
            except SharedSocialError as exc:
                raise self._shared_error(exc) from exc
            if not result.get('connected') or not result.get('binding_id'):
                raise ThreadsPublishingError('threads_shared_oauth_incomplete', 502)
            account = result.get('account') if isinstance(result.get('account'), dict) else {}
            public_profile = {
                'id': str(account.get('provider_account_id') or ''),
                'username': str(account.get('username') or ''),
                'name': '',
            }
            if not public_profile['id']:
                raise ThreadsPublishingError('threads_shared_identity_missing', 502)
            with self._lock:
                self._sessions[session_id] = {
                    'mode': 'shared',
                    'binding_id': str(result.get('binding_id')),
                    'profile': public_profile,
                }
            return {'account': public_profile, 'return_to': record['return_to']}

        if not code:
            raise ThreadsPublishingError('threads_oauth_code_missing', 400)
        token_url = f'{self.graph_host}/oauth/access_token'
        short = self._request_json(token_url, method='POST', body={
            'client_id': self._load('THREADS_APP_ID'),
            'client_secret': self._load('THREADS_APP_SECRET'),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self._redirect_uri(),
        })
        short_token = short.get('access_token')
        if not short_token:
            raise ThreadsPublishingError('threads_oauth_token_missing', 502)

        exchange_url = f'{self.graph_host}/access_token?' + urllib.parse.urlencode({
            'grant_type': 'th_exchange_token',
            'client_secret': self._load('THREADS_APP_SECRET'),
            'access_token': short_token,
        })
        long_lived = self._request_json(exchange_url)
        token = long_lived.get('access_token') or short_token
        expires_in = int(long_lived.get('expires_in') or 3600)
        profile = self._request_json(f'{self.graph_host}/me?fields=id,username,name', token=token)
        public_profile = {
            'id': str(profile.get('id') or short.get('user_id') or ''),
            'username': str(profile.get('username') or ''),
            'name': str(profile.get('name') or ''),
        }
        with self._lock:
            self._sessions[session_id] = {
                'mode': 'direct',
                'access_token': token,
                'expires_at': time.time() + max(60, expires_in - 60),
                'profile': public_profile,
            }
        return {'account': public_profile, 'return_to': record['return_to']}

    def status(self, session_id):
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.get('mode') == 'direct' and session['expires_at'] <= time.time():
                self._sessions.pop(session_id, None)
                session = None
            session = dict(session) if session else None

        if session and session.get('mode') == 'shared':
            try:
                shared = self._shared.status(binding_id=session.get('binding_id'))
            except SharedSocialError:
                shared = {'connected': False}
            if not shared.get('connected'):
                with self._lock:
                    self._sessions.pop(session_id, None)
                session = None

        profile = dict(session['profile']) if session else None
        return {'configured': self.configured(), 'connected': bool(session), 'account': profile}

    def disconnect(self, session_id):
        with self._lock:
            session = self._sessions.get(session_id)
        if session and session.get('mode') == 'shared':
            raise ThreadsPublishingError('threads_disconnect_governance_pending', 503)
        with self._lock:
            self._sessions.pop(session_id, None)

    def publish_text(self, session_id, primary_text, text_attachment=None):
        primary = str(primary_text or '').strip()
        if not primary or len(primary) > THREADS_TEXT_LIMIT:
            raise ThreadsPublishingError('threads_primary_text_invalid', 400)
        attachment = text_attachment if isinstance(text_attachment, dict) else None
        if attachment:
            plaintext = str(attachment.get('plaintext') or '').strip()
            if not plaintext or len(plaintext) > THREADS_ATTACHMENT_LIMIT:
                raise ThreadsPublishingError('threads_text_attachment_invalid', 400)
            attachment = {'plaintext': plaintext}
            link_url = str(text_attachment.get('link_attachment_url') or '').strip()
            if link_url:
                parsed = urllib.parse.urlsplit(link_url)
                if parsed.scheme not in {'http', 'https'}:
                    raise ThreadsPublishingError('threads_text_attachment_link_invalid', 400)
                attachment['link_attachment_url'] = link_url

        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.get('mode') == 'direct' and session['expires_at'] <= time.time():
                self._sessions.pop(session_id, None)
                session = None
            session = dict(session) if session else None
        if not session:
            raise ThreadsPublishingError('threads_not_connected', 401)
        if session.get('mode') == 'shared':
            # The shared runtime intentionally requires a separately governed,
            # exact one-shot write acceptance. Until the product-click issuance
            # bridge lands, never silently downgrade that boundary here.
            raise ThreadsPublishingError('threads_publish_governance_pending', 503)

        token = session.get('access_token')
        profile = dict(session['profile'])
        if not token:
            raise ThreadsPublishingError('threads_not_connected', 401)
        params = {
            'media_type': 'TEXT',
            'text': primary,
            'auto_publish_text': 'true',
        }
        if attachment:
            params['text_attachment'] = json.dumps(attachment, ensure_ascii=False, separators=(',', ':'))
        url = f'{self.graph_host}/me/threads?' + urllib.parse.urlencode(params)
        result = self._request_json(url, method='POST', token=token)
        post_id = str(result.get('id') or '')
        if not post_id:
            raise ThreadsPublishingError('threads_publish_id_missing', 502)
        return {'id': post_id, 'account': profile, 'has_text_attachment': bool(attachment)}
