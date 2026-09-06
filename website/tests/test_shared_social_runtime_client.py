import io
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from divination.shared_social import SharedSocialClient, SharedSocialError


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _limit=-1):
        return json.dumps(self.payload).encode('utf-8')


class FakeOpener:
    def __init__(self):
        self.requests = []

    def __call__(self, request, timeout=0):
        self.requests.append((request, timeout))
        path = request.full_url
        if path.endswith('/healthz'):
            return FakeResponse({'schema': 'agentos.social-runtime-status/v1', 'threads': {'configured': True}})
        body = json.loads((request.data or b'{}').decode('utf-8'))
        if path.endswith('/v1/social/connect'):
            return FakeResponse({
                'schema': 'agentos.social-browser-handoff/v1',
                'browser_start_url': 'https://studio.milkcat.org/dashboard/api/social/v1/social/oauth/threads/start?ticket=opaque',
                'expires_in': 300,
                'connection_id': 'connection-1',
            })
        if path.endswith('/v1/social/status'):
            return FakeResponse({
                'schema': 'agentos.social-status/v1',
                'configured': True,
                'connected': bool(body.get('account_binding_id')),
                'account': ({
                    'binding_id': body.get('account_binding_id'),
                    'provider_account_id': '42',
                    'username': 'cat',
                } if body.get('account_binding_id') else None),
            })
        if path.endswith('/v1/social/publish'):
            return FakeResponse({'schema': 'agentos.social-receipt/v1', 'ok': True, 'platform_object_id': 'thread-1'})
        raise AssertionError(path)


def loader(name):
    values = {
        'AGENTOS_SOCIAL_PRODUCT_KEY': 'PRODUCT-SECRET',
        'AGENTOS_SOCIAL_RUNTIME_URL': 'https://studio.milkcat.org/dashboard/api/social',
    }
    return values.get(name)


def test_provider_status_exposes_only_configured_boolean():
    opener = FakeOpener()
    client = SharedSocialClient(loader, opener=opener)
    assert client.provider_status() == {'configured': True, 'shared_runtime': True}
    request, _ = opener.requests[0]
    assert request.get_header('X-agentos-product-key') is None


def test_connect_keeps_product_key_in_server_header_not_browser_url():
    opener = FakeOpener()
    client = SharedSocialClient(loader, opener=opener)
    value = client.begin_connect('/reading/1')
    assert value['browser_start_url'].endswith('ticket=opaque')
    assert 'PRODUCT-SECRET' not in value['browser_start_url']
    request, _ = opener.requests[-1]
    assert request.get_header('X-agentos-product-key') == 'PRODUCT-SECRET'
    assert b'PRODUCT-SECRET' not in request.data


def test_status_uses_safe_binding_identifier_only():
    opener = FakeOpener()
    client = SharedSocialClient(loader, opener=opener)
    value = client.status(binding_id='leopardcat-tarot:threads:42')
    assert value['connected'] is True
    assert value['account']['provider_account_id'] == '42'
    assert 'token' not in repr(value).lower()


def test_publish_requires_separate_acceptance_header():
    opener = FakeOpener()
    client = SharedSocialClient(loader, opener=opener)
    value = client.publish(
        binding_id='leopardcat-tarot:threads:42',
        target_account_id='42',
        primary_text='short',
        text_attachment={'plaintext': 'full'},
        write_intent_id='intent-1',
        acceptance_id='acceptance-1',
    )
    assert value['ok'] is True
    request, _ = opener.requests[-1]
    assert request.get_header('X-agentos-acceptance-id') == 'acceptance-1'
    assert request.get_header('X-agentos-product-key') == 'PRODUCT-SECRET'


def test_missing_product_key_fails_closed_before_network():
    opener = FakeOpener()
    client = SharedSocialClient(lambda _name: None, opener=opener)
    try:
        client.begin_connect('/')
    except SharedSocialError as exc:
        assert exc.code == 'shared_social_product_not_configured'
        assert exc.status == 503
    else:
        raise AssertionError('expected SharedSocialError')
    assert opener.requests == []
