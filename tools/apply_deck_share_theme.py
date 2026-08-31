from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing anchor: {label}")
    return text.replace(old, new, 1)


main = Path("website/main.js")
s = main.read_text(encoding="utf-8")
render_block = """function renderShareCards(frame, shareContext) {
    const entries = shareContext.cards;
    frame.classList.toggle('share-three-card', entries.length > 1);
    frame.innerHTML = '';
    entries.forEach((entry, index) => {
        const slot = document.createElement('div');
        slot.className = 'share-card-slot';
        const img = document.createElement('img');
        if (index === 0) img.id = 'share-card-img'; // compatibility for older selectors/tests
        img.className = 'share-card-image';
        img.src = getShareCardImage(entry.card, shareContext.deckId);
        img.alt = getShareCardTitle(entry.card);
        img.style.transform = entry.orientation === 'reversed' ? 'rotate(180deg)' : '';
        slot.appendChild(img);
        const caption = document.createElement('div');
        caption.className = 'share-card-caption';
        const position = entry.position_label || entry.position;
        const orientation = entry.orientation === 'reversed' ? uiText('orientation_reversed', 'Reversed') : uiText('orientation_upright', 'Upright');
        caption.textContent = `${position ? position + ' · ' : ''}${getShareCardTitle(entry.card)} · ${orientation}`;
        slot.appendChild(caption);
        frame.appendChild(slot);
    });
}
"""
addition = r'''

function readThemeToken(name, fallback) {
    try {
        const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return value || fallback;
    } catch (_) {
        return fallback;
    }
}

function normalizeShareTheme(shareContext) {
    const deck = shareContext?.deck || {};
    const deckId = shareContext?.deckId || deck.deck_id || window.activeDeckId || 'leopardcat';
    const explicit = (deck.share_theme && typeof deck.share_theme === 'object') ? deck.share_theme : {};
    const hasExplicit = Object.keys(explicit).length > 0;
    const hasDeckTheme = Boolean(deck.default_theme || deck.theme_id || window.currentReadingState?.theme_id || window.activeThemeId);
    const isLeopardCat = deckId === 'leopardcat';
    const neutral = {
        background: '#171717', surface: 'rgba(255,255,255,.055)', accent: '#d7d2c8',
        text: '#f5f2ec', muted: 'rgba(245,242,236,.74)', line: 'rgba(215,210,200,.28)'
    };
    const themed = {
        background: readThemeToken('--color-bg', '#0a110e'),
        surface: readThemeToken('--color-card-bg', 'rgba(212,175,55,.05)'),
        accent: readThemeToken('--color-gold', '#d4af37'),
        text: readThemeToken('--color-text', '#ffffff'),
        muted: readThemeToken('--color-text-muted', 'rgba(244,241,234,.82)'),
        line: readThemeToken('--color-gold-glow', 'rgba(212,175,55,.28)')
    };
    const base = (isLeopardCat || hasDeckTheme) ? themed : neutral;
    const title = String(explicit.title || deck.name || (isLeopardCat ? window.brandText('share_title', '靈山靈貓 · 石虎塔羅') : 'Tarot Reading'));
    const siteTag = String(explicit.site_tag || (isLeopardCat ? window.brandText('share_site_tag', location.host) : location.host));
    return {
        source: hasExplicit ? 'deck' : ((isLeopardCat || hasDeckTheme) ? 'theme-derived' : 'neutral'),
        layout: String(explicit.layout || (isLeopardCat ? 'spirit-memo' : 'deck-memo')),
        title, site_tag: siteTag,
        background: String(explicit.background || base.background),
        surface: String(explicit.surface || base.surface),
        accent: String(explicit.accent || base.accent),
        text: String(explicit.text || base.text),
        muted: String(explicit.muted || base.muted),
        line: String(explicit.line || base.line)
    };
}

function applyShareTheme(template, shareContext) {
    const theme = normalizeShareTheme(shareContext);
    template.dataset.shareThemeSource = theme.source;
    template.dataset.shareLayout = theme.layout;
    template.style.setProperty('--share-bg', theme.background);
    template.style.setProperty('--share-surface', theme.surface);
    template.style.setProperty('--share-accent', theme.accent);
    template.style.setProperty('--share-text', theme.text);
    template.style.setProperty('--share-muted', theme.muted);
    template.style.setProperty('--share-line', theme.line);
    const memo = template.querySelector('#share-memo-title');
    const site = template.querySelector('#share-site-tag');
    if (memo) memo.textContent = theme.title;
    if (site) site.textContent = theme.site_tag;
    return theme;
}
'''
s = replace_once(s, render_block, render_block + addition, "share theme functions")
s = replace_once(
    s,
    """    const shareFrame = template.querySelector('.share-card-frame');
    renderShareCards(shareFrame, shareContext);
    const titleParts = shareEntries.map(entry => getShareCardTitle(entry.card));
""",
    """    const shareFrame = template.querySelector('.share-card-frame');
    renderShareCards(shareFrame, shareContext);
    const shareTheme = applyShareTheme(template, shareContext);
    const titleParts = shareEntries.map(entry => getShareCardTitle(entry.card));
""",
    "apply share theme",
)
s = replace_once(s, "backgroundColor: '#0a0f0d',", "backgroundColor: shareTheme.background,", "html2canvas background")
s = replace_once(
    s,
    """        document.getElementById('share-memo-title').innerText = window.brandText('share_title', uiCommon.share_memo_title);
        document.getElementById('share-seeker-label').innerText = uiCommon.share_seeker_label;
        document.getElementById('share-site-tag').innerText = window.brandText('share_site_tag', uiCommon.share_site_tag);
""",
    """        applyShareTheme(template, shareContext); // locale refresh must not restore LeopardCat branding.
        document.getElementById('share-seeker-label').innerText = uiCommon.share_seeker_label;
""",
    "late share labels",
)
main.write_text(s, encoding="utf-8")


