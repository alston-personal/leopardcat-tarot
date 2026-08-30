from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
main_path = root/'website/main.js'
style_path = root/'website/style.css'
cap_path = root/'governance/capabilities.json'
test_path = root/'website/tests/test_deck_driven_share_spreads.py'

main = main_path.read_text(encoding='utf-8')
anchor = '// 📸 Share Image Generator\nlet lastShareFile = null;\nlet lastShareText = "";\n\n// 📸 Share Image Generator\n'
helper = r'''// 📸 Share Image Generator
let lastShareFile = null;
let lastShareText = "";

function getShareCardTitle(card, lang = window.currentLang) {
    if (!card) return '';
    return card.title?.[lang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id || '';
}

function getShareCardImage(card, deckId = window.activeDeckId || 'leopardcat') {
    if (!card) return '';
    return card.image || card.main_image || card.output || (deckId === 'leopardcat' && card.id ? `art/renders/${card.id}.webp` : '');
}

async function resolveShareCardsFromDeck() {
    const state = window.currentReadingState || {};
    const deckId = state.deck_id || window.activeDeckId || 'leopardcat';
    let deck = null;
    try {
        const response = await fetch(`/api/v1/decks/${encodeURIComponent(deckId)}`, { cache: 'no-cache' });
        if (response.ok) deck = await response.json();
    } catch (error) {
        console.warn('[Share] deck snapshot unavailable, using loaded deck data', error);
    }
    const deckCards = Array.isArray(deck?.cards) && deck.cards.length ? deck.cards : (Array.isArray(window.cardData) ? window.cardData : []);
    const specs = Array.isArray(state.cards) && state.cards.length
        ? state.cards
        : [{ card_id: state.card_id || currentDrawnCard?.id, orientation: state.orientation || 'upright' }];
    const cards = specs.map((spec, index) => {
        const id = spec.card_id || spec.id;
        const card = deckCards.find(item => item.id === id) || (index === 0 ? currentDrawnCard : null) || spec;
        return {
            card,
            card_id: id || card?.id,
            orientation: spec.orientation || 'upright',
            position: spec.position || '',
            position_label: spec.position_label || ''
        };
    }).filter(item => item.card && getShareCardImage(item.card, deckId));
    if (!cards.length && currentDrawnCard) {
        cards.push({ card: currentDrawnCard, card_id: currentDrawnCard.id, orientation: state.orientation || 'upright', position: '', position_label: '' });
    }
    return { deck: deck || { deck_id: deckId, name: window.activeBrand?.app_name || deckId, cards: deckCards }, deckId, cards };
}

function renderShareCards(frame, shareContext) {
    const entries = shareContext.cards;
    frame.classList.toggle('share-three-card', entries.length > 1);
    frame.innerHTML = '';
    entries.forEach((entry, index) => {
        const slot = document.createElement('div');
        slot.className = 'share-card-slot';
        const img = document.createElement('img');
        if (index === 0) img.id = 'share-card-img'; // compatibility for older selectors/tests
        img.className = 'share-card-image';
        img.src = getShareCardImage(entry.card, shareContext.deckId);
        img.alt = getShareCardTitle(entry.card);
        img.style.transform = entry.orientation === 'reversed' ? 'rotate(180deg)' : '';
        slot.appendChild(img);
        const caption = document.createElement('div');
        caption.className = 'share-card-caption';
        const position = entry.position_label || entry.position;
        const orientation = entry.orientation === 'reversed' ? uiText('orientation_reversed', 'Reversed') : uiText('orientation_upright', 'Upright');
        caption.textContent = `${position ? position + ' · ' : ''}${getShareCardTitle(entry.card)} · ${orientation}`;
        slot.appendChild(caption);
        frame.appendChild(slot);
    });
}

// 📸 Share Image Generator
'''
if anchor not in main:
    raise SystemExit('share generator anchor not found')
main = main.replace(anchor, helper, 1)

