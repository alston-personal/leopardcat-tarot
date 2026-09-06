from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'main.js').read_text(encoding='utf-8')


def test_threads_author_uses_metadata_and_url_handle_fallback():
    assert 'function threadsSourceAuthorLabel(source)' in JS
    assert "author.display_name || author.name || source.author_name || source.display_name" in JS
    assert "pathname.match(/^\\/@([^/]+)\\/post\\//i)" in JS
    assert "share_threads_question_heading_with_author" in JS


def test_long_threads_intent_is_bounded_and_never_manual_clipboard_fallback():
    assert 'function buildThreadsPrimaryPost(text, limit = THREADS_TEXT_LIMIT)' in JS
    assert 'requiresTextAttachment: isLong' in JS
    assert 'window.pendingThreadsTextAttachment = plan.textAttachment;' in JS
    assert "encodeURIComponent(plan.primaryText)" in JS
    block = JS[JS.index('window.prepareThreadsShare = async function'):JS.index('function refreshSocialShareText')]
    assert 'navigator.clipboard.writeText(plan.text)' not in block
    assert "threads_long_share_copied" not in block


def test_all_threads_intent_writers_use_bounded_primary_text():
    assert JS.count('buildThreadsPrimaryPost(') >= 4
    assert "encodeURIComponent(threadsShareText)}`" not in JS
    assert "encodeURIComponent(buildSocialShareText(lastShareBaseMessage, u.toString()))}`" not in JS