decks = Path("website/divination/decks.py")
d = decks.read_text(encoding="utf-8")
d = replace_once(d, '    card_back: str = "/art/card-back.svg"\n', '    card_back: str = "/art/card-back.svg"\n    share_theme: dict[str, Any] | None = None\n', "deck dataclass")
d = replace_once(
    d,
    '''                "leopardcat",
                "/art/card-back.svg",
            )
''',
    '''                "leopardcat",
                "/art/card-back.svg",
                {
                    "layout": "spirit-memo",
                    "title": "靈山靈貓 · 石虎塔羅",
                    "site_tag": "leopardcat-tarot.milkcat.org",
                    "background": "#0a110e",
                    "accent": "#d4af37",
                },
            )
''',
    "builtin share theme",
)
d = replace_once(
    d,
    '''            card_back=str(data.get("card_back") or "/art/card-back.svg"),
        )
''',
    '''            card_back=str(data.get("card_back") or "/art/card-back.svg"),
            share_theme=data.get("share_theme") if isinstance(data.get("share_theme"), dict) else None,
        )
''',
    "custom share theme",
)
d = replace_once(d, '            "card_back": d.card_back,\n', '            "card_back": d.card_back,\n            "share_theme": d.share_theme or {},\n', "public share theme")
decks.write_text(d, encoding="utf-8")


