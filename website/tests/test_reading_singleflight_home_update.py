from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_primary_reading_is_single_flight_and_has_immediate_busy_feedback():
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    assert "window.readingRequestState = { inFlight: false, clientRequestId: null }" in js
    assert 'if (state.inFlight) return false' in js
    assert 'if (!beginReadingRequest()) return' in js
    assert "btn.disabled = Boolean(busy)" in js
    assert "btn.setAttribute('aria-busy'" in js
    assert "clientRequestId: window.readingRequestState?.clientRequestId" in js
    assert 'id="btn-primary-draw"' in html

def test_server_rejects_same_initial_client_request_while_in_flight():
    src=(ROOT/'fortune_server.py').read_text(encoding='utf-8')
    assert 'READING_REQUESTS_IN_FLIGHT = {}' in src
    assert 'begin_reading_request(client_request_id)' in src
    assert "'reading_in_progress'" in src
    assert 'end_reading_request' in src

def test_home_screen_has_manual_reload_and_automatic_bundle_update_check():
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    server=(ROOT/'fortune_server.py').read_text(encoding='utf-8')
    assert 'id="standalone-refresh"' in html
    assert "navigator.standalone === true" in js
    assert 'async function checkForAppUpdate()' in js
    assert "cache: 'no-store'" in js
    assert "document.addEventListener('visibilitychange'" in js
    assert "location.replace(u.toString())" in js
    assert "'Cache-Control', 'no-cache, no-store, must-revalidate'" in server
    assert 'serviceWorker.register' not in js
