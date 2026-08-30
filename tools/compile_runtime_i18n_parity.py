from pathlib import Path
import json

ROOT=Path('.')
locales_path=ROOT/'website/public/locales_v10.json'
data=json.loads(locales_path.read_text(encoding='utf-8'))
extra={
'zh':{
'dharma_redraw_title':'點擊重修法號','dharma_redraw_confirm':'是否要重新洗滌靈魂，重修法號？','loading_cards':'牌卡體驗載入中...','init_connection_unstable':'靈力連線不穩','retry_ritual':'重新祈願','card_meaning_scroll_aria':'{title} 牌義，可上下捲動','card_flip_back':'翻回牌面','err_free_ai_unavailable':'免費 AI 額度目前不可用。牌局已保留，稍後可沿用同一副牌重新祈請。','err_master_unavailable':'大師目前暫時無法回應。牌局已保留，重新祈請不會重抽。','err_reading_unavailable':'目前無法完成解讀，請稍後再試。','retry':'重新祈請','persona_label':'解牌者','theme_label':'頁面風格','custom_theme_label':'這副牌的自訂風格','creator_tarot':'創作者塔羅','brand_fortune_template':'{name}・塔羅占卜'},
'en':{
'dharma_redraw_title':'Click to redraw name','dharma_redraw_confirm':'Redraw your spiritual identity?','loading_cards':'Loading the card experience...','init_connection_unstable':'Spirit connection is unstable','retry_ritual':'Retry ritual','card_meaning_scroll_aria':'{title} meaning, scroll vertically','card_flip_back':'Flip to card face','err_free_ai_unavailable':'Free AI capacity is currently unavailable. Your draw is preserved for retry.','err_master_unavailable':'The Master is temporarily unavailable. Your draw is preserved and will not be redrawn.','err_reading_unavailable':'Unable to complete the reading right now.','retry':'Retry','persona_label':'Reader','theme_label':'Theme','custom_theme_label':'Custom deck theme','creator_tarot':'Creator Tarot','brand_fortune_template':'{name} · Tarot Reading'},
'ja':{
'dharma_redraw_title':'クリックして法名を引き直す','dharma_redraw_confirm':'魂を清め、法名を引き直しますか？','loading_cards':'カード体験を読み込み中...','init_connection_unstable':'霊的な接続が不安定です','retry_ritual':'もう一度祈る','card_meaning_scroll_aria':'{title} の意味。上下にスクロールできます','card_flip_back':'カード面に戻す','err_free_ai_unavailable':'無料 AI 容量は現在利用できません。カード結果は保持されています。','err_master_unavailable':'現在マスターは応答できません。カード結果は保持され、引き直しません。','err_reading_unavailable':'現在リーディングを完了できません。後でもう一度お試しください。','retry':'再試行','persona_label':'リーダー','theme_label':'テーマ','custom_theme_label':'このデッキのカスタムテーマ','creator_tarot':'クリエイタータロット','brand_fortune_template':'{name}・タロット占い'},
'ko':{
'dharma_redraw_title':'눌러서 법명을 다시 받기','dharma_redraw_confirm':'영혼을 정화하고 법명을 다시 받으시겠습니까?','loading_cards':'카드 경험을 불러오는 중...','init_connection_unstable':'영적 연결이 불안정합니다','retry_ritual':'다시 기도하기','card_meaning_scroll_aria':'{title} 카드 의미, 위아래로 스크롤할 수 있습니다','card_flip_back':'카드 앞면으로','err_free_ai_unavailable':'무료 AI 용량을 현재 사용할 수 없습니다. 카드 결과는 보존됩니다.','err_master_unavailable':'현재 마스터가 응답할 수 없습니다. 카드 결과는 보존되며 다시 뽑지 않습니다.','err_reading_unavailable':'현재 리딩을 완료할 수 없습니다. 나중에 다시 시도해 주세요.','retry':'다시 시도','persona_label':'리더','theme_label':'테마','custom_theme_label':'이 덱의 사용자 지정 테마','creator_tarot':'크리에이터 타로','brand_fortune_template':'{name} · 타로 리딩'},
'es':{
'dharma_redraw_title':'Pulsa para renovar tu nombre espiritual','dharma_redraw_confirm':'¿Quieres renovar tu identidad espiritual?','loading_cards':'Cargando la experiencia de cartas...','init_connection_unstable':'La conexión espiritual es inestable','retry_ritual':'Reintentar ritual','card_meaning_scroll_aria':'Significado de {title}; desplázate verticalmente','card_flip_back':'Volver al frente','err_free_ai_unavailable':'La capacidad gratuita de IA no está disponible. Tu tirada se conserva para reintentar.','err_master_unavailable':'El Maestro no puede responder temporalmente. Tu tirada se conserva y no se volverá a sacar.','err_reading_unavailable':'No se puede completar la lectura ahora. Inténtalo más tarde.','retry':'Reintentar','persona_label':'Lector','theme_label':'Tema','custom_theme_label':'Tema personalizado del mazo','creator_tarot':'Tarot del creador','brand_fortune_template':'{name} · Lectura de Tarot'}
}
for lang, vals in extra.items():
    data[lang]['common'].update(vals)
