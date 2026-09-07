from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
JS=(ROOT/'website/main.js').read_text(encoding='utf-8')
CSS=(ROOT/'website/style.css').read_text(encoding='utf-8')
CAP=json.loads((ROOT/'governance/capabilities.json').read_text(encoding='utf-8'))


def test_share_renderer_resolves_authoritative_deck():
    assert 'async function resolveShareCardsFromDeck()' in JS
    assert '/api/v1/decks/${encodeURIComponent(deckId)}' in JS
    assert "Array.isArray(state.cards) && state.cards.length" in JS
    assert "deckCards.find(item => item.id === id)" in JS


def test_multi_card_share_renders_every_entry_and_orientation():
    assert 'function renderShareCards(frame, shareContext)' in JS
    assert "entries.forEach((entry, index)" in JS
    assert "entry.orientation === 'reversed' ? 'rotate(180deg)'" in JS
    assert "frame.classList.toggle('share-three-card', entries.length > 1 && entries.length <= 3)" in JS
    assert "frame.classList.toggle('share-many-card', entries.length > 3)" in JS
    assert "frame.classList.toggle('share-ten-card', entries.length > 6)" in JS
    assert "shareEntries.map(entry =>" in JS
    assert "titleParts.join(' · ')" in JS


def test_custom_deck_image_contract_not_hardcoded_to_builtin():
    assert 'card.image || card.main_image || card.output' in JS
    assert "deckId === 'leopardcat'" in JS
    assert '.share-card-frame.share-three-card' in CSS
    assert '.share-card-frame.share-many-card' in CSS


def test_share_waits_for_all_spread_images():
    assert "querySelectorAll('.share-card-frame img')" in JS
    assert 'Promise.all(shareCardImages.map' in JS


def test_governance_protects_deck_driven_spread_sharing():
    capability=CAP['protected_capabilities']['sharing.deck-driven-spreads']
    assert capability['status']=='protected'
    assert any('three-card' in line.lower() for line in capability['contract'])
    assert any('Deck Module' in line for line in capability['contract'])
