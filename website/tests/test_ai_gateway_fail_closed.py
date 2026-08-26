import json
import urllib.error

import pytest

from divination.ai_gateway import AIUnavailable, ZeroCostGeminiGateway


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode('utf-8')


def gateway():
    return ZeroCostGeminiGateway('test-free-tier-key')


def test_valid_provider_text_is_returned(monkeypatch):
    monkeypatch.setattr(
        'urllib.request.urlopen',
        lambda *args, **kwargs: FakeResponse({'candidates': [{'content': {'parts': [{'text': '可用解讀'}]}}]}),
    )
    assert gateway().generate('prompt') == '可用解讀'


@pytest.mark.parametrize(
    'payload, expected_code',
    [
        ({'candidates': [{'content': {}}]}, 'empty_response'),
        ({'candidates': [{'content': {'parts': []}}]}, 'empty_response'),
        ({'candidates': []}, 'empty_response'),
        ({'candidates': [{'finishReason': 'SAFETY'}]}, 'empty_response'),
        ({'unexpected': True}, 'empty_response'),
    ],
)
def test_empty_or_malformed_success_payload_fails_closed(monkeypatch, payload, expected_code):
    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: FakeResponse(payload))
    with pytest.raises(AIUnavailable) as exc:
        gateway().generate('prompt')
    assert exc.value.code == expected_code
    assert exc.value.retryable is True


def test_invalid_json_fails_closed(monkeypatch):
    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: FakeResponse(b'not-json'))
    with pytest.raises(AIUnavailable) as exc:
        gateway().generate('prompt')
    assert exc.value.code == 'invalid_response'


def test_provider_network_error_fails_closed(monkeypatch):
    def fail(*args, **kwargs):
        raise urllib.error.URLError('network down')

    monkeypatch.setattr('urllib.request.urlopen', fail)
    with pytest.raises(AIUnavailable) as exc:
        gateway().generate('prompt')
    assert exc.value.code == 'provider_network'
    assert exc.value.retryable is True
