from pathlib import Path

root=Path(__file__).resolve().parents[1]

# creator history UI
p=root/'website/public/create.html'
s=p.read_text(encoding='utf-8')
anchor='''  <section class="card">\n    <h2>1. 這副牌叫什麼？</h2>'''
history='''  <section class="card" id="published-history-card">\n    <h2>我發布的牌組</h2>\n    <p class="muted">這裡只記在你目前這個瀏覽器，不會公開列出所有人的牌組。之後忘記網址，可以回到這頁找。</p>\n    <div id="published-history"></div>\n  </section>\n\n'''
if 'id="published-history-card"' not in s:
    s=s.replace(anchor, history+anchor,1)
p.write_text(s,encoding='utf-8')

p=root/'website/public/creator.js'
s=p.read_text(encoding='utf-8')
needle="  let cards = [];\n"
insert=r'''  const HISTORY_KEY = 'leopardcat-published-decks-v1';

  function getPublishedHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); }
    catch (_) { return []; }
  }

  function savePublishedHistory(entry) {
    const rows = getPublishedHistory().filter(x => x.deck_id !== entry.deck_id);
    rows.unshift(entry);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(rows.slice(0, 50)));
    renderPublishedHistory();
  }

  function renderPublishedHistory() {
    const el = document.getElementById('published-history');
    if (!el) return;
    const rows = getPublishedHistory();
    if (!rows.length) {
      el.innerHTML = '<p class="muted">這個瀏覽器還沒有發布紀錄。</p>';
      return;
    }
    el.innerHTML = rows.map(x => {
      const when = x.published_at ? new Date(x.published_at).toLocaleString('zh-TW') : '';
      return `<div style="padding:10px 0;border-top:1px solid #eee3d4"><strong>${escapeHtml(x.name || x.deck_id)}</strong><div class="muted">${escapeHtml(when)}</div><a href="${escapeHtml(x.url)}" target="_blank">開啟占卜頁</a></div>`;
    }).join('');
  }
'''
if 'leopardcat-published-decks-v1' not in s:
    s=s.replace(needle,needle+insert,1)

old="""      const link = document.getElementById('share-link');\n      link.href = url; link.textContent = url;\n      done.classList.remove('hidden');"""
new="""      const link = document.getElementById('share-link');\n      link.href = url; link.textContent = url;\n      savePublishedHistory({ deck_id: data.deck_id, name: data.name || name, theme_id: selectedThemeId, url, published_at: new Date().toISOString() });\n      done.classList.remove('hidden');"""
s=s.replace(old,new,1)
if 'renderPublishedHistory();\n})();' not in s:
    s=s.replace('})();','  renderPublishedHistory();\n})();',1)
p.write_text(s,encoding='utf-8')

# card back scroll + explicit flip-back button
p=root/'website/main.js'
s=p.read_text(encoding='utf-8')
s=s.replace('''                <div class="back-content">\n                    <h3>${title}</h3>''','''                <div class="back-content" tabindex="0" aria-label="${title} 牌義，可上下捲動">\n                    <button class="card-flip-back" type="button" aria-label="翻回牌面">↩ 翻回牌面</button>\n                    <h3>${title}</h3>''',1)
old='''    if (scrollableContent) {\n        scrollableContent.addEventListener('touchstart', (e) => e.stopPropagation(), { passive: true });\n        scrollableContent.addEventListener('touchend', (e) => e.stopPropagation(), { passive: true });\n    }'''
new='''    if (scrollableContent) {\n        scrollableContent.addEventListener('touchstart', (e) => e.stopPropagation(), { passive: true });\n        scrollableContent.addEventListener('touchend', (e) => e.stopPropagation(), { passive: true });\n        scrollableContent.addEventListener('wheel', (e) => e.stopPropagation(), { passive: true });\n        scrollableContent.addEventListener('click', (e) => e.stopPropagation());\n        const flipBack = scrollableContent.querySelector('.card-flip-back');\n        flipBack?.addEventListener('click', (e) => { e.stopPropagation(); cardInner.classList.remove('is-flipped'); });\n    }'''
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

p=root/'website/style.css'
s=p.read_text(encoding='utf-8')
append=r'''
/* Long card meanings: keep the back readable and independently scrollable. */
.card-back { min-height: 0; }
.back-content {
  flex: 1 1 auto;
  min-height: 0;
  max-height: 100%;
  overflow-y: auto !important;
  overflow-x: hidden;
  cursor: auto;
  touch-action: pan-y;
  scrollbar-gutter: stable;
  padding-bottom: 18px;
}
.card-flip-back {
  position: sticky;
  top: 0;
  z-index: 20;
  align-self: flex-end;
  border: 1px solid rgba(212,175,55,.45);
  background: rgba(3,5,4,.88);
  color: var(--color-gold);
  border-radius: 999px;
  padding: 5px 10px;
  font: inherit;
  font-size: .72rem;
  cursor: pointer;
  backdrop-filter: blur(8px);
}
.card.is-flipped:hover { transform: rotateY(180deg); }
'''
if 'Long card meanings:' not in s:
    s += append
p.write_text(s,encoding='utf-8')
print('published_history_scroll_patch=applied')
