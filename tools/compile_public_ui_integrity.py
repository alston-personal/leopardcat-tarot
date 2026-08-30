from pathlib import Path
import json,re
ROOT=Path('.')

# ----- locale bundle -----
lp=ROOT/'website/public/locales_v10.json'
data=json.loads(lp.read_text(encoding='utf-8'))
texts={
'zh':{'create_deck':'建立我的牌組','provider_429_error':'Gemini 目前回報供應商端額度／帳務狀態異常。牌局已保留，稍後可沿用同一副牌重新祈請。','privacy_note':'🔒 隱私預設：本站不保存你的問題與大師回答；問題會送至 AI 服務產生回覆。為了讓你能繼續追問，同一牌局的抽牌結果會匿名保存 24 小時後自動刪除。','social_share':'社群分享：','copy_link':'複製連結','spread_label':'牌陣','spread_single_short':'單牌','spread_three_short':'三牌'},
'en':{'create_deck':'Create My Deck','provider_429_error':'Gemini is currently reporting a provider quota or billing-state issue. Your draw is preserved for retry.','privacy_note':'🔒 Privacy by default: your question and the Master’s answer are not stored. The question is sent to the AI service to generate a response; anonymous draw state is kept for up to 24 hours so you can continue the same reading.','social_share':'Share:','copy_link':'Copy link','spread_label':'Spread','spread_single_short':'Single card','spread_three_short':'Three cards'},
'ja':{'create_deck':'自分のデッキを作る','provider_429_error':'Gemini 側で割り当て／請求状態の問題が報告されています。カード結果は保持されているため、後でもう一度試せます。','privacy_note':'🔒 プライバシー優先：質問とマスターの回答は保存しません。回答生成のため質問は AI サービスへ送信され、同じリーディングを続けられるよう匿名の抽選状態のみ最大24時間保持します。','social_share':'シェア：','copy_link':'リンクをコピー','spread_label':'スプレッド','spread_single_short':'1枚','spread_three_short':'3枚'},
'ko':{'create_deck':'내 덱 만들기','provider_429_error':'Gemini 공급자 측 할당량/결제 상태 문제가 보고되고 있습니다. 카드 결과는 유지되므로 나중에 다시 시도할 수 있습니다.','privacy_note':'🔒 개인정보 보호 기본값: 질문과 마스터의 답변은 저장하지 않습니다. 답변 생성을 위해 질문은 AI 서비스로 전송되며, 같은 리딩을 이어갈 수 있도록 익명 카드 상태만 최대 24시간 보관합니다.','social_share':'공유:','copy_link':'링크 복사','spread_label':'스프레드','spread_single_short':'1장','spread_three_short':'3장'},
'es':{'create_deck':'Crear mi mazo','provider_429_error':'Gemini informa de un problema de cuota o facturación del proveedor. La tirada se conserva para volver a intentarlo más tarde.','privacy_note':'🔒 Privacidad por defecto: no guardamos tu pregunta ni la respuesta del Maestro. La pregunta se envía al servicio de IA para generar la respuesta; solo el estado anónimo de la tirada se conserva hasta 24 horas para que puedas continuarla.','social_share':'Compartir:','copy_link':'Copiar enlace','spread_label':'Tirada','spread_single_short':'Una carta','spread_three_short':'Tres cartas'}
}
for lang,v in texts.items():
    data[lang].setdefault('nav',{})['create_deck']=v['create_deck']
    c=data[lang].setdefault('common',{})
    for k,val in v.items():
        if k!='create_deck': c[k]=val
