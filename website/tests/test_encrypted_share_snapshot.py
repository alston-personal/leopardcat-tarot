from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'share_snapshot.js').read_text(encoding='utf-8')
VITE = (ROOT / 'vite.config.js').read_text(encoding='utf-8')
MAIN = (ROOT / 'main.js').read_text(encoding='utf-8')


def test_runtime_is_injected_without_replacing_main_entrypoint():
    assert "src: '/share_snapshot.js'" in VITE
    assert "type: 'module'" in VITE
    assert 'main.js' in (ROOT / 'index.html').read_text(encoding='utf-8')


def test_snapshot_uses_browser_side_authenticated_encryption():
    assert "AES-GCM" in JS
    assert "crypto.subtle.generateKey" in JS
    assert "crypto.subtle.encrypt" in JS
    assert "crypto.subtle.decrypt" in JS


def test_decryption_material_stays_in_url_fragment():
    assert "u.hash = params.toString()" in JS
    assert "location.hash" in JS
    assert "searchParams.set('lcshare'" not in JS
    assert "SNAPSHOT_HASH_KEY = 'lcshare'" in JS


def test_private_content_is_explicitly_mode_gated():
    for mode in ("cards", "question", "highlight", "full"):
        assert f'value="{mode}"' in JS
    assert "mode === 'full' ? answer : null" in JS
    assert "includeQuestion ? editablePublicQuestion() : null" in JS


def test_share_snapshot_freezes_canonical_card_state():
    assert "window.currentReadingState" in JS
    assert "card_id" in JS
    assert "orientation" in JS
    assert "position_label" in JS
    assert "spread:" in JS


def test_snapshot_has_expiry_and_no_server_persistence_endpoint():
    assert "expires_at" in JS
    assert "snapshot_expired" in JS
    assert "/api/v1/share-snapshots" not in JS


def test_existing_symbolic_share_link_remains_as_base_fallback():
    # The new layer wraps the existing reading/share deep-link instead of replacing
    # canonical symbolic restore or putting private plaintext into query params.
    assert "shareU.searchParams.set('reading'" in MAIN
    assert "shareU.searchParams.set('share'" in MAIN
    assert "bestBaseShareUrl" in JS


if __name__ == '__main__':
    tests = [value for name, value in sorted(globals().items()) if name.startswith('test_') and callable(value)]
    for test in tests:
        test()
    print(f'encrypted_share_snapshot_tests=PASS count={len(tests)}')
