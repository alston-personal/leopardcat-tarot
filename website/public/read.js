(() => {
  const localeMeta={zh:{label:'中',html:'zh-TW'},en:{label:'EN',html:'en'},ja:{label:'日本語',html:'ja'},ko:{label:'한국어',html:'ko'},es:{label:'ES',html:'es'}};
  let localeCatalog={};
  let currentLang='zh';
  const normalizeLang=v=>String(v||'').toLowerCase().replace('_','-');
  const resolveLang=v=>{const n=normalizeLang(v), f=n.split('-')[0];return localeCatalog[n]?n:(localeCatalog[f]?f:(localeCatalog.zh?'zh':'en'));};
  const rt=(key,fallback='',params={})=>String(localeCatalog[currentLang]?.read?.[key]??fallback).replace(/\{(\w+)\}/g,(_,k)=>params[k]??`{${k}}`);
  const aiLang=()=>({zh:'zh-TW',en:'en',ja:'ja',ko:'ko',es:'es'})[currentLang]||currentLang||'en';
  function applyReadLocale(){
    document.documentElement.lang=localeMeta[currentLang]?.html||currentLang;
    document.querySelectorAll('[data-read-i18n]').forEach(el=>{el.textContent=rt(el.dataset.readI18n,el.textContent);});
    document.querySelectorAll('[data-read-placeholder]').forEach(el=>{el.placeholder=rt(el.dataset.readPlaceholder,el.placeholder);});
    const sel=document.getElementById('read-language');
    if(sel){sel.innerHTML=Object.keys(localeCatalog).filter(x=>localeMeta[x]).map(x=>`<option value=\"${x}\" ${x===currentLang?'selected':''}>${localeMeta[x].label}</option>`).join('');sel.onchange=()=>setReadLanguage(sel.value);}
  }
  function setReadLanguage(lang){currentLang=resolveLang(lang);localStorage.setItem('leopard-lang',currentLang);applyReadLocale();if(Object.keys(state.methods||{}).length)renderMethod();if(state.lastResult)renderCards(state.lastResult);}
  async function loadReadLocale(){try{const r=await fetch('/locales_v10.json',{cache:'no-store'});localeCatalog=await r.json();}catch(_){localeCatalog={zh:{read:{}}};}currentLang=resolveLang(localStorage.getItem('leopard-lang')||navigator.language||'zh');applyReadLocale();}

  const qs = new URLSearchParams(location.search);
  const state = {
    method: qs.get('method') || 'tarot',
    spread: '',
    deck: qs.get('deck') || 'leopardcat',
    persona: qs.get('persona') || '',
    theme: qs.get('theme') || '',
    methods: {},
    handoff: null,
    envelope: null,
    brand: null,
    history: [],
    lastResult: null,
  };
  const $ = id => document.getElementById(id);
  const escapeHtml = s => String(s ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const fallbackMethods=()=>({
    tarot:{method_id:'tarot',name:rt('tarot','Tarot'),description:rt('tarot_desc','Interpret positions and orientations.'),spreads:[
      {id:'single',name:rt('single','Single guidance'),card_count:1},{id:'three_card',name:rt('three_card','Past · Present · Future'),card_count:3},{id:'decision',name:rt('decision','Decision'),card_count:3}]},
    lenormand:{method_id:'lenormand',name:rt('lenormand','Lenormand'),description:rt('lenormand_desc','Prioritize combinations and structure.'),spreads:[
      {id:'yes_no',name:rt('yes_no','Yes / No'),card_count:1},{id:'three',name:rt('three','Three cards'),card_count:3},{id:'five',name:rt('five','Five-card line'),card_count:5},{id:'box9',name:rt('box9','Nine-card box'),card_count:9}]}
  });

  function hexRgb(hex){
    const s=String(hex||'').replace('#','');
    if(!/^[0-9a-f]{6}$/i.test(s)) return [245,241,232];
    return [parseInt(s.slice(0,2),16),parseInt(s.slice(2,4),16),parseInt(s.slice(4,6),16)];
  }
  function mix(a,b,t){return a.map((v,i)=>Math.round(v+(b[i]-v)*t));}
  function rgb(v,alpha=1){return alpha===1?`rgb(${v.join(',')})`:`rgba(${v.join(',')},${alpha})`;}

  async function loadExperienceIdentity(){
    const defaultTheme=state.deck==='leopardcat'?'leopardcat':'minimal-light';
    if(!state.theme && state.deck!=='leopardcat'){
      try{
        const deckResp=await fetch(`/api/v1/decks/${encodeURIComponent(state.deck)}`,{cache:'no-store'});
        if(deckResp.ok){const deck=await deckResp.json();state.theme=deck.default_theme||defaultTheme;}
      }catch(_){}
    }
    state.theme=state.theme||defaultTheme;
    try{
      const [brandResp,themeResp]=await Promise.all([
        fetch(`/api/v1/brands/${encodeURIComponent(state.deck)}`,{cache:'no-store'}),
        fetch(`/api/v1/themes/${encodeURIComponent(state.theme)}`,{cache:'no-store'})
      ]);
      if(brandResp.ok) state.brand=await brandResp.json();
      if(themeResp.ok){
        const t=await themeResp.json();
        const c=t.colors||{};
        const bg=c.background||'#f5f1e8', surface=c.surface||'#ffffff', accent=c.accent||'#6e5138', text=c.text||'#28231e';
        const bgRgb=hexRgb(bg), textRgb=hexRgb(text), surfaceRgb=hexRgb(surface);
        const root=document.documentElement;
        root.style.setProperty('--bg',bg);
        root.style.setProperty('--paper',surface);
        root.style.setProperty('--ink',text);
        root.style.setProperty('--accent',accent);
        root.style.setProperty('--muted',rgb(mix(textRgb,bgRgb,.42)));
        root.style.setProperty('--line',rgb(mix(textRgb,bgRgb,.72),.65));
        root.style.setProperty('--soft',rgb(mix(surfaceRgb,bgRgb,.45)));
        root.style.setProperty('--danger','#b85b50');
        document.body.style.backgroundImage=t.background_image?`linear-gradient(${bg}dd,${bg}ee),url("${t.background_image}")`:'';
        document.body.style.backgroundColor=bg;
        state.theme=t.theme_id||state.theme;
      }
    }catch(_){}

    const brandName=state.brand?.short_name||state.brand?.app_name||(state.deck==='leopardcat'?'靈山靈貓':'Divination OS');
    $('brand-link').textContent=brandName;
    $('brand-link').href=state.deck==='leopardcat'?'/':`/?deck=${encodeURIComponent(state.deck)}`;
    $('back-to-deck').href=$('brand-link').href;
    $('back-to-deck').textContent=state.deck==='leopardcat'?rt('back_leopardcat','Back to LeopardCat Tarot'):rt('back_custom','Back to deck home');
    document.title=rt('ask_master_title','{brand} · Ask the Master',{brand:brandName});
    document.body.dataset.deck=state.deck;
  }

  async function loadMethods(){
    try{
      const r=await fetch('/api/v1/methods',{cache:'no-store'}); if(!r.ok) throw new Error();
      const d=await r.json(); state.methods=Object.fromEntries((d.methods||[]).map(x=>[x.method_id,x]));
    }catch(_){ state.methods=fallbackMethods(); }
    if(!state.methods[state.method]) state.method='tarot';
    renderMethod();
  }

  async function loadDeckAndPersonas(){
    if(state.method==='tarot'){
      try{
        const r=await fetch(`/api/v1/decks/${encodeURIComponent(state.deck)}`,{cache:'no-store'});
        if(r.ok){
          const d=await r.json();
          $('experience-label').textContent=d.name || 'TAROT';
          $('experience-subtitle').textContent=d.description || rt('deck_default_subtitle','Ask your question, then choose a spread. Other settings can wait.');
          const opt=document.createElement('option'); opt.value=d.deck_id; opt.textContent=d.name;
          $('deck-select').innerHTML=''; $('deck-select').appendChild(opt); $('deck-select').value=d.deck_id;
        }
      }catch(_){}
    } else {
      $('experience-label').textContent=rt('lenormand_label','LENORMAND · 36 SYMBOLS');
      $('experience-subtitle').textContent=rt('lenormand_subtitle','Lenormand emphasizes relationships between cards.');
    }
    try{
      const deckForPersona=state.method==='tarot'?state.deck:'leopardcat';
      const r=await fetch(`/api/v1/personas?deck=${encodeURIComponent(deckForPersona)}`,{cache:'no-store'}); if(!r.ok) throw new Error();
      const d=await r.json();
      const compatible=(d.personas||[]).filter(p=>(p.methods||['tarot']).includes(state.method));
      const list=compatible.length?compatible:[{persona_id:'master',name:rt('generic_reader','General reader')}];
      $('persona-select').innerHTML=list.map(p=>`<option value="${escapeHtml(p.persona_id)}">${escapeHtml(p.name)}</option>`).join('');
      const requested=state.persona && list.some(p=>p.persona_id===state.persona) ? state.persona : '';
      const deckDefault=d.default_persona && list.some(p=>p.persona_id===d.default_persona) ? d.default_persona : '';
      const desired=requested || deckDefault || (list.some(p=>p.persona_id==='master') ? 'master' : list[0].persona_id);
      state.persona=desired; $('persona-select').value=desired;
    }catch(_){ $('persona-select').innerHTML=`<option value="master">${escapeHtml(rt('generic_reader','General reader'))}</option>`; state.persona='master'; }
  }

  function renderMethod(){
    document.querySelectorAll('[data-method]').forEach(b=>b.classList.toggle('active',b.dataset.method===state.method));
    $('tarot-advanced').classList.toggle('hidden',state.method!=='tarot');
    const method=state.methods[state.method]||fallbackMethods()[state.method];
    $('method-hint').textContent=rt(state.method+'_desc',method.description||'');
    if(!method.spreads.some(x=>x.id===state.spread)) state.spread=method.spreads[0].id;
    $('spread-options').innerHTML=method.spreads.map(s=>`<button type="button" class="spread ${s.id===state.spread?'active':''}" data-spread="${escapeHtml(s.id)}"><strong>${escapeHtml(rt(s.id,s.name))}</strong><span>${escapeHtml(rt('cards_count','{count} cards',{count:s.card_count}))}</span></button>`).join('');
    $('spread-options').querySelectorAll('[data-spread]').forEach(b=>b.onclick=()=>{state.spread=b.dataset.spread;renderMethod();});
    loadDeckAndPersonas();
  }

  document.querySelectorAll('[data-method]').forEach(b=>b.onclick=()=>{state.method=b.dataset.method;state.spread='';state.persona='';renderMethod();});
  $('deck-select').onchange=e=>{state.deck=e.target.value;state.persona='';loadDeckAndPersonas();};
  $('persona-select').onchange=e=>state.persona=e.target.value;

  function titleOf(card){ const t=card.title||{}; return typeof t==='string'?t:(t['zh-TW']||t.zh||t.en||card.card_id||''); }
  function renderCards(result){
    $('cards').innerHTML=(result.cards||[]).map(card=>{
      const reversed=card.orientation==='reversed';
      const visual=card.image?`<img class="card-art" src="${escapeHtml(card.image)}" alt="">`:`<div class="card-art">${escapeHtml(card.icon||'✦')}</div>`;
      const meta=result.method==='lenormand' ? (card.keywords||[]).join(' · ') : (reversed?rt('reversed','Reversed'):rt('upright','Upright'));
      return `<article class="draw-card ${reversed?'reversed':''}"><div><div class="card-position">${escapeHtml(card.position_label||'')}</div>${visual}</div><div><div class="card-name">${escapeHtml(titleOf(card))}</div><div class="card-meta">${escapeHtml(meta)}</div></div></article>`;
    }).join('');
    renderStructure(result);
  }

  function renderStructure(result){
    const el=$('structure');
    if(result.method!=='lenormand'){el.classList.add('hidden');el.innerHTML='';return;}
    const s=result.structure||{}; const lines=[];
    if(s.answer_tendency){const value=s.answer_tendency==='yes'?rt('yes','Yes'):s.answer_tendency==='no'?rt('no','No'):rt('unclear','Unclear');lines.push(rt('answer_tendency','Answer tendency: {value}',{value}));}
    if(s.center_card) lines.push(rt('center_card','Center card: {value}',{value:s.center_card}));
    if((s.adjacent_pairs||[]).length) lines.push(rt('adjacent_pairs','Adjacent pairs: {value}',{value:s.adjacent_pairs.map(x=>x.phrase).join(' ／ ')}));
    if(s.reading_order) lines.push(rt('reading_order','Reading order: {value}',{value:s.reading_order.join(' → ')}));
    el.innerHTML=lines.map(x=>`<div>${escapeHtml(x)}</div>`).join(''); el.classList.toggle('hidden',!lines.length);
  }

  function cleanReading(text){
    let quote='';
    let cleaned=String(text||'').replace(/<div\b[^>]*class=["'][^"']*hidden-quote[^"']*["'][^>]*>([\s\S]*?)<\/div>/gi,(_,q)=>{quote=String(q||'').replace(/<[^>]*>/g,'').replace(/[\[\]]/g,'').trim();return '';});
    cleaned=cleaned.replace(/<\/?(?:div|span|p|br)\b[^>]*>/gi,'').trim();
    return {text:cleaned,quote};
  }

  function readingHtml(text){
    const parsed=cleanReading(text);
    const safe=escapeHtml(parsed.text).replace(/\n\n+/g,'</p><p>').replace(/\n/g,'<br>');
    const quote=parsed.quote?`<blockquote class="golden-quote">${escapeHtml(parsed.quote)}</blockquote>`:'';
    return {html:(safe?`<p>${safe}</p>`:`<p>${escapeHtml(rt('reading_saved','The draw is complete and preserved.'))}</p>`)+quote,plain:parsed.text,quote:parsed.quote};
  }

  function renderReading(text){
    const rendered=readingHtml(text);
    $('reading').innerHTML=rendered.html;
    return rendered;
  }

  function renderHandoff(handoff){
    state.handoff=handoff;
    if(!handoff){$('handoff').classList.add('hidden');return;}
    $('handoff').classList.remove('hidden'); $('capsule-json').textContent=JSON.stringify(handoff.capsule,null,2);
    $('provider-actions').innerHTML=(handoff.providers||[]).map(p=>`<button class="provider-btn" data-provider="${escapeHtml(p.id)}">${escapeHtml(p.name)}</button>`).join('');
    $('provider-actions').querySelectorAll('[data-provider]').forEach(b=>b.onclick=async()=>{
      const p=(handoff.providers||[]).find(x=>x.id===b.dataset.provider); if(!p)return;
      try{await navigator.clipboard.writeText(p.prompt);b.textContent=rt('copied_opening','Copied, opening…');}catch(_){}
      window.open(p.url,'_blank','noopener'); setTimeout(()=>b.textContent=p.name,1000);
    });
    $('copy-prompt').onclick=async()=>{await navigator.clipboard.writeText(handoff.generic_prompt||'');$('copy-prompt').textContent=rt('copied','Copied');setTimeout(()=>$('copy-prompt').textContent=rt('copy_prompt','Copy full prompt only'),1200);};
  }

  function appendFollowup(role,text){
    const rendered=readingHtml(text);
    const node=document.createElement('div');
    node.className=`followup-bubble ${role}`;
    node.innerHTML=role==='assistant'?rendered.html:`<p>${escapeHtml(text)}</p>`;
    $('followup-history').appendChild(node);
    node.scrollIntoView({behavior:'smooth',block:'nearest'});
  }

  function configureFollowup(){
    const available=!!(state.envelope?.reading_id && state.envelope?.session_token);
    $('followup').classList.toggle('hidden',!available);
  }

  async function askFollowup(){
    const text=$('followup-input').value.trim();
    if(!text || !state.envelope?.reading_id || !state.envelope?.session_token) return;
    $('followup-send').disabled=true;$('followup-status').textContent=rt('followup_wait','The Master is responding…');
    appendFollowup('user',text);$('followup-input').value='';
    try{
      const payload={readingId:state.envelope.reading_id,sessionToken:state.envelope.session_token,question:text,lang:aiLang(),history:state.history.slice(-10)};
      const r=await fetch('/api/v1/readings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      let data={};try{data=await r.json();}catch(_){}
      if(!r.ok && !data.method_result) throw new Error(data.message||rt('master_unavailable','The Master is temporarily unavailable; your draw is preserved.'));
      if(data.reading){
        appendFollowup('assistant',data.reading);
        const clean=cleanReading(data.reading).text;
        state.history.push({role:'user',content:text},{role:'assistant',content:clean});
        $('followup-status').textContent='';
      }else{
        $('followup-status').textContent=rt('master_unavailable_preserved','The Master is temporarily unavailable. Your draw was not repeated.');
        $('ai-fallback').classList.remove('hidden');
        if(data.handoff) renderHandoff(data.handoff);
      }
    }catch(e){$('followup-status').textContent=e.message||rt('master_unavailable','The Master is temporarily unavailable; your draw is preserved.');}
    finally{$('followup-send').disabled=false;}
  }

  async function draw(){
    const question=$('question').value.trim(); if(!question){$('status').textContent=rt('question_required','Write your question first.');$('status').className='status error';return;}
    $('draw').disabled=true;$('status').className='status';$('status').textContent=rt('drawing','Drawing cards…');
    const payload={method:state.method,persona:state.persona||'master',question,lang:aiLang(),input:{spread:state.spread}};
    if(state.method==='tarot') payload.input.deck_id=state.deck;
    try{
      const r=await fetch('/api/v1/readings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      let data={};try{data=await r.json();}catch(_){}
      if(!r.ok && !data.method_result) throw new Error(data.message||rt('draw_failed','Unable to draw right now.'));
      state.envelope=data; const result=data.method_result||data.capsule?.result;
      if(!result) throw new Error(rt('no_result','No draw result was returned.'));
      state.lastResult=result; renderCards(result); const initial=renderReading(data.reading||''); renderHandoff(data.handoff||null);
      state.history=data.reading?[{role:'user',content:question},{role:'assistant',content:initial.plain}]:[];
      $('followup-history').innerHTML='';configureFollowup();
      $('ai-fallback').classList.toggle('hidden',r.ok && !!data.reading);
      $('ai-state').textContent=r.ok&&data.reading?rt('site_master','Site Master'):rt('draw_preserved','Draw preserved'); $('ai-state').classList.toggle('offline',!r.ok||!data.reading);
      $('result-title').textContent=result.method==='lenormand'?(result.spread_name||rt('lenormand_result','Lenormand spread')):`${result.deck?.name||rt('tarot','Tarot')} · ${rt('cards_count','{count} cards',{count:result.cards.length})}`;
      $('result').classList.remove('hidden'); $('status').textContent=''; $('result').scrollIntoView({behavior:'smooth',block:'start'});
      const u=new URL(location.href);u.searchParams.set('method',state.method);if(state.method==='tarot')u.searchParams.set('deck',state.deck);else u.searchParams.delete('deck');u.searchParams.set('persona',state.persona);if(state.theme)u.searchParams.set('theme',state.theme);history.replaceState({},'',u);
    }catch(e){$('status').className='status error';$('status').textContent=e.message||rt('generic_error','An error occurred.');}
    finally{$('draw').disabled=false;}
  }

  $('draw').onclick=draw;
  $('followup-send').onclick=askFollowup;
  $('followup-input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();askFollowup();}});
  $('new-reading').onclick=()=>{$('result').classList.add('hidden');state.envelope=null;state.history=[];$('followup-history').innerHTML='';$('question').focus();window.scrollTo({top:0,behavior:'smooth'});};
  loadReadLocale().then(()=>loadExperienceIdentity()).finally(loadMethods);
})();