lp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# ----- index: remove prod debugger, restore spread selector, i18n exposed strings -----
ip=ROOT/'website/index.html'; s=ip.read_text(encoding='utf-8')
s=re.sub(r'\s*<script src="https://unpkg\.com/vconsole@latest/dist/vconsole\.min\.js"></script>\s*<script>\s*// 🕵️ Mobile Debug Mode\s*window\.vConsole = new window\.VConsole\(\);\s*</script>','',s,flags=re.S)
s=s.replace('<a href="/create.html" id="nav-create-deck">建立我的牌組</a>','<a href="/create.html" id="nav-create-deck" data-i18n="nav.create_deck">建立我的牌組</a>')
s=s.replace('<p id="reading-privacy-note" style="font-size:0.72rem;line-height:1.6;opacity:.72;margin:8px 4px 14px;">','<p id="reading-privacy-note" data-i18n="common.privacy_note" style="font-size:0.72rem;line-height:1.6;opacity:.72;margin:8px 4px 14px;">')
needle='                        <button class="btn btn-gold" data-i18n="common.btn_draw" onclick="drawFortune()">祈請大師開牌</button>'
spread='''                        <div id="legacy-spread-picker" class="legacy-spread-picker" role="radiogroup" aria-label="Spread">\n                            <span class="legacy-spread-label" data-i18n="common.spread_label">牌陣</span>\n                            <button type="button" class="legacy-spread-btn active" data-spread-choice="single" data-i18n="common.spread_single_short">單牌</button>\n                            <button type="button" class="legacy-spread-btn" data-spread-choice="three_card" data-i18n="common.spread_three_short">三牌</button>\n                        </div>\n'''+needle
if 'data-spread-choice="single"' not in s: s=s.replace(needle,spread)
s=s.replace('<span class="social-label">社群分享：</span>','<span class="social-label" data-i18n="common.social_share">社群分享：</span>')
s=s.replace('class="btn btn-gold-outline btn-tiny" style="margin-left: 10px; font-size: 0.6rem;">複製連結</button>','class="btn btn-gold-outline btn-tiny" data-i18n="common.copy_link" style="margin-left: 10px; font-size: 0.6rem;">複製連結</button>')
ip.write_text(s,encoding='utf-8')

# ----- main runtime: real spread selection + live error retranslation -----
mp=ROOT/'website/main.js'; s=mp.read_text(encoding='utf-8')
if "window.activeSpread = 'single';" not in s:
    s=s.replace('window.currentReadingState = null; // shared deck/theme/card/orientation state for every Tarot deck',"window.currentReadingState = null; // shared deck/theme/card/orientation state for every Tarot deck\nwindow.activeSpread = 'single'; // homepage spread selector; preserved across retries")
# provider error through locale catalog instead of local language dict
s=re.sub(r"if \(e\?\.code === 'provider_429_billing_or_quota_state' \|\| e\?\.status === 429\) \{\s*const messages = \{.*?\};\s*return messages\[resolveLocale\(window\.currentLang\)\] \|\| messages\.en;\s*\}","if (e?.code === 'provider_429_billing_or_quota_state' || e?.status === 429) {\n        return uiText('provider_429_error', 'Gemini is currently reporting a provider quota or billing-state issue. Your draw is preserved for retry.');\n    }",s,flags=re.S)
# homepage request must respect the restored selector
s=s.replace("input: { spread: 'auto', deck_id: window.activeDeckId },","input: { spread: window.activeSpread || 'single', deck_id: window.activeDeckId },")
# mark dynamic error bubble so language changes can update it
s=s.replace("errBubble.classList.add('modular-retry-bubble');\n    const text = document.createElement('p');","errBubble.classList.add('modular-retry-bubble');\n    errBubble.dataset.errorCode = error?.code || '';\n    errBubble.dataset.errorStatus = String(error?.status || '');\n    const text = document.createElement('p');\n    text.className = 'modular-error-text';")
# applyLanguage updates already-rendered dynamic errors/buttons
marker="    if (languageSelect) languageSelect.value = lang;"
addition="""    if (languageSelect) languageSelect.value = lang;\n\n    // Dynamic runtime states must change language too; static data-i18n alone is not enough.\n    document.querySelectorAll('.modular-retry-bubble').forEach(bubble => {\n        const code = bubble.dataset.errorCode || '';\n        const status = Number(bubble.dataset.errorStatus || 0);\n        const text = bubble.querySelector('.modular-error-text');\n        const retry = bubble.querySelector('.retry-btn');\n        if (text) text.textContent = modularErrorMessage({ code, status });\n        if (retry) retry.textContent = uiText('retry', 'Retry');\n    });"""
if 'Dynamic runtime states must change language too' not in s: s=s.replace(marker,addition,1)
# spread picker binding
anchor="document.addEventListener('DOMContentLoaded', initAllSystems);"
binder="""function bindLegacySpreadPicker() {\n    const buttons = Array.from(document.querySelectorAll('[data-spread-choice]'));\n    if (!buttons.length) return;\n    const select = spread => {\n        window.activeSpread = spread || 'single';\n        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.spreadChoice === window.activeSpread));\n    };\n    buttons.forEach(btn => btn.addEventListener('click', () => select(btn.dataset.spreadChoice)));\n    select(window.activeSpread);\n}\n\ndocument.addEventListener('DOMContentLoaded', bindLegacySpreadPicker);\n"""+anchor
if 'function bindLegacySpreadPicker()' not in s: s=s.replace(anchor,binder,1)
mp.write_text(s,encoding='utf-8')

