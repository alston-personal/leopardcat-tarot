from pathlib import Path


def test_spread_share_state_cannot_be_reauthored_from_current_drawn_card():
    src = Path(__file__).parents[1].joinpath('main.js').read_text(encoding='utf-8')
    assert 'if (shareEntries.length === 1 && !window.currentReadingState && !window.currentReadingEnvelope)' in src
    assert 'updateSocialLinks(shareEntries[0].card, bestQuote);' in src
    assert 'updateSocialLinks(currentDrawnCard, bestQuote);' not in src


def test_three_card_share_is_derived_from_reading_entries():
    src = Path(__file__).parents[1].joinpath('main.js').read_text(encoding='utf-8')
    assert "const shareEntries = shareContext.cards;" in src
    assert "shareEntries.map(entry =>" in src
    assert "renderShareCards(shareFrame, shareContext);" in src
    assert "applySingleCardShareFallback(shareU);" in src  # permitted only as fallback; canonical receipt still wins