pub = Path("website/divination/publishing.py")
p = pub.read_text(encoding="utf-8")
helper = '''def _clean_text(value: Any, max_len: int) -> str:
    text = str(value or "").replace("\\x00", " ")
    text = re.sub(r"[<>]", "", text)
    text = re.sub(r"[\\t\\r]+", " ", text)
    return text.strip()[:max_len]
'''
helper2 = helper + '''

_SHARE_THEME_FIELDS = {
    "layout": 32, "title": 120, "site_tag": 120,
    "background": 80, "surface": 80, "accent": 80,
    "text": 80, "muted": 80, "line": 80,
}


def _clean_share_theme(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    cleaned: dict[str, str] = {}
    for key, max_len in _SHARE_THEME_FIELDS.items():
        if key in value:
            item = _clean_text(value.get(key), max_len)
            if item:
                cleaned[key] = item
    return cleaned
'''
p = replace_once(p, helper, helper2, "share theme sanitizer")
p = replace_once(p, '        default_theme = _clean_text(payload.get("theme"), 64).lower() or "minimal-light"\n', '        default_theme = _clean_text(payload.get("theme"), 64).lower() or "minimal-light"\n        share_theme = _clean_share_theme(payload.get("share_theme"))\n', "publish share theme")
p = replace_once(p, '                "default_theme": default_theme,\n                "card_count": len(saved_cards),\n', '                "default_theme": default_theme,\n                "share_theme": share_theme,\n                "card_count": len(saved_cards),\n', "manifest share theme")
p = replace_once(p, '            "default_theme": default_theme,\n            "share_path":', '            "default_theme": default_theme,\n            "share_theme": share_theme,\n            "share_path":', "publish response")
p = replace_once(p, '            "default_theme": data.get("default_theme", "minimal-light"),\n            "reversals":', '            "default_theme": data.get("default_theme", "minimal-light"),\n            "share_theme": data.get("share_theme") if isinstance(data.get("share_theme"), dict) else {},\n            "reversals":', "management info")
update = '''        if "theme" in payload:
            theme = _clean_text(payload.get("theme"), 64).lower()
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", theme):
                raise DivinationError("無效的牌組主題")
            data["default_theme"] = theme
'''
p = replace_once(p, update, update + '''        if "share_theme" in payload:
            data["share_theme"] = _clean_share_theme(payload.get("share_theme"))
''', "update share theme")
pub.write_text(p, encoding="utf-8")


css = Path("website/style.css")
c = css.read_text(encoding="utf-8")
c += r'''

/* Share surface is owned by the active Deck/Theme contract, not LeopardCat globals. */
.share-card-body {
  --share-bg: #171717;
  --share-surface: rgba(255,255,255,.055);
  --share-accent: #d7d2c8;
  --share-text: #f5f2ec;
  --share-muted: rgba(245,242,236,.74);
  --share-line: rgba(215,210,200,.28);
  background: var(--share-bg);
  border-color: var(--share-accent);
  color: var(--share-text);
}
.share-card-body .share-header,
.share-card-body .share-footer { border-color: var(--share-line); }
.share-card-body .share-logo,
.share-card-body .share-info h2,
.share-card-body .quote-mark,
.share-card-body .share-seeker .label { color: var(--share-accent); }
.share-card-body .share-card-frame { background: var(--share-surface); border-color: var(--share-line); }
.share-card-body .share-card-caption { color: var(--share-muted); }
.share-card-body[data-share-layout="deck-memo"] .share-logo { letter-spacing: .04em; }
'''
css.write_text(c, encoding="utf-8")


cap = Path("governance/capabilities.json")
g = cap.read_text(encoding="utf-8")
block = '''    "sharing.deck-owned-share-theme": {
      "status": "protected",
      "owner": "website",
      "contract": [
        "Share-card branding, palette, and layout are resolved from the active Deck Module/share_theme or its active Theme instead of a global LeopardCat template.",
        "Custom decks without an explicit share_theme derive the share surface from their active theme; decks without either use a neutral platform fallback, never LeopardCat branding.",
        "Deck public metadata may expose a sanitized share_theme contract without executable HTML/CSS or arbitrary fields.",
        "Deck-driven card faces, spread order, positions, and upright/reversed orientation remain unchanged."
      ],
      "evidence": [
        "website/main.js",
        "website/style.css",
        "website/divination/decks.py",
        "website/divination/publishing.py",
        "website/tests/test_deck_owned_share_theme.py"
      ]
    },
'''
g = replace_once(g, '    "sharing.reading-receipt-reload": {', block + '    "sharing.reading-receipt-reload": {', "capability")
cap.write_text(g, encoding="utf-8")


test = Path("website/tests/test_deck_owned_share_theme.py")
test.write_text(r'''from pathlib import Path

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
''', encoding="utf-8")
