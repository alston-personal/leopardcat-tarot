from pathlib import Path

html = Path('website/public/create.html')
js = Path('website/public/creator.js')

h = html.read_text(encoding='utf-8')
old = '      <p id="persona-create-status" class="muted" aria-live="polite"></p>\n'
new = old + '      <div id="persona-management" class="hidden" style="margin-top:12px;padding:12px;border-radius:12px;background:#fff7e8"><strong>請保存解牌師管理連結</strong><p class="muted">這是跨裝置找回與修改的唯一鑰匙，只顯示在你的瀏覽器。</p><a id="persona-manage-link" style="word-break:break-all"></a><br><button id="copy-persona-manage" type="button" class="btn secondary" style="margin-top:8px">複製管理連結</button></div>\n'
if new not in h:
    if old not in h: raise SystemExit('persona status anchor missing')
    h = h.replace(old, new, 1)

old = '    <button id="copy" class="btn secondary">複製網址</button>\n'
new = old + '    <div id="deck-management" style="margin-top:18px;padding:14px;border-radius:12px;background:#fff7e8"><strong>🔑 請另外保存管理連結</strong><p class="muted">公開占卜網址可以分享；管理連結不要公開。換手機或電腦時，只要開啟這條連結就能找回管理權。</p><p><a id="deck-manage-link" style="word-break:break-all"></a></p><button id="copy-deck-manage" type="button" class="btn secondary">複製管理連結</button></div>\n'
if new not in h:
    if old not in h: raise SystemExit('done copy anchor missing')
    h = h.replace(old, new, 1)
html.write_text(h, encoding='utf-8')

s = js.read_text(encoding='utf-8')
old = "  const HISTORY_KEY = 'leopardcat-published-decks-v1';\n"
new = old + "  const MANAGED_KEY = 'divination-managed-resources-v1';\n"
if new not in s:
    if old not in s: raise SystemExit('history key anchor missing')
    s = s.replace(old, new, 1)

old = "  function savePublishedHistory(entry) {\n"
helper = """  function managementUrl(data) {
    if (!data?.management_token || !data?.manage_path) return '';
    const u = new URL(data.manage_path, location.origin);
    u.hash = `token=${encodeURIComponent(data.management_token)}`;
    return u.href;
  }

  function saveManagedResource(entry) {
    try {
      const rows = JSON.parse(localStorage.getItem(MANAGED_KEY) || '[]').filter(x => !(x.type === entry.type && x.id === entry.id));
      rows.unshift(entry);
      localStorage.setItem(MANAGED_KEY, JSON.stringify(rows.slice(0, 100)));
    } catch (_) {}
  }

  function savePublishedHistory(entry) {
"""
if helper not in s:
    if old not in s: raise SystemExit('save history anchor missing')
    s = s.replace(old, helper, 1)

old = "      return `<div style=\"padding:10px 0;border-top:1px solid #eee3d4\"><strong>${escapeHtml(x.name || x.deck_id)}</strong><div class=\"muted\">${escapeHtml(when)}</div><a href=\"${escapeHtml(x.url)}\" target=\"_blank\">開啟占卜頁</a></div>`;\n"
new = "      const manage = x.manage_url ? ` · <a href=\"${escapeHtml(x.manage_url)}\">管理</a>` : '';\n      return `<div style=\"padding:10px 0;border-top:1px solid #eee3d4\"><strong>${escapeHtml(x.name || x.deck_id)}</strong><div class=\"muted\">${escapeHtml(when)}</div><a href=\"${escapeHtml(x.url)}\" target=\"_blank\">開啟占卜頁</a>${manage}</div>`;\n"
if new not in s:
    if old not in s: raise SystemExit('history row anchor missing')
    s = s.replace(old, new, 1)

old = "      personaCreateStatus.textContent = `✓ 已建立「${data.name}」，並設為這副牌的預設解牌師。`;\n"
new = old + "      const manageUrl = managementUrl(data);\n      if (manageUrl) {\n        const box = document.getElementById('persona-management'); const link = document.getElementById('persona-manage-link');\n        link.href = manageUrl; link.textContent = manageUrl; box.classList.remove('hidden');\n        saveManagedResource({type:'persona', id:data.persona_id, name:data.name, manage_url:manageUrl, created_at:new Date().toISOString()});\n      }\n"
if new not in s:
    if old not in s: raise SystemExit('persona status JS anchor missing')
    s = s.replace(old, new, 1)

old = "      savePublishedHistory({ deck_id: data.deck_id, name: data.name || name, theme_id: selectedThemeId, persona_id: data.default_persona || selectedPersonaId, url, published_at: new Date().toISOString() });\n"
new = "      const manageUrl = managementUrl(data);\n      const manageLink = document.getElementById('deck-manage-link');\n      if (manageLink && manageUrl) { manageLink.href = manageUrl; manageLink.textContent = manageUrl; }\n      savePublishedHistory({ deck_id: data.deck_id, name: data.name || name, theme_id: selectedThemeId, persona_id: data.default_persona || selectedPersonaId, url, manage_url: manageUrl, published_at: new Date().toISOString() });\n      if (manageUrl) saveManagedResource({type:'deck', id:data.deck_id, name:data.name || name, manage_url:manageUrl, public_url:url, created_at:new Date().toISOString()});\n"
if new not in s:
    if old not in s: raise SystemExit('deck history anchor missing')
    s = s.replace(old, new, 1)

old = "  document.getElementById('copy').addEventListener('click', async () => {\n"
buttons = """  document.getElementById('copy-persona-manage')?.addEventListener('click', async () => {
    const url = document.getElementById('persona-manage-link')?.href || '';
    if (url) await navigator.clipboard.writeText(url);
    document.getElementById('copy-persona-manage').textContent = '已複製';
  });
  document.getElementById('copy-deck-manage')?.addEventListener('click', async () => {
    const url = document.getElementById('deck-manage-link')?.href || '';
    if (url) await navigator.clipboard.writeText(url);
    document.getElementById('copy-deck-manage').textContent = '已複製';
  });

  document.getElementById('copy').addEventListener('click', async () => {
"""
if buttons not in s:
    if old not in s: raise SystemExit('copy button anchor missing')
    s = s.replace(old, buttons, 1)
js.write_text(s, encoding='utf-8')
print('creator_ownership_ui_patch=passed')
