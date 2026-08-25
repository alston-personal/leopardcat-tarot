from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
index_path = ROOT / 'website' / 'index.html'
main_path = ROOT / 'website' / 'main.js'

index = index_path.read_text(encoding='utf-8')
main = main_path.read_text(encoding='utf-8')

# Make creation discoverable without requiring knowledge of a hidden URL.
nav_anchor = '            <a href="#gallery" data-i18n="nav.gallery">Gallery</a>\n'
nav_insert = nav_anchor + '            <a href="/create.html" id="nav-create-deck">建立我的牌組</a>\n'
if 'id="nav-create-deck"' not in index:
    index = index.replace(nav_anchor, nav_insert)

# Clear, accurate privacy copy: not persisted by us, but sent to the AI provider to answer.
question_anchor = '                        <textarea id="fortune-question" class="sacred-textarea" data-i18n="common.placeholder_question" placeholder="在此輸入你的困惑，或是屏息靜心..."></textarea>\n'
privacy = question_anchor + '''                        <p id="reading-privacy-note" style="font-size:0.72rem;line-height:1.6;opacity:.72;margin:8px 4px 14px;">🔒 隱私預設：本站不保存你的問題與大師回答；問題會送至 AI 服務產生回覆。為了讓你能繼續追問，同一牌局的抽牌結果會匿名保存 24 小時後自動刪除。</p>\n'''
if 'id="reading-privacy-note"' not in index:
    index = index.replace(question_anchor, privacy)

# Custom deck pages should feel like the creator's page, not a LeopardCat page.
branding = r'''

window.loadActiveDeckBranding = async function() {
    if (!window.activeDeckId || window.activeDeckId === 'leopardcat') return;
    try {
        const resp = await fetch(`/api/v1/decks/${encodeURIComponent(window.activeDeckId)}`);
        if (!resp.ok) throw new Error('DECK_NOT_FOUND');
        const deck = await resp.json();
        window.activeDeckInfo = deck;
        document.title = `${deck.name}・線上塔羅占卜`;

        const logo = document.querySelector('.nav-logo');
        if (logo) { logo.removeAttribute('data-i18n'); logo.textContent = deck.name; }
        const heroTitle = document.querySelector('#hero h1');
        if (heroTitle) { heroTitle.removeAttribute('data-i18n'); heroTitle.textContent = deck.name; }
        const heroSubtitle = document.querySelector('#hero .subtitle');
        if (heroSubtitle) {
            heroSubtitle.removeAttribute('data-i18n');
            heroSubtitle.textContent = deck.description || (deck.creator ? `由 ${deck.creator} 創作・${deck.card_count} 張牌` : `${deck.card_count} 張牌`);
        }
        const fortuneTitle = document.querySelector('#fortune .section-title h2');
        if (fortuneTitle) { fortuneTitle.removeAttribute('data-i18n'); fortuneTitle.textContent = `${deck.name}・塔羅占卜`; }
        const fortuneLabel = document.querySelector('#fortune .section-title .label');
        if (fortuneLabel) { fortuneLabel.removeAttribute('data-i18n'); fortuneLabel.textContent = deck.creator ? `by ${deck.creator}` : 'Creator Tarot'; }

        // Ecology/history/gallery belong to LeopardCat, so a creator page hides them instead of impersonating the creator.
        ['intro','chronicle','gallery'].forEach(id => document.getElementById(id)?.classList.add('hidden'));
        document.querySelector('a[href="#gallery"]')?.classList.add('hidden');
        document.querySelector('a[href="#intro"]')?.classList.add('hidden');

        const shareTitle = document.getElementById('share-memo-title');
        if (shareTitle) shareTitle.textContent = deck.name;
        const shareTag = document.getElementById('share-site-tag');
        if (shareTag) shareTag.textContent = deck.creator ? `牌卡創作：${deck.creator}` : '專屬線上占卜';
    } catch (err) {
        console.error('[Custom Deck] Unable to load deck:', err);
        const area = document.getElementById('fortune-ritual-area');
        if (area) area.innerHTML = '<p style="padding:24px;text-align:center">找不到這副牌，可能已下架或網址有誤。</p>';
    }
};

document.addEventListener('DOMContentLoaded', () => window.loadActiveDeckBranding());
'''
if 'window.loadActiveDeckBranding' not in main:
    main += branding

index_path.write_text(index, encoding='utf-8')
main_path.write_text(main, encoding='utf-8')
print('custom_deck_branding_patch=applied')
