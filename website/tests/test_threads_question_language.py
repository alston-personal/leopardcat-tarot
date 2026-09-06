from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / 'website/main.js').read_text(encoding='utf-8')
SERVER = (ROOT / 'website/fortune_server.py').read_text(encoding='utf-8')
CAP = json.loads((ROOT / 'governance/capabilities.json').read_text(encoding='utf-8'))


def test_question_language_is_independent_from_ui_locale():
    assert 'function detectQuestionLanguage(text' in JS
    assert "/[ぁ-ゖァ-ヺー]/.test(value)" in JS
    assert "/[가-힣]/.test(value)" in JS
    assert "return 'zh-TW'" in JS
    assert "return 'ja'" in JS
    assert "return 'ko'" in JS
    assert "return 'es'" in JS
    assert "return 'en'" in JS
    assert JS.count('getQuestionLanguageTag(q)') >= 3
    assert 'getQuestionLanguageTag(text)' in JS


def test_threads_url_is_resolved_before_reading_and_raw_url_is_not_question():
    assert 'async function resolveQuestionInput(rawQuestion)' in JS
    assert "fetch('/api/v1/sources/threads'" in JS
    assert 'q = resolvedInput.question;' in JS
    assert 'window.currentQuestionSource = resolvedInput.source;' in JS
    assert "THREADS_POST_URL_RE" in JS


def test_threads_source_proxy_is_localhost_and_ssrf_restricted():
    assert "THREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'" in SERVER
    assert "if path == '/api/v1/sources/threads':" in SERVER
    assert "THREADS_ALLOWED_HOSTS = {'threads.com','www.threads.com','threads.net','www.threads.net'}" in SERVER
    assert "parsed.scheme != 'https'" in SERVER
    assert 'class ThreadsSafeRedirectHandler' in SERVER
    assert "(parsed.hostname or '').lower() not in THREADS_ALLOWED_HOSTS" in SERVER
    assert 'THREADS_CANONICAL_PATH_RE.fullmatch(final.path)' in SERVER
    assert 'canonicalize_threads_source_url(source_url)' in SERVER
    assert "THREADS_READER_URL.rstrip('/') + '/v1/threads/resolve'" in SERVER


def test_full_share_preserves_threads_original_url_and_separates_interpretation():
    assert "source?.type === 'threads'" in JS
    assert "share_threads_question_heading" in JS
    assert "source.url" in JS
    assert "share_source_heading" in JS
    assert "share_master_heading" in JS


def test_source_metadata_and_language_survive_same_tab_reload_only():
    assert 'question_source: window.currentQuestionSource' in JS
    assert 'question_language: window.currentQuestionLanguage' in JS
    assert 'window.currentQuestionSource = local ? (snapshot?.question_source || null) : null;' in JS
    assert 'window.currentQuestionLanguage = local ?' in JS


def test_governance_protects_both_capabilities():
    assert CAP['protected_capabilities']['reading.reply-language-follows-user']['status'] == 'protected'
    assert CAP['protected_capabilities']['reading.threads-public-source']['status'] == 'protected'
