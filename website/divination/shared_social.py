import json
import urllib.error
import urllib.request


DEFAULT_SOCIAL_RUNTIME_URL = 'https://studio.milkcat.org/dashboard/api/social'
PRODUCT_ID = 'leopardcat-tarot'


class SharedSocialError(Exception):
    def __init__(self, code, status=502):
        super().__init__(code)
        self.code = code
        self.status = status


class SharedSocialClient:
    """Server-side-only LeopardCat client for the AgentOS shared social runtime.

    This client owns no Meta App credential or provider access token. Its product
    credential authenticates only LeopardCat to the bounded AgentOS social API.
    """

    def __init__(self, value_loader, opener=None):
        self._load = value_loader
        self._opener = opener or urllib.request.urlopen

    def base_url(self):
        return (self._load('AGENTOS_SOCIAL_RUNTIME_URL') or DEFAULT_SOCIAL_RUNTIME_URL).rstrip('/')

    def product_key(self):
        return str(self._load('AGENTOS_SOCIAL_PRODUCT_KEY') or '').strip()

    def enabled(self):
        return bool(self.product_key())

    def _request(self, path, payload=None, acceptance_id=None, timeout=12):
        url = self.base_url() + path
        headers = {'Accept': 'application/json', 'User-Agent': 'LeopardCat-Tarot/AgentOS-Social/1.0'}
        data = None
        method = 'GET'
        if payload is not None:
            method = 'POST'
            data = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            headers['Content-Type'] = 'application/json'
            key = self.product_key()
            if not key:
                raise SharedSocialError('shared_social_product_not_configured', 503)
            headers['X-AgentOS-Product-Key'] = key
        if acceptance_id:
            headers['X-AgentOS-Acceptance-ID'] = str(acceptance_id)
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener(request, timeout=timeout) as response:
                status = int(getattr(response, 'status', 200))
                body = json.loads(response.read(128 * 1024).decode('utf-8'))
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read(64 * 1024).decode('utf-8'))
                code = str(body.get('error') or 'shared_social_rejected')
            except Exception:
                code = 'shared_social_rejected'
            raise SharedSocialError(code, exc.code) from exc
        except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SharedSocialError('shared_social_unavailable', 502) from exc
        if not isinstance(body, dict):
            raise SharedSocialError('shared_social_invalid_response', 502)
        if status >= 400 or body.get('ok') is False:
            raise SharedSocialError(str(body.get('error') or 'shared_social_rejected'), status)
        return body

    def provider_status(self):
        value = self._request('/healthz')
        threads = value.get('threads') if isinstance(value, dict) else None
        return {
            'configured': bool(isinstance(threads, dict) and threads.get('configured')),
            'shared_runtime': True,
        }

    def status(self, binding_id=None, connection_id=None):
        payload = {
            'product_id': PRODUCT_ID,
            'platform': 'threads',
            'operation': 'status',
        }
        if binding_id:
            payload['account_binding_id'] = str(binding_id)
        if connection_id:
            payload['object_id'] = str(connection_id)
        return self._request('/v1/social/status', payload)

    def begin_connect(self, return_to='/'):
        payload = {
            'product_id': PRODUCT_ID,
            'platform': 'threads',
            'operation': 'connect',
            'return_to': str(return_to or '/'),
        }
        value = self._request('/v1/social/connect', payload)
        url = str(value.get('browser_start_url') or '')
        if not url.startswith(self.base_url() + '/v1/social/oauth/threads/start?ticket='):
            raise SharedSocialError('shared_social_browser_handoff_invalid', 502)
        return value

    def publish(self, *, binding_id, target_account_id, primary_text, text_attachment, write_intent_id, acceptance_id):
        payload = {
            'product_id': PRODUCT_ID,
            'platform': 'threads',
            'operation': 'publish',
            'account_binding_id': str(binding_id or ''),
            'target_account_id': str(target_account_id or ''),
            'primary_text': str(primary_text or ''),
            'text_attachment': text_attachment,
            'write_intent_id': str(write_intent_id or ''),
        }
        return self._request('/v1/social/publish', payload, acceptance_id=acceptance_id)

    def disconnect(self, *, binding_id, target_account_id, write_intent_id, acceptance_id):
        payload = {
            'product_id': PRODUCT_ID,
            'platform': 'threads',
            'operation': 'disconnect',
            'account_binding_id': str(binding_id or ''),
            'target_account_id': str(target_account_id or ''),
            'write_intent_id': str(write_intent_id or ''),
        }
        return self._request('/v1/social/disconnect', payload, acceptance_id=acceptance_id)
