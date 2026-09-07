import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from divination.threads_publishing import ThreadsPublishingError, ThreadsPublishingService


class FakeShared:
    def __init__(self):
        self.calls = []
        self.connection_id = 'connection-1'
        self.binding_id = 'leopardcat-tarot:threads:42'

    def enabled(self):
        return True

    def provider_status(self):
        self.calls.append(('provider_status',))
        return {'configured': True, 'shared_runtime': True}

    def begin_connect(self, return_to='/'):
        self.calls.append(('begin_connect', return_to))
        return {
            'schema': 'agentos.social-browser-handoff/v1',
            'connection_id': self.connection_id,
            'browser_start_url': 'https://studio.milkcat.org/dashboard/api/social/v1/social/oauth/threads/start?ticket=opaque',
            'expires_in': 300,
        }

    def status(self, binding_id=None, connection_id=None):
        self.calls.append(('status', binding_id, connection_id))
        if connection_id:
            assert connection_id == self.connection_id
            return {
                'schema': 'agentos.social-connection-result/v1',
                'connected': True,
                'binding_id': self.binding_id,
                'account': {'provider_account_id': '42', 'username': 'milkcat'},
            }
        if binding_id:
            assert binding_id == self.binding_id
            return {
                'schema': 'agentos.social-status/v1',
                'configured': True,
                'connected': True,
                'account': {
                    'binding_id': self.binding_id,
                    'provider_account_id': '42',
                    'username': 'milkcat',
                },
            }
        return {'configured': True, 'connected': False, 'account': None}


def service():
    values = {
        'AGENTOS_SOCIAL_PRODUCT_KEY': 'server-only-product-key',
        # Direct provider values intentionally absent.
        'THREADS_APP_ID': None,
        'THREADS_APP_SECRET': None,
        'THREADS_REDIRECT_URI': None,
    }
    value = ThreadsPublishingService(values.get)
    value._shared = FakeShared()
    return value


def shared_connect(value, session_id='sid', return_to='/?reading=1'):
    browser_url = value.issue_authorization(session_id, return_to)
    assert browser_url.endswith('ticket=opaque')
    begin = next(call for call in value._shared.calls if call[0] == 'begin_connect')
    callback = begin[1]
    assert callback.startswith('/api/v1/threads/oauth/callback?')
    assert 'shared=1' in callback
    local_state = callback.split('state=', 1)[1].split('&', 1)[0]
    return value.complete_authorization(session_id, local_state, '')


def test_shared_oauth_works_without_product_meta_credentials():
    value = service()
    assert value.configured() is True
    result = shared_connect(value)
    assert result['return_to'] == '/?reading=1'
    assert result['account'] == {'id': '42', 'username': 'milkcat', 'name': ''}
    status = value.status('sid')
    assert status == {
        'configured': True,
        'connected': True,
        'account': {'id': '42', 'username': 'milkcat', 'name': ''},
    }
    text = repr(value._states) + repr(value._sessions)
    assert 'access_token' not in text
    assert 'app-secret' not in text


def test_shared_completion_is_bound_to_local_browser_session():
    value = service()
    value.issue_authorization('sid-a', '/')
    callback = next(call for call in value._shared.calls if call[0] == 'begin_connect')[1]
    local_state = callback.split('state=', 1)[1].split('&', 1)[0]
    with pytest.raises(ThreadsPublishingError) as exc:
        value.complete_authorization('sid-b', local_state, '')
    assert exc.value.code == 'threads_oauth_state_invalid'


def test_shared_publish_does_not_bypass_core_write_governance():
    value = service()
    shared_connect(value)
    with pytest.raises(ThreadsPublishingError) as exc:
        value.publish_text('sid', 'short', {'plaintext': 'full interpretation'})
    assert exc.value.code == 'threads_publish_governance_pending'
    assert exc.value.status == 503


def test_shared_disconnect_does_not_fake_remote_revocation():
    value = service()
    shared_connect(value)
    with pytest.raises(ThreadsPublishingError) as exc:
        value.disconnect('sid')
    assert exc.value.code == 'threads_disconnect_governance_pending'
    assert value.status('sid')['connected'] is True
