import json
import random
from pathlib import Path

import pytest

from divination.core import DivinationError
from divination.tarot import draw, shuffle, TarotMethod


class Deck:
    deck_id='test-deck'; name='Test'; creator=''; reversals=True; source='test'; card_back='/art/card-back.svg'
    cards=[{'id':f'c{i}','title':{'en':f'C{i}'},'meanings':{'upright':f'u{i}','reversed':f'r{i}'}} for i in range(1,79)]
class Registry:
    def get(self, _): return Deck()


def test_shuffle_fixes_order_and_orientation_before_selection():
    a=shuffle(Deck.cards, reversal_rate=.5, rng=random.Random(42))
    b=shuffle(Deck.cards, reversal_rate=.5, rng=random.Random(42))
    assert [(x['card']['id'],x['orientation']) for x in a] == [(x['card']['id'],x['orientation']) for x in b]
    assert len({x['card']['id'] for x in a}) == 78


def test_draw_uses_one_based_manual_indices_and_preserves_order():
    hidden=shuffle(Deck.cards, reversal_rate=.5, rng=random.Random(8))
    result=draw(hidden,[3,76,55],[('past','Past'),('present','Present'),('future','Future')])
    assert [x['draw_index'] for x in result] == [3,76,55]
    assert [x['card_id'] for x in result] == [hidden[2]['card']['id'],hidden[75]['card']['id'],hidden[54]['card']['id']]
    assert [x['orientation'] for x in result] == [hidden[2]['orientation'],hidden[75]['orientation'],hidden[54]['orientation']]


def test_draw_rejects_duplicate_or_out_of_range_indices():
    hidden=shuffle(Deck.cards, reversal_rate=.5, rng=random.Random(1))
    with pytest.raises(DivinationError): draw(hidden,[1,1,2],[('a','a'),('b','b'),('c','c')])
    with pytest.raises(DivinationError): draw(hidden,[0],[('a','a')])
    with pytest.raises(DivinationError): draw(hidden,[79],[('a','a')])


def test_auto_and_manual_share_same_engine_result_when_indices_match():
    method=TarotMethod(Registry())
    auto=method.generate(input_data={'deck_id':'test-deck','spread':'three_card'},question='x',rng=random.Random(99))
    manual=method.generate(input_data={'deck_id':'test-deck','spread':'three_card','draw_indices':[1,2,3]},question='x',rng=random.Random(99))
    assert auto['cards'] == manual['cards']
    assert auto['rules']['draw_mode']=='auto'
    assert manual['rules']['draw_mode']=='manual'
    assert auto['rules']['orientation_assigned_at_shuffle_time'] is True


def test_manual_three_card_arbitrary_indices_are_deterministic():
    method=TarotMethod(Registry())
    x=method.generate(input_data={'spread':'three_card','draw_indices':[3,76,55]},question='x',rng=random.Random(123))
    y=method.generate(input_data={'spread':'three_card','draw_indices':[3,76,55]},question='x',rng=random.Random(123))
    assert x['cards']==y['cards']
    assert x['rules']['draw_indices']==[3,76,55]


def test_card_back_is_four_way_symmetric_by_construction_and_has_no_text():
    svg=Path('public/art/card-back.svg').read_text(encoding='utf-8')
    assert 'scale(-1 1)' in svg and 'scale(1 -1)' in svg and 'scale(-1 -1)' in svg
    assert '<text' not in svg.lower()


def test_ui_has_auto_manual_shuffle_and_shared_draw_payload():
    html=Path('index.html').read_text(encoding='utf-8')
    js=Path('main.js').read_text(encoding='utf-8')
    assert 'data-draw-mode="auto"' in html and 'data-draw-mode="manual"' in html
    assert 'id="manual-card-pool"' in html and 'shuffleManualDeck()' in html
    assert 'performReading(q, state.selected.slice(), state.seed)' in js
    assert 'draw_indices: drawOptions.drawIndices' in js
    assert '...(drawOptions.seed ? {seed: drawOptions.seed} : {})' in js


def test_all_locales_have_draw_mode_copy():
    data=json.loads(Path('public/locales_v10.json').read_text(encoding='utf-8'))
    for lang in ('zh','en','ja','ko','es'):
        c=data[lang]['common']
        for key in ('draw_mode_label','draw_mode_auto','draw_mode_manual','shuffle_cards','manual_draw_shuffle_first','manual_draw_progress','manual_card_aria'):
            assert c.get(key)


def test_governance_protects_shared_shuffle_draw_engine():
    caps=json.loads(Path('../governance/capabilities.json').read_text(encoding='utf-8'))
    c=caps['protected_capabilities']['reading.shuffle-draw-engine']
    assert c['status']=='protected'
    assert any('same shuffle() and draw()' in x for x in c['contract'])