# ----- visual consistency: one control radius across public surfaces -----
sp=ROOT/'website/style.css'; css=sp.read_text(encoding='utf-8')
if '--control-radius:' not in css:
    css=css.replace('--nav-height: 80px;','--nav-height: 80px;\n  --control-radius: 18px;')
override='''\n/* Public control geometry contract: interactive controls use one rounded language. */\nbutton, select, input, textarea, .btn, .btn-gold-outline, .nav-links a, .lang-switcher, .language-select, #user-spirit-badge {\n  border-radius: var(--control-radius) !important;\n}\n.legacy-spread-picker { display:flex; align-items:center; justify-content:center; gap:8px; flex-wrap:wrap; margin:4px 0 14px; }\n.legacy-spread-label { color:var(--color-text-sec); font-size:.78rem; margin-right:2px; }\n.legacy-spread-btn { background:rgba(212,175,55,.05); color:var(--color-gold); border:1px solid rgba(212,175,55,.35); padding:8px 18px; cursor:pointer; }\n.legacy-spread-btn.active { background:var(--color-gold); color:var(--color-bg); border-color:var(--color-gold); }\n'''
if 'Public control geometry contract' not in css: css += override
sp.write_text(css,encoding='utf-8')

rp=ROOT/'website/public/read.css'; rcss=rp.read_text(encoding='utf-8')
if 'Public control geometry contract' not in rcss:
    rcss += '\n/* Public control geometry contract */\n:root{--control-radius:18px}button,select,input,textarea,.pill,.spread{border-radius:var(--control-radius)!important}\n'
rp.write_text(rcss,encoding='utf-8')

for file in ['website/public/create.html','website/public/manage.html']:
    p=ROOT/file; h=p.read_text(encoding='utf-8')
    if 'Public control geometry contract' not in h:
        h=h.replace('</style>','/* Public control geometry contract */ button,select,input,textarea,.btn{border-radius:18px!important}\n  </style>',1)
    p.write_text(h,encoding='utf-8')

# ----- regression tests -----
tp=ROOT/'website/tests/test_public_ui_integrity.py'
tp.write_text('''import json\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\n\ndef test_homepage_preserves_explicit_spread_selection_and_no_prod_vconsole():\n    html=(ROOT/'index.html').read_text(encoding='utf-8')\n    js=(ROOT/'main.js').read_text(encoding='utf-8')\n    assert 'vconsole' not in html.lower()\n    assert 'data-spread-choice="single"' in html\n    assert 'data-spread-choice="three_card"' in html\n    assert "window.activeSpread = 'single'" in js\n    assert "spread: window.activeSpread || 'single'" in js\n    assert "spread: 'auto'" not in js\n\ndef test_dynamic_errors_and_nav_are_locale_driven():\n    html=(ROOT/'index.html').read_text(encoding='utf-8')\n    js=(ROOT/'main.js').read_text(encoding='utf-8')\n    data=json.loads((ROOT/'public/locales_v10.json').read_text(encoding='utf-8'))\n    assert 'data-i18n="nav.create_deck"' in html\n    assert "uiText('provider_429_error'" in js\n    assert 'Dynamic runtime states must change language too' in js\n    required={'provider_429_error','privacy_note','social_share','copy_link','spread_label','spread_single_short','spread_three_short'}\n    for lang in ('zh','en','ja','ko','es'):\n        assert data[lang]['nav']['create_deck']\n        assert required.issubset(data[lang]['common'])\n\ndef test_public_controls_share_one_rounded_geometry_contract():\n    css=(ROOT/'style.css').read_text(encoding='utf-8')\n    read_css=(ROOT/'public/read.css').read_text(encoding='utf-8')\n    assert '--control-radius: 18px' in css\n    assert 'Public control geometry contract' in css\n    assert 'Public control geometry contract' in read_css\n    for file in ('create.html','manage.html'):\n        assert 'Public control geometry contract' in (ROOT/'public'/file).read_text(encoding='utf-8')\n\ndef test_primary_read_page_still_exposes_single_and_three_card_spreads():\n    js=(ROOT/'public/read.js').read_text(encoding='utf-8')\n    assert "{id:'single'" in js\n    assert "{id:'three_card'" in js\n''',encoding='utf-8')
