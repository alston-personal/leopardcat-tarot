async function initWebsite() {
    try {
        const [contentRes, manifestRes] = await Promise.all([
            fetch('content.json'),
            fetch('manifest.json')
        ]);
        
        const content = await contentRes.json();
        const cards = await manifestRes.json();

        initScrollReveal(); 
        
        renderIntro(content.introduction);
        renderEvents(content.events);
        renderConservation(content.conservation);
        renderGallery(content.groups, cards);
        
    } catch (err) {
        console.error('Failed to load website content:', err);
    }
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
            const cardEl = createCardElement(card);
            grid.appendChild(cardEl);
            revealObserver?.observe(cardEl); 
        });
    });
}

function createCardElement(card) {
    const wrapper = document.createElement('div');
    wrapper.className = 'card-wrapper reveal-on-scroll';
    
    wrapper.innerHTML = `
        <div class="card" id="${card.id}">
            <div class="card-front">
                <div class="shimmer"></div>
                <img src="art/renders/${card.id}.png" alt="${card.title}" loading="lazy" 
                     onload="this.parentElement.classList.add('loaded')"
                     onerror="this.src='https://placehold.co/1400x2420/0a110e/d4af37?text=${card.title}'">
            </div>
            <div class="card-back">
                <div class="back-content">
                    <h3>${card.number}. ${card.title}</h3>
                    <div class="meaning-box">
                        <span class="label">塔羅牌義</span>
                        <p class="content-text">${card.meaning}</p>
                    </div>
                    <div class="ecology-box">
                        <span class="label">石虎生態</span>
                        <p class="content-text">${card.ecology}</p>
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
