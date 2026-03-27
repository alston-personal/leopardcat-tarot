(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e,t=localStorage.getItem(`leopard-lang`)||`zh`,n=null,r=null;async function i(){try{let[e,t]=await Promise.all([fetch(`content.json`),fetch(`manifest.json`)]);n=await e.json(),r=await t.json(),f(),o()}catch(e){console.error(`Failed to load website content:`,e)}}function a(e){e!==t&&(t=e,localStorage.setItem(`leopard-lang`,e),o())}function o(){if(!n||!r)return;let e=n[t];document.querySelectorAll(`[data-i18n]`).forEach(t=>{let n=t.getAttribute(`data-i18n`);for(let r in e)typeof e[r]==`object`&&e[r][n]&&(t.tagName===`TEXTAREA`||t.tagName===`INPUT`?t.placeholder=e[r][n]:t.textContent=e[r][n])}),document.querySelectorAll(`.lang-btn`).forEach(e=>e.classList.remove(`active`));let i=document.getElementById(`btn-${t}`);i&&i.classList.add(`active`),s(e.introduction),c(e.events),l(e.conservation),u(e.groups,r)}function s(t){document.getElementById(`intro-desc`).textContent=t.description;let n=document.getElementById(`intro-stats`);n.innerHTML=(t.stats||[]).map(e=>`
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
        `,r.appendChild(i),e?.observe(i);let a=i.querySelector(`.gallery-grid`),o=[];t.id===`material`?o=n.filter(e=>e.number>=0&&e.number<=7):t.id===`inner`?o=n.filter(e=>e.number>=8&&e.number<=14):t.id===`cosmic`?o=n.filter(e=>e.number>=15&&e.number<=21):t.id===`wands`&&(o=n.filter(e=>e.number>=101&&e.number<=114)),o.forEach(n=>{let r=d(n,t.id);a.appendChild(r),e?.observe(r)})}))}function d(e,n){let r=document.createElement(`div`);r.className=`card-wrapper reveal-on-scroll theme-${n}`;let i=e.title[t],a=e.meaning[t],o=e.ecology[t],s=t===`zh`?`塔羅牌義`:`Tarot Meaning`,c=t===`zh`?`石虎生態`:`Eco-Connection`;return r.innerHTML=`
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
    `,r.addEventListener(`click`,()=>{let e=r.querySelector(`.card`);e.style.transform=``,e.classList.toggle(`is-flipped`)}),r.addEventListener(`mousemove`,e=>{if(window.innerWidth<1024)return;let t=r.querySelector(`.card`),n=r.getBoundingClientRect(),i=e.clientX-n.left,a=e.clientY-n.top,o=n.width/2,s=(a-n.height/2)/10,c=(o-i)/10;t.classList.contains(`is-flipped`)||(t.style.transform=`perspective(1200px) rotateX(${s}deg) rotateY(${c}deg) translateY(-10px) translateZ(50px)`)}),r.addEventListener(`mouseleave`,()=>{let e=r.querySelector(`.card`);e.classList.contains(`is-flipped`)||(e.style.transform=``)}),r}function f(){if(!window.IntersectionObserver){console.warn(`IntersectionObserver not supported. Enabling fallback.`),document.body.classList.add(`no-observer`);return}e=new IntersectionObserver(t=>{t.forEach(t=>{t.isIntersecting&&(t.target.classList.add(`visible`),e.unobserve(t.target))})},{threshold:.01,rootMargin:`0px 0px 100px 0px`}),document.querySelectorAll(`.section`).forEach(t=>e.observe(t))}document.addEventListener(`DOMContentLoaded`,()=>{i()}),window.setLanguage=a,window.initWebsite=i,window.applyLanguage=o;var p=3,m=[],h=null;function g(e,t){let n=document.getElementById(`chat-history`),r=document.createElement(`div`);r.style.marginBottom=`15px`,r.style.padding=`12px 18px`,r.style.borderRadius=`15px`,r.style.maxWidth=`85%`,r.style.lineHeight=`1.6`,e===`user`?(r.style.backgroundColor=`rgba(212,175,55,0.15)`,r.style.color=`#fff`,r.style.marginLeft=`auto`,r.style.border=`1px solid rgba(212,175,55,0.3)`):(r.style.backgroundColor=`rgba(0,0,0,0.3)`,r.style.color=`#e0e0e0`,r.style.marginRight=`auto`,r.style.border=`1px solid rgba(255,255,255,0.1)`),r.innerHTML=t.replace(/\n/g,`<br>`),n.appendChild(r),n.scrollTop=n.scrollHeight}window.drawFortune=async function(){if(p<=0){document.getElementById(`fortune-result`).innerHTML=`
            <div class="master-response">
                <p style="color: #ff4a4a;">⚡ <strong>對話額度不足</strong></p>
                <p>大師陷入沉默，精神力已耗盡...<br>請添香油錢解鎖進階深度解析。</p>
                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn btn-gold-outline" onclick="topUp()">添香油錢 (需錢包連線 / $0.99)</button>
                </div>
            </div>
        `,document.getElementById(`fortune-result`).classList.remove(`hidden`);return}let e=document.getElementById(`fortune-question`).value,n=t===`zh`?`大師需要聽見你心中的疑惑！`:`The Oracle needs to hear your question!`;if(!e.trim())return alert(n);let i=document.getElementById(`btn-draw`),a=t===`zh`?`大師元神感應中...`:`Oracle is meditating...`,o=t===`zh`?`祈請大師開牌`:`Draw Your Destiny`;i.innerText=a,i.disabled=!0;try{if(!r||r.length===0){alert(t===`zh`?`牌組讀取中，請稍後`:`Deck is loading, please wait...`),i.innerText=o,i.disabled=!1;return}let n=Math.floor(Math.random()*r.length),a=r[n];p--;let s=t===`zh`?a.title.zh:a.title.en,c=t===`zh`?a.meaning.zh:a.meaning.en;i.innerText=t===`zh`?`大師解籤中...`:`Oracle is channeling...`;let l=await fetch(`/api/fortune`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({question:e,cardTitle:s,cardMeaning:c,lang:t})}),u=c;if(l.ok){let e=await l.json();e.reading&&(u=e.reading)}h=a,document.getElementById(`fortune-ritual-area`).classList.add(`hidden`),document.getElementById(`fortune-chat-area`).classList.remove(`hidden`);let d=t===`zh`?`大師為你抽出了 <strong>【${s}】</strong>。<br><img src="art/renders/${a.id}.png" style="width:100%; max-width:200px; margin:10px 0; border-radius:8px;"><br>${u}`:`The Oracle reveals <strong>【${s}】</strong>.<br><img src="art/renders/${a.id}.png" style="width:100%; max-width:200px; margin:10px 0; border-radius:8px;"><br>${u}`;m.push({role:`user`,content:e}),m.push({role:`assistant`,content:u}),g(`assistant`,d)}catch(e){console.error(e),alert(t===`zh`?`大師閉關中 (網路連線錯誤)`:`Oracle is resting (Network Error)`)}i.innerText=o,i.disabled=!1},window.sendChatMessage=async function(){let e=document.getElementById(`chat-input`),n=e.value.trim();if(n){if(p<=0)return alert(`⚡ 靈氣已耗盡，請鑄造 NFT 或重新祈願。`);e.value=``,g(`user`,n),p--;try{let e=await fetch(`/api/fortune`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({question:n,cardTitle:h.title[t],cardMeaning:h.meaning[t],lang:t,history:m})});if(e.ok){let t=(await e.json()).reading;g(`assistant`,t),m.push({role:`user`,content:n}),m.push({role:`assistant`,content:t})}}catch{g(`assistant`,`（大師因緣暫斷，請稍後再試...）`)}}},window.resetRitual=function(){m=[],document.getElementById(`chat-history`).innerHTML=``,document.getElementById(`fortune-chat-area`).classList.add(`hidden`),document.getElementById(`fortune-ritual-area`).classList.remove(`hidden`)},window.mintHistoryNFT=function(){alert(`🚀 正在封存對話紀錄並上傳 IPFS...
此功能將在下階段 Web3 打通後正式上線！`)},window.topUp=function(){alert(`即將跳轉至 Web3 錢包授權或 Stripe 支付端點...
(本演示直接為您充滿點數！)`),p+=3,document.getElementById(`fortune-result`).innerHTML=`<p style="text-align:center; padding: 20px;">✅ 感謝大德，天地靈氣已補充至 ⚡ ${p} 點！您可以繼續詢問大師了。</p>`};