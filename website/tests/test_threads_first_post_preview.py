from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.js").read_text(encoding="utf-8")

def test_threads_long_share_keeps_reading_url_in_first_post():
    assert "fitThreadsLeadWithUrls" in MAIN
    assert "firstPost" in MAIN
    assert "window._threadsShareUrl" in MAIN
    assert "threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(plan.firstPost || threadsText)}`" in MAIN

def test_threads_long_share_only_copies_remainder():
    assert "navigator.clipboard.writeText(plan.remainderText)" in MAIN
    assert "navigator.clipboard.writeText(plan.text)" not in MAIN
    assert "第一則已帶入塔羅圖卡連結" in MAIN

def test_threads_first_post_preserves_source_and_master_headings():
    assert "share_threads_question_heading" in MAIN
    assert "share_source_heading" in MAIN
    assert "share_master_heading" in MAIN
    assert "readingUrl" in MAIN
