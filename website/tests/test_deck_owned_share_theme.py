from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_share_theme_is_deck_owned_and_has_neutral_fallback():
    main = (ROOT / "main.js").read_text(encoding="utf-8")
    assert "function normalizeShareTheme(shareContext)" in main
    assert "deck.share_theme" in main
    assert "source: hasExplicit ? 'deck'" in main
    assert "'theme-derived' : 'neutral'" in main
    assert "applyShareTheme(template, shareContext)" in main
    assert "backgroundColor: shareTheme.background" in main
    assert "window.brandText('share_title', uiCommon.share_memo_title)" not in main


def test_share_theme_is_public_sanitized_deck_metadata():
    decks = (ROOT / "divination" / "decks.py").read_text(encoding="utf-8")
    publishing = (ROOT / "divination" / "publishing.py").read_text(encoding="utf-8")
    assert "share_theme: dict[str, Any] | None = None" in decks
    assert '"share_theme": d.share_theme or {}' in decks
    assert "_SHARE_THEME_FIELDS" in publishing
    assert "_clean_share_theme" in publishing
    assert '"share_theme": share_theme' in publishing


def test_share_css_uses_runtime_share_tokens():
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    assert "--share-bg" in css
    assert "background: var(--share-bg)" in css
    assert "border-color: var(--share-accent)" in css


def test_capability_is_protected():
    governance = (ROOT.parent / "governance" / "capabilities.json").read_text(encoding="utf-8")
    assert '"sharing.deck-owned-share-theme"' in governance
