from pathlib import Path

path = Path('website/main.js')
s = path.read_text(encoding='utf-8')
old = """window.updatePrimaryReadingLinks = function() {
    const u = new URL('/read.html', window.location.origin);
    if (window.activeDeckId) u.searchParams.set('deck', window.activeDeckId);
    if (window.activePersonaId) u.searchParams.set('persona', window.activePersonaId);
    document.querySelectorAll('[data-primary-reading]').forEach(el => { el.href = u.toString(); });
};
"""
new = """window.updatePrimaryReadingLinks = function() {
    // Tarot's primary experience stays inside the active deck page. The focused
    // /read.html surface remains available for other methods or explicit entry,
    // but “開始占卜／詢問大師” must not feel like leaving the deck's website.
    document.querySelectorAll('[data-primary-reading]').forEach(el => {
        el.setAttribute('href', '#fortune');
    });
};
"""
if new in s:
    print('primary-reading patch already applied')
elif old in s:
    path.write_text(s.replace(old, new, 1), encoding='utf-8')
    print('primary-reading patch applied')
else:
    raise SystemExit('primary-reading anchor not found')
