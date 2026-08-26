import random

from divination.lenormand import LENORMAND_CARDS, LenormandMethod, SPREADS


def test_lenormand_has_canonical_36_unique_cards():
    assert len(LENORMAND_CARDS) == 36
    assert len({x["number"] for x in LENORMAND_CARDS}) == 36
    assert len({x["id"] for x in LENORMAND_CARDS}) == 36


def test_all_spreads_draw_without_replacement_and_emit_structure():
    method = LenormandMethod()
    for spread_id, spec in SPREADS.items():
        result = method.generate(input_data={"spread": spread_id}, question="測試", rng=random.Random(7))
        assert result["method"] == "lenormand"
        assert len(result["cards"]) == spec["count"]
        assert len({x["card_id"] for x in result["cards"]}) == spec["count"]
        assert result["rules"]["combination_reading"] is True
        assert "polarity_score" in result["structure"]


def test_yes_no_and_box9_emit_method_specific_grammar():
    method = LenormandMethod()
    yes_no = method.generate(input_data={"spread":"yes_no"}, question="可以嗎？", rng=random.Random(2))
    assert yes_no["structure"]["answer_tendency"] in {"yes","no","unclear"}

    box = method.generate(input_data={"spread":"box9"}, question="整體局勢？", rng=random.Random(3))
    assert len(box["structure"]["rows"]) == 3
    assert len(box["structure"]["columns"]) == 3
    assert len(box["structure"]["diagonals"]) == 2
    assert box["structure"]["center_card"] == box["cards"][4]["card_id"]
