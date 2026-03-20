(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e;async function t(){try{let[e,t]=await Promise.all([fetch(`content.json`),fetch(`manifest.json`)]),o=await e.json(),c=await t.json();s(),n(o.introduction),r(o.events),i(o.conservation),a(o.groups,c)}catch(e){console.error(`Failed to load website content:`,e)}}function n(t){document.getElementById(`intro-desc`).textContent=t.description;let n=document.getElementById(`intro-stats`);n.innerHTML=(t.stats||[]).map(e=>`
        <div class="stat-item reveal-on-scroll">
            <div class="stat-val">${e.value}</div>
            <div class="stat-lbl">${e.label}</div>
        </div>
    `).join(``),n.querySelectorAll(`.reveal-on-scroll`).forEach(t=>e?.observe(t))}function r(t){let n=document.getElementById(`events-list`);n.innerHTML=(t||[]).map(e=>`
        <div class="event-card reveal-on-scroll">
            <div class="date">${e.date} | ${e.tag}</div>
            <h3>${e.title}</h3>
            <p class="content-text">${e.description}</p>
        </div>
    `).join(``),n.querySelectorAll(`.reveal-on-scroll`).forEach(t=>e?.observe(t))}function i(t){document.getElementById(`cons-title`).textContent=t.title,document.getElementById(`cons-desc`).textContent=t.description;let n=document.getElementById(`cons-links`);n.innerHTML=(t.links||[]).map(e=>`
        <a href="${e.url}" target="_blank" class="btn btn-gold-outline reveal-on-scroll" style="margin-top:0">${e.name}</a>
    `).join(``),n.querySelectorAll(`.reveal-on-scroll`).forEach(t=>e?.observe(t))}function a(t,n){let r=document.getElementById(`gallery-container`);r&&(r.innerHTML=``,(t||[]).forEach(t=>{let i=document.createElement(`div`);i.className=`group-section section`,i.innerHTML=`
            <div class="group-info">
                <h3>${t.title}</h3>
                <p class="content-text">${t.description}</p>
            </div>
            <div class="gallery-grid" id="grid-${t.id}"></div>
        `,r.appendChild(i),e?.observe(i);let a=i.querySelector(`.gallery-grid`),s=[];t.id===`material`?s=n.filter(e=>e.number>=0&&e.number<=7):t.id===`inner`?s=n.filter(e=>e.number>=8&&e.number<=14):t.id===`cosmic`&&(s=n.filter(e=>e.number>=15&&e.number<=21)),s.forEach(t=>{let n=o(t);a.appendChild(n),e?.observe(n)})}))}function o(e){let t=document.createElement(`div`);return t.className=`card-wrapper reveal-on-scroll`,t.innerHTML=`
        <div class="card" id="${e.id}">
            <div class="card-front">
                <div class="shimmer"></div>
                <img src="art/renders/${e.id}.png" alt="${e.title}" loading="lazy" 
                     onload="this.parentElement.classList.add('loaded')"
                     onerror="this.src='https://placehold.co/1400x2420/0a110e/d4af37?text=${e.title}'">
            </div>
            <div class="card-back">
                <div class="back-content">
                    <h3>${e.number}. ${e.title}</h3>
                    <div class="meaning-box">
                        <span class="label">塔羅牌義</span>
                        <p class="content-text">${e.meaning}</p>
                    </div>
                    <div class="ecology-box">
                        <span class="label">石虎生態</span>
                        <p class="content-text">${e.ecology}</p>
                    </div>
                </div>
            </div>
        </div>
    `,t.addEventListener(`click`,()=>{t.querySelector(`.card`).classList.toggle(`is-flipped`)}),t.addEventListener(`mousemove`,e=>{if(window.innerWidth<1024)return;let n=t.querySelector(`.card`),r=t.getBoundingClientRect(),i=e.clientX-r.left,a=e.clientY-r.top,o=r.width/2,s=(a-r.height/2)/10,c=(o-i)/10;n.classList.contains(`is-flipped`)||(n.style.transform=`perspective(1200px) rotateX(${s}deg) rotateY(${c}deg) translateY(-10px) translateZ(50px)`)}),t.addEventListener(`mouseleave`,()=>{let e=t.querySelector(`.card`);e.classList.contains(`is-flipped`)||(e.style.transform=``)}),t}function s(){if(!window.IntersectionObserver){console.warn(`IntersectionObserver not supported. Enabling fallback.`),document.body.classList.add(`no-observer`);return}e=new IntersectionObserver(t=>{t.forEach(t=>{t.isIntersecting&&(t.target.classList.add(`visible`),e.unobserve(t.target))})},{threshold:.01,rootMargin:`0px 0px 100px 0px`}),document.querySelectorAll(`.section`).forEach(t=>e.observe(t))}document.addEventListener(`DOMContentLoaded`,()=>{t()});