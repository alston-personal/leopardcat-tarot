from pathlib import Path

html=Path('website/index.html')
js=Path('website/main.js')
h=html.read_text(encoding='utf-8')
h=h.replace('<a href="#fortune" data-i18n="nav.fortune">Fortune</a>','<a href="/read.html" data-primary-reading data-i18n="nav.fortune">Fortune</a>')
h=h.replace('<a href="#fortune" class="btn btn-gold" data-i18n="hero.cta_fortune">詢問大師</a>','<a href="/read.html" data-primary-reading class="btn btn-gold" data-i18n="hero.cta_fortune">開始占卜</a>')
html.write_text(h,encoding='utf-8')

s=js.read_text(encoding='utf-8')
anchor="window.defaultPersonaId = null;\n"
block="""window.defaultPersonaId = null;

window.updatePrimaryReadingLinks = function() {
    const u = new URL('/read.html', window.location.origin);
    if (window.activeDeckId) u.searchParams.set('deck', window.activeDeckId);
    if (window.activePersonaId) u.searchParams.set('persona', window.activePersonaId);
    document.querySelectorAll('[data-primary-reading]').forEach(el => { el.href = u.toString(); });
};
document.addEventListener('DOMContentLoaded', window.updatePrimaryReadingLinks);
"""
if block not in s:
    if anchor not in s: raise SystemExit('main state anchor missing')
    s=s.replace(anchor,block,1)
js.write_text(s,encoding='utf-8')
print('primary_reading_cta_patch=passed')
