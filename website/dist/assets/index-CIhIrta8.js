(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e,t=localStorage.getItem(`leopard-lang`)||`zh`,n=null,r=null;async function i(){try{let[e,t]=await Promise.all([fetch(`content.json`),fetch(`manifest.json`)]);n=await e.json(),r=await t.json(),f(),o()}catch(e){console.error(`Failed to load website content:`,e)}}function a(e){e!==t&&(t=e,localStorage.setItem(`leopard-lang`,e),o())}function o(){if(!n||!r)return;let e=n[t];document.querySelectorAll(`[data-i18n]`).forEach(t=>{let n=t.getAttribute(`data-i18n`);e.nav[n]&&(t.textContent=e.nav[n])}),document.querySelectorAll(`.lang-btn`).forEach(e=>e.classList.remove(`active`));let i=document.getElementById(`btn-${t}`);i&&i.classList.add(`active`),s(e.introduction),c(e.events),l(e.conservation),u(e.groups,r)}function s(t){document.getElementById(`intro-desc`).textContent=t.description;let n=document.getElementById(`intro-stats`);n.innerHTML=(t.stats||[]).map(e=>`
        <div class="stat-item reveal-on-scroll">
            <div class="stat-val">${e.value}</div>
            <div class="stat-lbl">${e.label}</div>
        </div>
    `).join(``),n.querySelectorAll(`.reveal-on-scroll`).forEach(t=>e?.observe(t))}function c(t){let n=document.getElementById(`events-list`);n.innerHTML=(t||[]).map(e=>`
        <div class="event-card reveal-on-scroll">
            <div class="date">${e.date} | ${e.tag}</div>
            <h3>${e.title}</h3>
            <p class="content-text">${e.description}</p>
            ${e.attribution?`<div class="attribution" style="font-size:0.7rem; opacity:0.5; margin-top:1rem; font-style:italic;">${e.attribution}</div>`:``}
        </div>
    `).join(``),n.querySelectorAll(`.reveal-on-scroll`).forEach(t=>e?.observe(t))}function l(t){document.getElementById(`cons-title`).textContent=t.title,document.getElementById(`cons-desc`).textContent=t.description;let n=document.getElementById(`cons-links`);n.innerHTML=(t.links||[]).map(e=>`
        <a href="${e.url}" target="_blank" class="btn btn-gold-outline reveal-on-scroll" style="margin-top:0">${e.name}</a>
    `).join(``),n.querySelectorAll(`.reveal-on-scroll`).forEach(t=>e?.observe(t))}function u(t,n){let r=document.getElementById(`gallery-container`);r&&(r.innerHTML=``,(t||[]).forEach(t=>{let i=document.createElement(`div`);i.className=`group-section section`,i.innerHTML=`
            <div class="group-info">
                <h3>${t.title}</h3>
                <p class="content-text">${t.description}</p>
            </div>
            <div class="gallery-grid" id="grid-${t.id}"></div>
        `,r.appendChild(i),e?.observe(i);let a=i.querySelector(`.gallery-grid`),o=[];t.id===`material`?o=n.filter(e=>e.number>=0&&e.number<=7):t.id===`inner`?o=n.filter(e=>e.number>=8&&e.number<=14):t.id===`cosmic`&&(o=n.filter(e=>e.number>=15&&e.number<=21)),o.forEach(n=>{let r=d(n,t.id);a.appendChild(r),e?.observe(r)})}))}function d(e,n){let r=document.createElement(`div`);r.className=`card-wrapper reveal-on-scroll theme-${n}`;let i=e.title[t],a=e.meaning[t],o=e.ecology[t],s=t===`zh`?`塔羅牌義`:`Tarot Meaning`,c=t===`zh`?`石虎生態`:`Eco-Connection`;return r.innerHTML=`
        <div class="card" id="${e.id}">
            <div class="card-front">
                <div class="shimmer"></div>
                <img src="art/renders/${e.id}.png" alt="${i}" loading="lazy" 
                     onload="this.parentElement.classList.add('loaded')"
                     onerror="this.src='https://placehold.co/1400x2420/0a110e/d4af37?text=${i}'">
            </div>
            <div class="card-back">
                <div class="back-content">
                    <h3>${i}</h3>
                    <div class="meaning-box">
                        <span class="label">${s}</span>
                        <p class="content-text">${a}</p>
                    </div>
                    <div class="ecology-box">
                        <span class="label">${c}</span>
                        <p class="content-text">${o}</p>
                    </div>
                </div>
            </div>
        </div>
    `,r.addEventListener(`click`,()=>{r.querySelector(`.card`).classList.toggle(`is-flipped`)}),r.addEventListener(`mousemove`,e=>{if(window.innerWidth<1024)return;let t=r.querySelector(`.card`),n=r.getBoundingClientRect(),i=e.clientX-n.left,a=e.clientY-n.top,o=n.width/2,s=(a-n.height/2)/10,c=(o-i)/10;t.classList.contains(`is-flipped`)||(t.style.transform=`perspective(1200px) rotateX(${s}deg) rotateY(${c}deg) translateY(-10px) translateZ(50px)`)}),r.addEventListener(`mouseleave`,()=>{let e=r.querySelector(`.card`);e.classList.contains(`is-flipped`)||(e.style.transform=``)}),r}function f(){if(!window.IntersectionObserver){console.warn(`IntersectionObserver not supported. Enabling fallback.`),document.body.classList.add(`no-observer`);return}e=new IntersectionObserver(t=>{t.forEach(t=>{t.isIntersecting&&(t.target.classList.add(`visible`),e.unobserve(t.target))})},{threshold:.01,rootMargin:`0px 0px 100px 0px`}),document.querySelectorAll(`.section`).forEach(t=>e.observe(t))}document.addEventListener(`DOMContentLoaded`,()=>{i()}),window.setLanguage=a,window.initWebsite=i,window.applyLanguage=o;