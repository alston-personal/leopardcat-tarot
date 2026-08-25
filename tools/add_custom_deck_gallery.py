from pathlib import Path
p=Path('website/main.js')
s=p.read_text(encoding='utf-8')
anchor='window.loadActiveDeckBranding = async function() {'
if anchor not in s:
    raise SystemExit('branding anchor missing')
if 'window.renderCustomDeckGallery = function(deck)' not in s:
    fn=r'''
window.renderCustomDeckGallery = function(deck) {
    const section = document.getElementById('gallery');
    const container = document.getElementById('gallery-container');
    if (!section || !container) return;
    section.classList.remove('hidden');

    const sectionLabel = section.querySelector('.section-title .label');
    const sectionTitle = section.querySelector('.section-title h2');
    if (sectionLabel) { sectionLabel.removeAttribute('data-i18n'); sectionLabel.textContent = 'Deck Gallery'; }
    if (sectionTitle) { sectionTitle.removeAttribute('data-i18n'); sectionTitle.textContent = `${deck.name}・牌卡展示`; }

    const cards = Array.isArray(deck.cards) ? deck.cards : [];
    container.innerHTML = `<div class="gallery-grid custom-deck-gallery"></div>`;
    const grid = container.querySelector('.gallery-grid');

    cards.forEach((card, index) => {
        const title = card.title?.[window.currentLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || `Card ${index + 1}`;
        const upright = card.meanings?.upright || card.meaning?.[window.currentLang] || card.meaning || '';
        const reversed = card.meanings?.reversed || upright;
        const wrapper = document.createElement('div');
        wrapper.className = 'card-wrapper reveal-on-scroll theme-custom';
        wrapper.innerHTML = `
            <div class="card" id="gallery-${card.id || index}">
                <div class="card-front" style="background:#111;">
                    <img src="${card.image || ''}" alt="${title}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;">
                </div>
                <div class="card-back">
                    <div class="back-content" tabindex="0" aria-label="${title} 牌義，可上下捲動">
                        <button class="card-flip-back" type="button" aria-label="翻回牌面">↩ 翻回牌面</button>
                        <h3>${title}</h3>
                        <div class="meaning-box"><span class="label">正位牌義</span><p class="content-text"></p></div>
                        ${deck.reversals ? '<div class="ecology-box reversed-meaning"><span class="label">逆位牌義</span><p class="content-text"></p></div>' : ''}
                    </div>
                </div>
            </div>`;
        wrapper.querySelector('.meaning-box .content-text').textContent = upright;
        const reversedText = wrapper.querySelector('.reversed-meaning .content-text');
        if (reversedText) reversedText.textContent = reversed;

        const cardInner = wrapper.querySelector('.card');
        const scrollable = wrapper.querySelector('.back-content');
        scrollable.addEventListener('wheel', (e) => {
            const maxScroll = Math.max(0, scrollable.scrollHeight - scrollable.clientHeight);
            const atTop = scrollable.scrollTop <= 0;
            const atBottom = scrollable.scrollTop >= maxScroll - 1;
            const canConsume = maxScroll > 0 && !((e.deltaY < 0 && atTop) || (e.deltaY > 0 && atBottom));
            if (canConsume) {
                e.preventDefault();
                e.stopPropagation();
                scrollable.scrollTop += e.deltaY;
            }
        }, { passive:false });
        scrollable.addEventListener('click', e => e.stopPropagation());
        scrollable.addEventListener('touchstart', e => e.stopPropagation(), { passive:true });
        scrollable.addEventListener('touchend', e => e.stopPropagation(), { passive:true });
        scrollable.querySelector('.card-flip-back')?.addEventListener('click', e => {
            e.stopPropagation();
            cardInner.classList.remove('is-flipped');
        });
        cardInner.addEventListener('click', () => cardInner.classList.toggle('is-flipped'));
        grid.appendChild(wrapper);
        revealObserver?.observe(wrapper);
    });
};

'''
    s=s.replace(anchor,fn+anchor,1)
old="""        // Ecology/history/gallery belong to LeopardCat, so a creator page hides them instead of impersonating the creator.\n        ['intro','chronicle','gallery'].forEach(id => document.getElementById(id)?.classList.add('hidden'));\n        document.querySelector('a[href=\"#gallery\"]')?.classList.add('hidden');\n        document.querySelector('a[href=\"#intro\"]')?.classList.add('hidden');\n"""
new="""        // LeopardCat-specific ecology/history stay hidden, but a creator deck gets its own card gallery.\n        ['intro','chronicle'].forEach(id => document.getElementById(id)?.classList.add('hidden'));\n        document.querySelector('a[href=\"#intro\"]')?.classList.add('hidden');\n        const galleryNav = document.querySelector('a[href=\"#gallery\"]');\n        if (galleryNav) { galleryNav.classList.remove('hidden'); galleryNav.removeAttribute('data-i18n'); galleryNav.textContent = '牌卡展示'; }\n        window.cardData = Array.isArray(deck.cards) ? deck.cards : window.cardData;\n        window.renderCustomDeckGallery(deck);\n"""
if old not in s:
    raise SystemExit('custom hide block missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('custom_deck_gallery_patch=applied')
