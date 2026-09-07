from pathlib import Path

from divination.tarot import SPREADS, plan_spread, spread_catalog


ROOT = Path(__file__).resolve().parents[1]
MAIN_JS = (ROOT / 'main.js').read_text(encoding='utf-8')
SERVER = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')


def test_spread_catalog_cannot_silently_shrink():
    required = {
        'single',
        'clarifier',
        'three_card',
        'situation_advice',
        'decision',
        'relationship',
        'career',
        'path',
        'celtic_cross',
    }
    assert required <= set(SPREADS)
    assert len(spread_catalog()) >= len(required)
    assert len(SPREADS['relationship']) == 5
    assert len(SPREADS['career']) == 5
    assert len(SPREADS['path']) == 5
    assert len(SPREADS['celtic_cross']) == 10


def test_canonical_planner_selects_question_semantics_not_input_source():
    relationship = '我們的感情關係接下來會怎麼發展？'
    assert plan_spread(relationship)['spread'] == 'relationship'
    # Threads-source text is resolved to ordinary question text before planning;
    # the planner intentionally has no source parameter, so equal text is equal plan.
    assert plan_spread(str(relationship)) == plan_spread(relationship)

    assert plan_spread('我最近工作是否該換跑道？')['spread'] == 'career'
    assert plan_spread('A 與 B 兩個選擇哪一個比較適合我？')['spread'] == 'decision'
    assert plan_spread('今天請給我一個指引')['spread'] == 'single'
    assert plan_spread('我現在適合搬家嗎？')['spread'] == 'situation_advice'
    assert plan_spread('請補牌釐清剛才的訊息')['spread'] == 'clarifier'


def test_planner_result_contains_receipt_safe_metadata():
    plan = plan_spread('我的人生方向下一步該往哪裡走？')
    assert plan['spread'] == 'path'
    assert plan['card_count'] == 5
    assert plan['intent'] == 'direction'
    assert plan['complexity'] == 'medium'
    assert plan['reason']
    assert set(plan) == {'spread', 'card_count', 'intent', 'complexity', 'reason'}


def test_browser_no_longer_owns_auto_spread_heuristic():
    assert 'function automaticSpreadForQuestion' not in MAIN_JS
    assert "fetch('/api/v1/spread-plan'" in MAIN_JS
    assert "spread: window.drawMode === 'manual'" in MAIN_JS
    assert "(window.activeSpread || 'auto')" in MAIN_JS
    assert "['auto', 'single', 'three_card'].includes(spread)" not in MAIN_JS


def test_manual_auto_draw_uses_server_plan_before_card_selection():
    assert 'window.shuffleManualDeck = async function()' in MAIN_JS
    assert 'await fetchCanonicalSpreadPlan(q)' in MAIN_JS
    assert 'window.currentSpreadPlan = plan' in MAIN_JS
    assert 'window.effectiveSpread = plan.spread' in MAIN_JS


def test_server_owns_catalog_and_private_body_planner_endpoint():
    assert 'from divination.tarot import plan_spread, spread_catalog' in SERVER
    assert "'spreads': spread_catalog()" in SERVER
    assert "path == '/api/v1/spread-plan'" in SERVER
    assert "payload.get('question')" in SERVER
    # Question text must not be put into a planner query string.
    assert '/api/v1/spread-plan?question=' not in MAIN_JS


def test_ui_exposes_expanded_catalog_for_explicit_choice():
    for spread, count in (
        ('single', 1),
        ('clarifier', 1),
        ('three_card', 3),
        ('situation_advice', 3),
        ('decision', 3),
        ('relationship', 5),
        ('career', 5),
        ('path', 5),
        ('celtic_cross', 10),
    ):
        assert f'value="{spread}" data-card-count="{count}"' in INDEX


def test_share_path_stays_reading_state_monotonic():
    # Share renderer must continue to derive every card from canonical reading-level state.
    assert 'const shareContext = await resolveShareCardsFromDeck();' in MAIN_JS
    assert 'const shareEntries = shareContext.cards;' in MAIN_JS
    forbidden = 'updateSocialLinks(currentDrawnCard, bestQuote);'
    assert forbidden not in MAIN_JS
