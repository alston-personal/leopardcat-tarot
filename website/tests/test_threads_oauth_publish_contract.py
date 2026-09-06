from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / 'main.js').read_text(encoding='utf-8')
SERVER = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')
SERVICE = (ROOT / 'divination' / 'threads_publishing.py').read_text(encoding='utf-8')


def test_browser_never_receives_threads_secret_or_token():
    assert 'THREADS_APP_SECRET' not in MAIN
    assert 'access_token' not in MAIN
    assert "fetch('/api/v1/threads/oauth/status'" in MAIN
    assert "fetch('/api/v1/threads/publish'" in MAIN
    assert "credentials: 'same-origin'" in MAIN


def test_long_share_connects_then_publishes_typed_attachment():
    assert '/api/v1/threads/oauth/start?return_to=' in MAIN
    assert 'primary_text: plan.primaryText' in MAIN
    assert 'text_attachment: plan.textAttachment' in MAIN
    assert 'navigator.clipboard.writeText(plan.text)' not in MAIN


def test_server_owns_oauth_and_publish_capability():
    for route in (
        '/api/v1/threads/oauth/status',
        '/api/v1/threads/oauth/start',
        '/api/v1/threads/oauth/callback',
        '/api/v1/threads/oauth/disconnect',
        '/api/v1/threads/publish',
    ):
        assert route in SERVER
    assert 'ThreadsPublishingService(load_env_value)' in SERVER
    assert 'HttpOnly; Secure; SameSite=Lax' in SERVER


def test_tokens_are_ephemeral_and_server_only():
    assert 'intentionally not persisted' in SERVICE
    assert "self._sessions = {}" in SERVICE
    assert "headers['Authorization'] = f'Bearer {token}'" in SERVICE
    assert "'THREADS_APP_SECRET'" in SERVICE