locales_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

main=ROOT/'website/main.js'
s=main.read_text(encoding='utf-8')
# helper after getLocaleData
needle="function getAILanguageTag(lang = window.currentLang) {"
helper="""function uiText(key, fallback = '', params = {}) {\n    const common = getLocaleData()?.common || {};\n    let value = common[key] ?? fallback;\n    return String(value).replace(/\\{(\\w+)\\}/g, (_, name) => params[name] ?? `{${name}}`);\n}\n\n"""
if helper not in s:
    s=s.replace(needle,helper+needle,1)
repls={
"nameElem.title = window.currentLang === 'zh' ? '點擊重修法號' : 'Click to redraw name';":"nameElem.title = uiText('dharma_redraw_title', 'Click to redraw name');",
"if (confirm(window.currentLang === 'zh' ? '是否要重新洗滌靈魂，重修法號？' : 'Redraw your spiritual identity?')) {":"if (confirm(uiText('dharma_redraw_confirm', 'Redraw your spiritual identity?'))) {",
"loadingOverlay.innerHTML = '<div class=\"spirit-thinking\"><span></span><span></span><span></span></div><p style=\"color:var(--color-gold);margin-top:10px;font-size:0.8rem;letter-spacing:0.1em;\">牌卡體驗載入中...</p>';":"loadingOverlay.innerHTML = `<div class=\"spirit-thinking\"><span></span><span></span><span></span></div><p style=\"color:var(--color-gold);margin-top:10px;font-size:0.8rem;letter-spacing:0.1em;\">${uiText('loading_cards', 'Loading the card experience...')}</p>`;",
"<p style=\"color:#ff6b6b;font-size:0.8rem;\">靈力連線不穩 (${errType})</p>":"<p style=\"color:#ff6b6b;font-size:0.8rem;\">${uiText('init_connection_unstable', 'Spirit connection is unstable')} (${errType})</p>",
">重新祈願</button>":">${uiText('retry_ritual', 'Retry ritual')}</button>",
"aria-label=\"${title} 牌義，可上下捲動\"":"aria-label=\"${uiText('card_meaning_scroll_aria', `${title} meaning, scroll vertically`, {title})}\"",
"aria-label=\"翻回牌面\">↩ 翻回牌面</button>":"aria-label=\"${uiText('card_flip_back', 'Flip to card face')}\">↩ ${uiText('card_flip_back', 'Flip to card face')}</button>",
"return window.currentLang === 'zh'\n            ? '免費 AI 額度目前不可用。牌局已保留，稍後可沿用同一副牌重新祈請。'\n            : 'Free AI capacity is currently unavailable. Your draw is preserved for retry.';":"return uiText('err_free_ai_unavailable', 'Free AI capacity is currently unavailable. Your draw is preserved for retry.');",
"return window.currentLang === 'zh'\n            ? '大師目前暫時無法回應。牌局已保留，重新祈請不會重抽。'\n            : 'The Master is temporarily unavailable. Your draw is preserved and will not be redrawn.';":"return uiText('err_master_unavailable', 'The Master is temporarily unavailable. Your draw is preserved and will not be redrawn.');",
"return e?.message || (window.currentLang === 'zh' ? '目前無法完成解讀，請稍後再試。' : 'Unable to complete the reading right now.');":"return e?.message || uiText('err_reading_unavailable', 'Unable to complete the reading right now.');",
"btn.textContent = window.currentLang === 'zh' ? '重新祈請' : 'Retry';":"btn.textContent = uiText('retry', 'Retry');",
"box.innerHTML = '<label style=\"display:flex;gap:6px;align-items:center\">解牌者 <select id=\"persona-switcher-select\" style=\"border-radius:999px;padding:4px 8px\"></select></label>';":"box.innerHTML = `<label style=\"display:flex;gap:6px;align-items:center\">${uiText('persona_label', 'Reader')} <select id=\"persona-switcher-select\" style=\"border-radius:999px;padding:4px 8px\"></select></label>`;",
"box.innerHTML = '<label style=\"display:flex;gap:6px;align-items:center\">頁面風格 <select id=\"theme-switcher-select\" style=\"border-radius:999px;padding:4px 8px\"></select></label>';":"box.innerHTML = `<label style=\"display:flex;gap:6px;align-items:center\">${uiText('theme_label', 'Theme')} <select id=\"theme-switcher-select\" style=\"border-radius:999px;padding:4px 8px\"></select></label>`;",
"o.textContent='這副牌的自訂風格';":"o.textContent=uiText('custom_theme_label', 'Custom deck theme');",
"setText('#fortune .section-title h2', `${b.short_name || b.app_name}・塔羅占卜`);":"setText('#fortune .section-title h2', uiText('brand_fortune_template', '{name} · Tarot Reading', {name: b.short_name || b.app_name}));",
"setText('#fortune .section-title .label', b.creator_line || 'Creator Tarot');":"setText('#fortune .section-title .label', b.creator_line || uiText('creator_tarot', 'Creator Tarot'));"
}
for old,new in repls.items():
    if old not in s:
        print('WARN missing replacement',old[:80])
    else:
        s=s.replace(old,new,1)
