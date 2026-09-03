from pathlib import Path
import json

root = Path('.')
index = root/'website/index.html'
main = root/'website/main.js'
style = root/'website/style.css'
locales = root/'website/public/locales_v10.json'
gov = root/'governance/capabilities.json'
test = root/'website/tests/test_full_master_share.py'

# 1) UI controls
s = index.read_text(encoding='utf-8')
anchor = '''                        <div id="fortune-actions" class="hidden sacred-actions">\n                            <div class="sacred-action-btns">'''
insert = '''                        <div id="fortune-actions" class="hidden sacred-actions">\n                            <div id="share-content-controls" class="share-content-controls" data-share-content-mode="quote">\n                                <span class="share-content-label" data-i18n="common.share_content_label">分享內容</span>\n                                <div class="share-content-segments" role="group" aria-label="分享內容">\n                                    <button type="button" class="share-content-btn active" data-share-content-mode="quote" onclick="setShareContentMode('quote')" data-i18n="common.share_quote_mode">金句</button>\n                                    <button type="button" class="share-content-btn" data-share-content-mode="full" onclick="setShareContentMode('full')" data-i18n="common.share_full_mode">完整大師解讀</button>\n                                </div>\n                                <label id="share-question-option" class="share-question-option">\n                                    <input id="share-include-question" type="checkbox" onchange="setShareIncludeQuestion(this.checked)">\n                                    <span data-i18n="common.share_include_question">包含我的問題</span>\n                                </label>\n                                <p class="share-content-privacy" data-i18n="common.share_full_privacy">完整解讀只在你主動分享時送往社群；問題預設不分享。</p>\n                            </div>\n                            <div class="sacred-action-btns">'''
if anchor not in s:
    raise SystemExit('fortune actions anchor missing')
s = s.replace(anchor, insert, 1)
index.write_text(s, encoding='utf-8')

# 2) Share text behavior
s = main.read_text(encoding='utf-8')
anchor = '''let lastShareFile = null;\nlet lastShareText = "";'''
insert = '''let lastShareFile = null;\nlet lastShareText = "";\nlet lastShareBaseMessage = "";\nlet lastShareUrl = "";\nwindow.shareContentMode = 'quote';\nwindow.shareIncludeQuestion = false;\n\nfunction normalizeMasterShareText(value) {\n    return String(value || '')\n        .replace(/^#{1,6}\\s+/gm, '')\n        .replace(/\\*\\*(.*?)\\*\\*/g, '$1')\n        .replace(/__(.*?)__/g, '$1')\n        .replace(/`([^`]+)`/g, '$1')\n        .replace(/\\n{3,}/g, '\\n\\n')\n        .trim();\n}\n\nfunction latestMasterInterpretation() {\n    for (let i = currentChatHistory.length - 1; i >= 0; i--) {\n        const item = currentChatHistory[i];\n        if (item?.role === 'assistant' && item.content) return normalizeMasterShareText(item.content);\n    }\n    return '';\n}\n\nfunction buildSocialShareText(shareMsg, shareUrl) {\n    if (window.shareContentMode !== 'full') return `${shareMsg} ${shareUrl}`;\n    const answer = latestMasterInterpretation();\n    if (!answer) return `${shareMsg} ${shareUrl}`;\n    const parts = [];\n    if (window.shareIncludeQuestion && window._lastQuestion) {\n        parts.push(`${uiText('share_question_heading', '我的提問')}\\n${normalizeMasterShareText(window._lastQuestion)}`);\n    }\n    parts.push(answer);\n    parts.push(shareUrl);\n    return parts.join('\\n\\n');\n}\n\nfunction syncShareContentControls() {\n    const host = document.getElementById('share-content-controls');\n    if (host) host.dataset.shareContentMode = window.shareContentMode;\n    document.querySelectorAll('[data-share-content-mode]').forEach(btn => {\n        if (btn.matches('button')) btn.classList.toggle('active', btn.dataset.shareContentMode === window.shareContentMode);\n    });\n    const question = document.getElementById('share-include-question');\n    if (question) question.checked = Boolean(window.shareIncludeQuestion);\n}\n\nfunction refreshSocialShareText() {\n    if (!lastShareUrl || !lastShareBaseMessage) return;\n    const fullShareText = buildSocialShareText(lastShareBaseMessage, lastShareUrl);\n    lastShareText = fullShareText;\n    const lineLink = document.getElementById('share-line');\n    if (lineLink) lineLink.href = `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(lastShareUrl)}&text=${encodeURIComponent(fullShareText)}`;\n    const fbLink = document.getElementById('share-fb');\n    if (fbLink) fbLink.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(lastShareUrl)}&quote=${encodeURIComponent(fullShareText)}`;\n    const xLink = document.getElementById('share-x');\n    if (xLink) xLink.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(fullShareText)}`;\n    const threadsLink = document.getElementById('share-threads');\n    if (threadsLink) {\n        const u = new URL(lastShareUrl);\n        u.searchParams.set('preview', String(Date.now()));\n        threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildSocialShareText(lastShareBaseMessage, u.toString()))}`;\n    }\n}\n\nwindow.setShareContentMode = function(mode) {\n    window.shareContentMode = mode === 'full' ? 'full' : 'quote';\n    if (window.shareContentMode !== 'full') window.shareIncludeQuestion = false;\n    syncShareContentControls();\n    refreshSocialShareText();\n};\n\nwindow.setShareIncludeQuestion = function(include) {\n    window.shareIncludeQuestion = window.shareContentMode === 'full' && Boolean(include);\n    syncShareContentControls();\n    refreshSocialShareText();\n};\n\nwindow.prepareFacebookShare = async function() {\n    if (window.shareContentMode !== 'full' || !lastShareText) return;\n    try { await navigator.clipboard?.writeText(lastShareText); } catch (_) {}\n};'''
if anchor not in s:
    raise SystemExit('share globals anchor missing')
