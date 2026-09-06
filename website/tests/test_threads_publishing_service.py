import json
import time

import pytest

from divination.threads_publishing import (
    THREADS_ATTACHMENT_LIMIT,
    THREADS_TEXT_LIMIT,
    ThreadsPublishingError,
    ThreadsPublishingService,
)


class FakeThreadsService(ThreadsPublishingService):
    def __init__(self, values):
        super().__init__(values.get)
        self.calls = []

    def _request_json(self, url, method='GET', token=None, body=None, timeout=15):
        self.calls.append({'url': url, 'method': method, 'token': token, 'body': body})
        if url.endswith('/oauth/access_token'):
            return {'access_token': 'short-secret', 'user_id': '42'}
        if '/access_token?' in url:
            return {'access_token': 'long-secret', 'expires_in': 5184000}
        if '/me?fields=' in url:
            return {'id': '42', 'username': 'milkcat', 'name': 'Milk Cat'}
        if '/me/threads?' in url:
            return {'id': 'post-123'}
        raise AssertionError(url)


def configured_values():
    return {
        'THREADS_APP_ID': 'app-id',
        'THREADS_APP_SECRET': 'app-secret',
        'THREADS_REDIRECT_URI': 'https://example.test/api/v1/threads/oauth/callback',
    }


def connect(service, session_id='sid'):
    auth_url = service.issue_authorization(session_id, '/?threads=return')
    state = auth_url.split('state=', 1)[1]
    state = state.split('&', 1)[0]
    service.complete_authorization(session_id, state, 'code-1')
    return session_id


def test_oauth_is_ephemeral_and_profile_only_is_exposed():
    service = FakeThreadsService(configured_values())
    sid = connect(service)
    status = service.status(sid)
    assert status == {
        'configured': True,
        'connected': True,
        'account': {'id': '42', 'username': 'milkcat', 'name': 'Milk Cat'},
    }
    assert 'access_token' not in json.dumps(status)
    service.disconnect(sid)
    assert service.status(sid)['connected'] is False


def test_oauth_state_is_bound_to_browser_session():
    service = FakeThreadsService(configured_values())
    auth_url = service.issue_authorization('sid-a')
    state = auth_url.split('state=', 1)[1].split('&', 1)[0]
    with pytest.raises(ThreadsPublishingError) as exc:
        service.complete_authorization('sid-b', state, 'code')
    assert exc.value.code == 'threads_oauth_state_invalid'


def test_publish_uses_bearer_server_side_and_text_attachment():
    service = FakeThreadsService(configured_values())
    sid = connect(service)
    result = service.publish_text(
        sid,
        '短主文',
        {'plaintext': '完整大師解讀', 'link_attachment_url': 'https://example.test/reading'},
    )
    assert result['id'] == 'post-123'
    publish_call = service.calls[-1]
    assert publish_call['method'] == 'POST'
    assert publish_call['token'] == 'long-secret'
    assert 'access_token=' not in publish_call['url']
    assert 'text_attachment=' in publish_call['url']
    assert 'short-secret' not in publish_call['url']
    assert 'long-secret' not in publish_call['url']


def test_publish_contract_rejects_overlong_primary_and_attachment():
    service = FakeThreadsService(configured_values())
    sid = connect(service)
    with pytest.raises(ThreadsPublishingError) as exc:
        service.publish_text(sid, 'x' * (THREADS_TEXT_LIMIT + 1), None)
    assert exc.value.code == 'threads_primary_text_invalid'
    with pytest.raises(ThreadsPublishingError) as exc:
        service.publish_text(sid, 'ok', {'plaintext': 'x' * (THREADS_ATTACHMENT_LIMIT + 1)})
    assert exc.value.code == 'threads_text_attachment_invalid'


def test_unconfigured_service_fails_closed():
    service = FakeThreadsService({})
    assert service.status('sid') == {'configured': False, 'connected': False, 'account': None}
    with pytest.raises(ThreadsPublishingError) as exc:
        service.issue_authorization('sid')
    assert exc.value.status == 503