main.write_text(s,encoding='utf-8')

t=ROOT/'website/tests/test_runtime_i18n_parity.py'
t.write_text("""import json\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\nREQUIRED={'dharma_redraw_title','dharma_redraw_confirm','loading_cards','init_connection_unstable','retry_ritual','card_meaning_scroll_aria','card_flip_back','err_free_ai_unavailable','err_master_unavailable','err_reading_unavailable','retry','persona_label','theme_label','custom_theme_label','creator_tarot','brand_fortune_template'}\ndef test_runtime_ui_keys_exist_in_all_locales():\n    data=json.loads((ROOT/'public/locales_v10.json').read_text(encoding='utf-8'))\n    for lang in ('zh','en','ja','ko','es'):\n        assert REQUIRED.issubset(data[lang]['common'])\ndef test_runtime_does_not_fall_back_to_zh_else_en_for_ui():\n    js=(ROOT/'main.js').read_text(encoding='utf-8')\n    forbidden=[\"window.currentLang === 'zh' ?\",\"window.currentLang === 'zh'\\n\"]\n    for token in forbidden:\n        assert token not in js\n    for token in (\"uiText('persona_label'\",\"uiText('theme_label'\",\"uiText('retry'\",\"uiText('card_flip_back'\"):\n        assert token in js\n""",encoding='utf-8')