s = s.replace(anchor, insert, 1)

# Capture share base/url and build full text in both share paths.
old = '        const fullShareText = `${shareMsg} ${shareUrl}`;\n        lastShareText = fullShareText;'
new = '        lastShareBaseMessage = shareMsg;\n        lastShareUrl = shareUrl;\n        const fullShareText = buildSocialShareText(shareMsg, shareUrl);\n        lastShareText = fullShareText;'
if s.count(old) < 1:
    raise SystemExit('primary share text anchor missing')
s = s.replace(old, new)
old2 = '    const fullShareText = `${shareMsg} ${shareUrl}`;\n    \n    lastShareText = fullShareText;'
new2 = '    lastShareBaseMessage = shareMsg;\n    lastShareUrl = shareUrl;\n    const fullShareText = buildSocialShareText(shareMsg, shareUrl);\n    \n    lastShareText = fullShareText;'
if old2 in s:
    s = s.replace(old2, new2)

s = s.replace('quote=${encodeURIComponent(shareMsg)}', 'quote=${encodeURIComponent(fullShareText)}')
s = s.replace('const threadsShareText = `${shareMsg} ${threadsShareU.toString()}`;', 'const threadsShareText = buildSocialShareText(shareMsg, threadsShareU.toString());')

# Reset privacy-sensitive toggles with ritual reset.
reset_anchor = '''    lastShareFile = null;\n    lastShareText = "";'''
reset_new = '''    lastShareFile = null;\n    lastShareText = "";\n    lastShareBaseMessage = "";\n    lastShareUrl = "";\n    window.shareContentMode = 'quote';\n    window.shareIncludeQuestion = false;\n    syncShareContentControls();'''
if reset_anchor not in s:
    raise SystemExit('reset share anchor missing')
s = s.replace(reset_anchor, reset_new, 1)
main.write_text(s, encoding='utf-8')

# 3) Facebook copy-before-open hook
s = index.read_text(encoding='utf-8')
s = s.replace('id="share-fb" target="_blank" title="Facebook"', 'id="share-fb" target="_blank" title="Facebook" onclick="prepareFacebookShare()"', 1)
index.write_text(s, encoding='utf-8')

# 4) Styles
css = style.read_text(encoding='utf-8')
css += '''\n\n/* Full master interpretation sharing */\n.share-content-controls {\n  display: flex; align-items: center; justify-content: center; flex-wrap: wrap;\n  gap: 10px 12px; margin: 0 auto 14px; padding: 12px 14px;\n  max-width: 680px; border: 1px solid rgba(212,175,55,.18); border-radius: 14px;\n  background: rgba(255,255,255,.018);\n}\n.share-content-label { color: rgba(255,255,255,.62); font-size: .78rem; }\n.share-content-segments { display: inline-flex; gap: 4px; padding: 3px; border-radius: 999px; background: rgba(212,175,55,.07); }\n.share-content-btn { border: 1px solid transparent; border-radius: 999px; padding: 7px 13px; background: transparent; color: rgba(255,255,255,.72); cursor: pointer; font: inherit; font-size: .78rem; }\n.share-content-btn.active { background: var(--color-gold); color: #10130f; border-color: var(--color-gold); font-weight: 700; }\n.share-question-option { display: none; align-items: center; gap: 6px; color: rgba(255,255,255,.7); font-size: .74rem; cursor: pointer; }\n.share-content-controls[data-share-content-mode="full"] .share-question-option { display: inline-flex; }\n.share-content-privacy { flex-basis: 100%; margin: 0; text-align: center; color: rgba(255,255,255,.42); font-size: .67rem; line-height: 1.5; }\n@media (max-width: 620px) {\n  .share-content-controls { align-items: stretch; flex-direction: column; gap: 8px; }\n  .share-content-label { text-align: center; }\n  .share-content-segments { display: grid; grid-template-columns: 1fr 1fr; width: 100%; }\n  .share-content-btn { width: 100%; }\n  .share-question-option { justify-content: center; }\n}\n'''
style.write_text(css, encoding='utf-8')

