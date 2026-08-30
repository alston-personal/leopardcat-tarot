import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED={'dharma_redraw_title','dharma_redraw_confirm','loading_cards','init_connection_unstable','retry_ritual','card_meaning_scroll_aria','card_flip_back','err_free_ai_unavailable','err_master_unavailable','err_reading_unavailable','retry','persona_label','theme_label','custom_theme_label','creator_tarot','brand_fortune_template','share_gathering','orientation_upright','orientation_reversed','default_quote','share_downloaded_manual','share_clipboard_saved','share_generate_again','seeking','spread_single','spread_three','spread_decision','master_opens','legacy_retry_error','share_generate','coming_soon','copied_link','deck_gallery_label','deck_gallery_title','upright_meaning','reversed_meaning','deck_page_title','deck_creator_summary','deck_count_summary','gallery_nav','share_creator','share_exclusive','deck_not_found'}
def test_runtime_ui_keys_exist_in_all_locales():
    data=json.loads((ROOT/'public/locales_v10.json').read_text(encoding='utf-8'))
    for lang in ('zh','en','ja','ko','es'):
        assert REQUIRED.issubset(data[lang]['common'])
def test_runtime_does_not_fall_back_to_zh_else_en_for_ui():
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    forbidden=["window.currentLang === 'zh' ?","window.currentLang === 'zh'\n"]
    for token in forbidden:
        assert token not in js
    for token in ("uiText('persona_label'","uiText('theme_label'","uiText('retry'","uiText('card_flip_back'"):
        assert token in js