old_fill = r'''    const template = document.getElementById('share-card-template');
    
    // Fill data
    const shareState = window.currentReadingState || {};
    const shareOrientation = shareState.orientation || 'upright';
    const shareImage = currentDrawnCard.image || `art/renders/${currentDrawnCard.id}.webp`;
    const shareImgEl = document.getElementById('share-card-img');
    shareImgEl.src = shareImage;
    shareImgEl.style.transform = shareOrientation === 'reversed' ? 'rotate(180deg)' : '';
    const titleZh = currentDrawnCard.title?.zh || currentDrawnCard.title?.['zh-TW'] || currentDrawnCard.title?.en || currentDrawnCard.id;
    const titleEn = currentDrawnCard.title?.en || titleZh;
    const orientationLabel = shareOrientation === 'reversed' ? uiText('orientation_reversed', 'Reversed') : uiText('orientation_upright', 'Upright');
    document.getElementById('share-card-title').innerText = `【${titleZh} / ${titleEn}】 · ${orientationLabel}`;
    document.getElementById('share-seeker-name').innerText = localStorage.getItem('userDharmaName') || 'Seeker';
    document.getElementById('share-date').innerText = new Date().toLocaleDateString();
'''
new_fill = r'''    const template = document.getElementById('share-card-template');
    
    // Deck-driven share composition: resolve this reading against the authoritative active deck.
    const shareState = window.currentReadingState || {};
    const shareContext = await resolveShareCardsFromDeck();
    const shareEntries = shareContext.cards;
    if (!shareEntries.length) throw new Error('SHARE_CARDS_NOT_FOUND');
    const shareFrame = template.querySelector('.share-card-frame');
    renderShareCards(shareFrame, shareContext);
    const titleParts = shareEntries.map(entry => getShareCardTitle(entry.card));
    if (shareEntries.length === 1) {
        const entry = shareEntries[0];
        const titleZh = entry.card.title?.zh || entry.card.title?.['zh-TW'] || entry.card.title?.en || entry.card_id;
        const titleEn = entry.card.title?.en || titleZh;
        const orientationLabel = entry.orientation === 'reversed' ? uiText('orientation_reversed', 'Reversed') : uiText('orientation_upright', 'Upright');
        document.getElementById('share-card-title').innerText = `【${titleZh} / ${titleEn}】 · ${orientationLabel}`;
    } else {
        document.getElementById('share-card-title').innerText = `【${uiText('spread_three_short', 'Three Cards')}】 ${titleParts.join(' · ')}`;
    }
    document.getElementById('share-seeker-name').innerText = localStorage.getItem('userDharmaName') || 'Seeker';
    document.getElementById('share-date').innerText = new Date().toLocaleDateString();
'''
if old_fill not in main:
    raise SystemExit('share fill block not found')
main = main.replace(old_fill, new_fill, 1)

old_wait = r'''    // 🕵️ Stability: Wait for image load + small layout settling delay
    const shareCardImg = document.getElementById('share-card-img');
    await Promise.race([
        new Promise(resolve => {
            if (shareCardImg.complete) resolve();
            else {
                shareCardImg.onload = resolve;
                shareCardImg.onerror = resolve; // Don't hang
            }
        }),
        new Promise(resolve => setTimeout(resolve, 5000)) // Force continue after 5s
    ]);
    await new Promise(resolve => setTimeout(resolve, 300)); // Layout settling delay
'''
new_wait = r'''    // 🕵️ Stability: wait for every card face in the spread, not only the first card.
    const shareCardImages = Array.from(template.querySelectorAll('.share-card-frame img'));
    await Promise.race([
        Promise.all(shareCardImages.map(img => new Promise(resolve => {
            if (img.complete) resolve();
            else {
                img.onload = resolve;
                img.onerror = resolve; // Don't hang; html2canvas still renders the remaining deck faces.
            }
        }))),
        new Promise(resolve => setTimeout(resolve, 5000))
    ]);
    await new Promise(resolve => setTimeout(resolve, 300)); // Layout settling delay
'''
if old_wait not in main:
    raise SystemExit('share image wait block not found')
main = main.replace(old_wait, new_wait, 1)

