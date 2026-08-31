from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_share_png_is_session_authorized_and_public_read_is_share_token_authorized():
    server = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')
    assert "SESSION_STORE.get(reading_id, str(payload.get('session_token') or ''))" in server
    assert "SESSION_STORE.get_shared(reading_id, share_token)" in server
    assert "share-image.png?shareToken=" in server
    assert "data:image/png;base64" in server


def test_reading_og_uses_persisted_deck_owned_share_card_without_private_text():
    server = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')
    assert "shared_reading = SESSION_STORE.get_shared(reading_id, share_token)" in server
    assert "meta_img_type = 'image/png'" in server
    assert "meta_img_width, meta_img_height = 1200, 630" in server
    og_section = server[server.index('# 🔮 Dynamic SEO / Open Graph Injection'):server.index('super().do_GET()')]
    assert 'question' not in og_section.lower()
    assert "shared_reading.get('reading')" not in og_section


def test_browser_uploads_rendered_png_before_social_share():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    assert 'async function persistReadingSharePreview(blob)' in js
    assert "body: JSON.stringify({session_token: envelope.session_token, image})" in js
    assert "await persistReadingSharePreview(ogBlob);" in js
    assert js.index('await persistReadingSharePreview(ogBlob);') < js.index('navigator.share({', js.index('await persistReadingSharePreview(ogBlob);'))


def test_threads_share_busts_social_preview_cache_without_changing_reading_identity():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    assert "threadsShareU.searchParams.set('preview', String(Date.now()))" in js
    assert "new URL(shareUrl)" in js
    assert "shareU.searchParams.set('reading'" in js
    assert "shareU.searchParams.set('share'" in js
