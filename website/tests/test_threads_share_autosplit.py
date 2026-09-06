from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / 'main.js').read_text(encoding='utf-8')
SERVER = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')


def test_threads_share_short_url_is_accepted_and_canonicalized():
    assert "share\\/[A-Za-z0-9_-]+" in MAIN
    assert 'canonicalize_threads_source_url' in SERVER
    assert 'THREADS_SHARE_PATH_RE' in SERVER
    assert 'ThreadsSafeRedirectHandler' in SERVER
    assert 'threads_redirect_not_allowed' in SERVER
    assert "data=json.dumps({'url': source_url})" in SERVER


def test_threads_long_share_uses_bounded_intent_and_typed_text_attachment():
    assert 'THREADS_TEXT_LIMIT = 500' in MAIN
    assert 'function splitThreadsText' in MAIN
    assert 'function threadsSharePlan' in MAIN
    assert 'function buildThreadsPrimaryPost' in MAIN
    assert 'requiresTextAttachment: isLong' in MAIN
    assert 'window.pendingThreadsTextAttachment = plan.textAttachment' in MAIN
    assert 'navigator.clipboard.writeText(plan.text)' not in MAIN
    assert 'threads_long_share_copied' not in MAIN
    assert 'threadsLink.onclick = window.prepareThreadsShare' in MAIN
    assert "document.getElementById('share-threads').onclick = window.prepareThreadsShare" in MAIN


def test_modular_reading_language_follows_question():
    block = MAIN[MAIN.index('window.getModularReading'):MAIN.index('window.getAIReading')]
    assert block.count('lang: getQuestionLanguageTag(q)') >= 2
    assert 'lang: getAILanguageTag()' not in block
    assert 'lang: getQuestionLanguageTag(text)' in MAIN