old_msg = r'''        const shareTitle = currentDrawnCard.title?.[shareLang] || currentDrawnCard.title?.['zh-TW'] || currentDrawnCard.title?.zh || currentDrawnCard.title?.en || currentDrawnCard.id;
        const orientationText = (window.currentReadingState?.orientation === 'reversed') ? (shareLang === 'zh' ? '（逆位）' : ' (Reversed)') : '';
        const brandTemplate = window.brandText('share_copy_template', common.share_copy_template);
        const shareMsg = brandTemplate.replace('{card}', `${shareTitle}${orientationText}`);
'''
new_msg = r'''        const shareCardText = shareEntries.map(entry => {
            const title = getShareCardTitle(entry.card, shareLang);
            const reversed = entry.orientation === 'reversed' ? (shareLang === 'zh' ? '（逆位）' : ' (Reversed)') : '';
            return `${title}${reversed}`;
        }).join(shareLang === 'zh' ? '、' : ', ');
        const brandTemplate = window.brandText('share_copy_template', common.share_copy_template);
        const shareMsg = brandTemplate.replace('{card}', shareCardText);
'''
if old_msg not in main:
    raise SystemExit('share text block not found')
main = main.replace(old_msg, new_msg, 1)

main_path.write_text(main, encoding='utf-8')

style = style_path.read_text(encoding='utf-8')
css_anchor = '''.share-card-frame img {\n  width: 160px;\n  border-radius: 4px;\n  box-shadow: 0 10px 20px rgba(0,0,0,0.5);\n}\n'''
css_new = css_anchor + r'''

/* Deck-driven share renderer: one-card and three-card spreads share the same deck contract. */
.share-card-frame {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 10px;
}
.share-card-slot {
  min-width: 0;
  text-align: center;
}
.share-card-caption {
  max-width: 160px;
  margin-top: 8px;
  color: rgba(244,241,234,.82);
  font-size: 10px;
  line-height: 1.35;
}
.share-card-frame.share-three-card {
  width: 390px;
  padding: 10px 8px;
  gap: 8px;
}
.share-card-frame.share-three-card .share-card-slot {
  width: 118px;
}
.share-card-frame.share-three-card img {
  width: 112px;
  max-height: 194px;
  object-fit: contain;
}
.share-card-frame.share-three-card .share-card-caption {
  max-width: 118px;
  font-size: 9px;
}
'''
if css_anchor not in style:
    raise SystemExit('share css anchor not found')
style = style.replace(css_anchor, css_new, 1)
style_path.write_text(style, encoding='utf-8')

caps = json.loads(cap_path.read_text(encoding='utf-8'))
caps['protected_capabilities']['sharing.deck-driven-spreads'] = {
    'status':'protected', 'owner':'website',
    'contract':[
        'Share-card rendering resolves card faces from the active Deck Module instead of assuming LeopardCat built-in asset paths.',
        'A three-card Tarot reading renders all three drawn cards in reading order, including each card position and upright/reversed orientation.',
        'Custom decks and future Deck Modules inherit the same share renderer when they expose cards through the public deck contract.',
        'Single-card sharing remains supported and compatible with the existing share-card experience.'
    ],
    'evidence':['website/main.js','website/style.css','website/tests/test_deck_driven_share_spreads.py']
}
cap_path.write_text(json.dumps(caps,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

test_path.write_text(r'''from pathlib import Path
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


def test_three_card_share_renders_every_entry_and_orientation():
    assert 'function renderShareCards(frame, shareContext)' in JS
    assert "entries.forEach((entry, index)" in JS
    assert "entry.orientation === 'reversed' ? 'rotate(180deg)'" in JS
    assert "frame.classList.toggle('share-three-card', entries.length > 1)" in JS
    assert "shareEntries.map(entry =>" in JS
    assert "titleParts.join(' · ')" in JS


def test_custom_deck_image_contract_not_hardcoded_to_builtin():
    assert 'card.image || card.main_image || card.output' in JS
    assert "deckId === 'leopardcat'" in JS
    assert '.share-card-frame.share-three-card' in CSS


def test_share_waits_for_all_spread_images():
    assert "querySelectorAll('.share-card-frame img')" in JS
    assert 'Promise.all(shareCardImages.map' in JS


def test_governance_protects_deck_driven_spread_sharing():
    capability=CAP['protected_capabilities']['sharing.deck-driven-spreads']
    assert capability['status']=='protected'
    assert any('three-card' in line.lower() for line in capability['contract'])
    assert any('Deck Module' in line for line in capability['contract'])
''', encoding='utf-8')
print('deck-driven share spread patch applied')