# 5) Locales
loc = json.loads(locales.read_text(encoding='utf-8'))
translations = {
 'zh': ('分享內容','金句','完整大師解讀','包含我的問題','完整解讀只在你主動分享時送往社群；問題預設不分享。','我的提問'),
 'en': ('Share content','Quote','Full Master reading','Include my question','The full reading is sent to the social app only when you choose to share it. Your question is excluded by default.','My question'),
 'ja': ('共有内容','金言','大師の全文解読','質問も含める','全文解読は共有を選んだ時だけSNSへ渡されます。質問は既定では共有しません。','私の質問'),
 'ko': ('공유 내용','한마디','전체 해석','내 질문 포함','전체 해석은 직접 공유할 때만 소셜 앱으로 전달됩니다. 질문은 기본적으로 포함되지 않습니다.','내 질문'),
 'es': ('Contenido para compartir','Frase','Lectura completa','Incluir mi pregunta','La lectura completa solo se envía a la red social cuando decides compartirla. Tu pregunta queda fuera por defecto.','Mi pregunta')
}
for lang, vals in translations.items():
    if lang not in loc: continue
    common = loc[lang].setdefault('common', {})
    keys = ['share_content_label','share_quote_mode','share_full_mode','share_include_question','share_full_privacy','share_question_heading']
    for k,v in zip(keys, vals): common[k]=v
locales.write_text(json.dumps(loc, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

# 6) Governance
cap = json.loads(gov.read_text(encoding='utf-8'))
pc = cap['protected_capabilities']
pc['sharing.full-master-text'] = {
  'status':'protected', 'owner':'website',
  'contract':[
    'Quote-only sharing remains the default; full Master interpretation sharing requires an explicit user choice.',
    'Sharing the full Master interpretation uses the browser-local reading/chat state and MUST NOT introduce server-side persistence of the AI answer.',
    'The seeker question is excluded from full interpretation sharing by default and may be included only through a separate explicit opt-in control.',
    'Native/social sharing may send the selected share text and existing deck-owned share image to the chosen platform, while the public reading URL keeps the existing read-only symbolic receipt boundary.',
    'Facebook web sharing may copy the selected full text to the clipboard because the platform does not guarantee arbitrary long-text prefill from third-party share URLs.'
  ],
  'evidence':['website/index.html','website/main.js','website/style.css','website/public/locales_v10.json','website/tests/test_full_master_share.py']
}
gov.write_text(json.dumps(cap, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

# 7) Focused tests
test.write_text('''from pathlib import Path\nimport json\nROOT=Path(__file__).resolve().parents[1]\n\ndef test_full_master_share_is_explicit_and_question_opt_in():\n    html=(ROOT/'index.html').read_text(encoding='utf-8')\n    js=(ROOT/'main.js').read_text(encoding='utf-8')\n    assert 'data-share-content-mode="quote"' in html\n    assert 'data-share-content-mode="full"' in html\n    assert 'id="share-include-question"' in html\n    assert "window.shareContentMode = 'quote'" in js\n    assert 'window.shareIncludeQuestion = false' in js\n    assert "window.shareContentMode !== 'full'" in js\n\ndef test_full_master_share_uses_browser_chat_without_server_persistence():\n    js=(ROOT/'main.js').read_text(encoding='utf-8')\n    assert 'function latestMasterInterpretation()' in js\n    assert 'currentChatHistory.length - 1' in js\n    assert "item?.role === 'assistant'" in js\n    assert 'function buildSocialShareText' in js\n    assert "parts.push(answer)" in js\n    assert "window._lastQuestion" in js\n\ndef test_full_share_drives_native_and_social_text():\n    js=(ROOT/'main.js').read_text(encoding='utf-8')\n    assert 'buildSocialShareText(shareMsg, shareUrl)' in js\n    assert 'buildSocialShareText(shareMsg, threadsShareU.toString())' in js\n    assert 'text: lastShareText' in js\n    assert 'window.prepareFacebookShare' in js\n    assert 'navigator.clipboard?.writeText(lastShareText)' in js\n\ndef test_capability_protects_privacy_default():\n    cap=json.loads((ROOT.parent/'governance/capabilities.json').read_text(encoding='utf-8'))\n    c=cap['protected_capabilities']['sharing.full-master-text']['contract']\n    joined=' '.join(c)\n    assert 'explicit user choice' in joined\n    assert 'MUST NOT introduce server-side persistence' in joined\n    assert 'excluded' in joined and 'opt-in' in joined\n''', encoding='utf-8')
print('full_master_share_patch=applied')
