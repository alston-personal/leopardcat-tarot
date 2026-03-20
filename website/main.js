// Global state
let revealObserver;
let currentLang = localStorage.getItem('leopard-lang') || 'zh';
let siteData = null;
let cardData = null;

async function initWebsite() {
    try {
        const [contentRes, manifestRes] = await Promise.all([
            fetch('content.json'),
            fetch('manifest.json')
        ]);
        
        siteData = await contentRes.json();
        cardData = await manifestRes.json();

        initScrollReveal(); 
        applyLanguage();
        
    } catch (err) {
        console.error('Failed to load website content:', err);
    }
}

function setLanguage(lang) {
    if (lang === currentLang) return;
    currentLang = lang;
    localStorage.setItem('leopard-lang', lang);
    applyLanguage();
}

function applyLanguage() {
    if (!siteData || !cardData) return;

    const data = siteData[currentLang];
    
    // Update all elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        // Look through all sections in content.json
        for (const section in data) {
            if (typeof data[section] === 'object' && data[section][key]) {
                el.textContent = data[section][key];
            }
        }
    });

    // Update Lang Switcher UI
    document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`btn-${currentLang}`);
    if (activeBtn) activeBtn.classList.add('active');

    // Render localized sections
    renderIntro(data.introduction);
    renderEvents(data.events);
    renderConservation(data.conservation);
    renderGallery(data.groups, cardData);
}

function renderIntro(intro) {
    document.getElementById('intro-desc').textContent = intro.description;
    const statsContainer = document.getElementById('intro-stats');
    statsContainer.innerHTML = (intro.stats || []).map(s => `
        <div class="stat-item reveal-on-scroll">
            <div class="stat-val">${s.value}</div>
            <div class="stat-lbl">${s.label}</div>
        </div>
    `).join('');
    
    statsContainer.querySelectorAll('.reveal-on-scroll').forEach(el => revealObserver?.observe(el));
}

function renderEvents(events) {
    const eventsList = document.getElementById('events-list');
    eventsList.innerHTML = (events || []).map(e => `
        <div class="event-card reveal-on-scroll">
            <div class="date">${e.date} | ${e.tag}</div>
            <h3>${e.title}</h3>
            <p class="content-text">${e.description}</p>
            ${e.attribution ? `<div class="attribution" style="font-size:0.7rem; opacity:0.5; margin-top:1rem; font-style:italic;">${e.attribution}</div>` : ''}
        </div>
    `).join('');
    
    eventsList.querySelectorAll('.reveal-on-scroll').forEach(el => revealObserver?.observe(el));
}

function renderConservation(cons) {
    document.getElementById('cons-title').textContent = cons.title;
    document.getElementById('cons-desc').textContent = cons.description;
    const linksContainer = document.getElementById('cons-links');
    linksContainer.innerHTML = (cons.links || []).map(l => `
        <a href="${l.url}" target="_blank" class="btn btn-gold-outline reveal-on-scroll" style="margin-top:0">${l.name}</a>
    `).join('');
    
    linksContainer.querySelectorAll('.reveal-on-scroll').forEach(el => revealObserver?.observe(el));
}

function renderGallery(groups, cards) {
    const container = document.getElementById('gallery-container');
    if (!container) return;
    container.innerHTML = '';

    (groups || []).forEach(group => {
        const groupEl = document.createElement('div');
        groupEl.className = 'group-section section';
        groupEl.innerHTML = `
            <div class="group-info">
                <h3>${group.title}</h3>
                <p class="content-text">${group.description}</p>
            </div>
            <div class="gallery-grid" id="grid-${group.id}"></div>
        `;
        container.appendChild(groupEl);
        revealObserver?.observe(groupEl);

        const grid = groupEl.querySelector('.gallery-grid');
        
        let filtered = [];
        if (group.id === 'material') filtered = cards.filter(c => c.number >= 0 && c.number <= 7);
        else if (group.id === 'inner') filtered = cards.filter(c => c.number >= 8 && c.number <= 14);
        else if (group.id === 'cosmic') filtered = cards.filter(c => c.number >= 15 && c.number <= 21);

        filtered.forEach(card => {
            const cardEl = createCardElement(card, group.id);
            grid.appendChild(cardEl);
            revealObserver?.observe(cardEl); 
        });
    });
}

function createCardElement(card, groupId) {
    const wrapper = document.createElement('div');
    wrapper.className = `card-wrapper reveal-on-scroll theme-${groupId}`;
    
    const title = card.title[currentLang];
    const meaning = card.meaning[currentLang];
    const ecology = card.ecology[currentLang];
    const labelMeaning = currentLang === 'zh' ? '塔羅牌義' : 'Tarot Meaning';
    const labelEcology = currentLang === 'zh' ? '石虎生態' : 'Eco-Connection';

    wrapper.innerHTML = `
        <div class="card" id="${card.id}">
            <div class="card-front">
                <div class="shimmer"></div>
                <img src="art/renders/${card.id}.png" alt="${title}" loading="lazy" 
                     onload="this.parentElement.classList.add('loaded')"
                     onerror="this.src='https://placehold.co/1400x2420/0a110e/d4af37?text=${title}'">
            </div>
            <div class="card-back">
                <div class="back-content">
                    <h3>${title}</h3>
                    <div class="meaning-box">
                        <span class="label">${labelMeaning}</span>
                        <p class="content-text">${meaning}</p>
                    </div>
                    <div class="ecology-box">
                        <span class="label">${labelEcology}</span>
                        <p class="content-text">${ecology}</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    wrapper.addEventListener('click', () => {
        wrapper.querySelector('.card').classList.toggle('is-flipped');
    });

    // Add mouse tilt effect (Desktop only optimized)
    wrapper.addEventListener('mousemove', (e) => {
        if (window.innerWidth < 1024) return;
        const card = wrapper.querySelector('.card');
        const rect = wrapper.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        if (!card.classList.contains('is-flipped')) {
            card.style.transform = `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-10px) translateZ(50px)`;
        }
    });

    wrapper.addEventListener('mouseleave', () => {
        const card = wrapper.querySelector('.card');
        if (!card.classList.contains('is-flipped')) {
            card.style.transform = '';
        }
    });

    return wrapper;
}

function initScrollReveal() {
    if (!window.IntersectionObserver) {
        console.warn('IntersectionObserver not supported. Enabling fallback.');
        document.body.classList.add('no-observer');
        return;
    }

    revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                revealObserver.unobserve(entry.target); 
            }
        });
    }, { threshold: 0.01, rootMargin: '0px 0px 100px 0px' });

    document.querySelectorAll('.section').forEach(el => revealObserver.observe(el));
}

document.addEventListener('DOMContentLoaded', () => {
    initWebsite();
});

// Expose to global scope for HTML onclick handlers
window.setLanguage = setLanguage;
window.initWebsite = initWebsite;
window.applyLanguage = applyLanguage;
