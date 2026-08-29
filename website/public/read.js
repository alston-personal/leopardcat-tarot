(() => {
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
  };
  const $ = id => document.getElementById(id);
  const escapeHtml = s => String(s ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const FALLBACK_METHODS = {
    tarot: {method_id:'tarot', name:'塔羅 Tarot', description:'以牌陣位置與正逆位解讀。', spreads:[
      {id:'single',name:'單張指引',card_count:1},{id:'three_card',name:'過去・現在・未來',card_count:3},{id:'decision',name:'選擇題',card_count:3}
    ]},
    lenormand: {method_id:'lenormand',name:'雷諾曼 Lenormand',description:'以相鄰組合與結構優先解讀。',spreads:[
      {id:'yes_no',name:'是／否',card_count:1},{id:'three',name:'三張牌',card_count:3},{id:'five',name:'五張線性',card_count:5},{id:'box9',name:'九宮格',card_count:9}
    ]}
  };

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
    $('back-to-deck').textContent=state.deck==='leopardcat'?'返回石虎塔羅':'返回牌組首頁';
    document.title=`${brandName}・詢問大師`;
    document.body.dataset.deck=state.deck;
  }

  async function loadMethods(){
    try{
      const r=await fetch('/api/v1/methods',{cache:'no-store'}); if(!r.ok) throw new Error();
      const d=await r.json(); state.methods=Object.fromEntries((d.methods||[]).map(x=>[x.method_id,x]));
    }catch(_){ state.methods=FALLBACK_METHODS; }
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
          $('experience-subtitle').textContent=d.description || '先問問題，再選牌陣。其他設定都可以之後再看。';
          const opt=document.createElement('option'); opt.value=d.deck_id; opt.textContent=d.name;
          $('deck-select').innerHTML=''; $('deck-select').appendChild(opt); $('deck-select').value=d.deck_id;
        }
      }catch(_){}
    } else {
      $('experience-label').textContent='LENORMAND · 36 SYMBOLS';
      $('experience-subtitle').textContent='雷諾曼重視牌與牌之間的關係。系統會保留相鄰組合、中心與九宮格結構。';
    }
    try{
      const deckForPersona=state.method==='tarot'?state.deck:'leopardcat';
      const r=await fetch(`/api/v1/personas?deck=${encodeURIComponent(deckForPersona)}`,{cache:'no-store'}); if(!r.ok) throw new Error();
      const d=await r.json();
      const compatible=(d.personas||[]).filter(p=>(p.methods||['tarot']).includes(state.method));
      const list=compatible.length?compatible:[{persona_id:'master',name:'通用解牌師'}];
      $('persona-select').innerHTML=list.map(p=>`<option value="${escapeHtml(p.persona_id)}">${escapeHtml(p.name)}</option>`).join('');
      const requested=state.persona && list.some(p=>p.persona_id===state.persona) ? state.persona : '';
      const deckDefault=d.default_persona && list.some(p=>p.persona_id===d.default_persona) ? d.default_persona : '';
      const desired=requested || deckDefault || (list.some(p=>p.persona_id==='master') ? 'master' : list[0].persona_id);
      state.persona=desired; $('persona-select').value=desired;
    }catch(_){ $('persona-select').innerHTML='<option value="master">通用解牌師</option>'; state.persona='master'; }
  }

  function renderMethod(){
    document.querySelectorAll('[data-method]').forEach(b=>b.classList.toggle('active',b.dataset.method===state.method));
    $('tarot-advanced').classList.toggle('hidden',state.method!=='tarot');
    const method=state.methods[state.method]||FALLBACK_METHODS[state.method];
    $('method-hint').textContent=method.description||'';
    if(!method.spreads.some(x=>x.id===state.spread)) state.spread=method.spreads[0].id;
    $('spread-options').innerHTML=method.spreads.map(s=>`<button type="button" class="spread ${s.id===state.spread?'active':''}" data-spread="${escapeHtml(s.id)}"><strong>${escapeHtml(s.name)}</strong><span>${s.card_count} 張牌</span></button>`).join('');
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
      const meta=result.method==='lenormand' ? (card.keywords||[]).join(' · ') : (reversed?'逆位':'正位');
      return `<article class="draw-card ${reversed?'reversed':''}"><div><div class="card-position">${escapeHtml(card.position_label||'')}</div>${visual}</div><div><div class="card-name">${escapeHtml(titleOf(card))}</div><div class="card-meta">${escapeHtml(meta)}</div></div></article>`;
    }).join('');
    renderStructure(result);
  }

  function renderStructure(result){
    const el=$('structure');
    if(result.method!=='lenormand'){el.classList.add('hidden');el.innerHTML='';return;}
    const s=result.structure||{}; const lines=[];
    if(s.answer_tendency) lines.push(`答案傾向：${s.answer_tendency==='yes'?'是':s.answer_tendency==='no'?'否':'尚不明確'}`);
    if(s.center_card) lines.push(`中心牌：${s.center_card}`);
    if((s.adjacent_pairs||[]).length) lines.push('相鄰組合：'+s.adjacent_pairs.map(x=>x.phrase).join(' ／ '));
    if(s.reading_order) lines.push('解讀順序：'+s.reading_order.join(' → '));
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
    return {html:(safe?`<p>${safe}</p>`:'<p>抽牌完成。牌局已保留，你可以稍後繼續詢問大師。</p>')+quote,plain:parsed.text,quote:parsed.quote};
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
      try{await navigator.clipboard.writeText(p.prompt);b.textContent='已複製，正在開啟…';}catch(_){}
      window.open(p.url,'_blank','noopener'); setTimeout(()=>b.textContent=p.name,1000);
    });
    $('copy-prompt').onclick=async()=>{await navigator.clipboard.writeText(handoff.generic_prompt||'');$('copy-prompt').textContent='已複製';setTimeout(()=>$('copy-prompt').textContent='只複製完整提示',1200);};
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
    $('followup-send').disabled=true;$('followup-status').textContent='大師正在回應…';
    appendFollowup('user',text);$('followup-input').value='';
    try{
      const payload={readingId:state.envelope.reading_id,sessionToken:state.envelope.session_token,question:text,lang:'zh-TW',history:state.history.slice(-10)};
      const r=await fetch('/api/v1/readings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      let data={};try{data=await r.json();}catch(_){}
      if(!r.ok && !data.method_result) throw new Error(data.message||'大師暫時無法回應，牌局仍然保留。');
      if(data.reading){
        appendFollowup('assistant',data.reading);
        const clean=cleanReading(data.reading).text;
        state.history.push({role:'user',content:text},{role:'assistant',content:clean});
        $('followup-status').textContent='';
      }else{
        $('followup-status').textContent='大師目前暫時無法回應；牌局沒有重抽，你可以稍後再問。';
        $('ai-fallback').classList.remove('hidden');
        if(data.handoff) renderHandoff(data.handoff);
      }
    }catch(e){$('followup-status').textContent=e.message||'大師暫時無法回應，牌局仍然保留。';}
    finally{$('followup-send').disabled=false;}
  }

  async function draw(){
    const question=$('question').value.trim(); if(!question){$('status').textContent='先寫下你想問的問題。';$('status').className='status error';return;}
    $('draw').disabled=true;$('status').className='status';$('status').textContent='正在抽牌…';
    const payload={method:state.method,persona:state.persona||'master',question,lang:'zh-TW',input:{spread:state.spread}};
    if(state.method==='tarot') payload.input.deck_id=state.deck;
    try{
      const r=await fetch('/api/v1/readings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      let data={};try{data=await r.json();}catch(_){}
      if(!r.ok && !data.method_result) throw new Error(data.message||'目前無法抽牌，請稍後再試。');
      state.envelope=data; const result=data.method_result||data.capsule?.result;
      if(!result) throw new Error('沒有收到抽牌結果。');
      renderCards(result); const initial=renderReading(data.reading||''); renderHandoff(data.handoff||null);
      state.history=data.reading?[{role:'user',content:question},{role:'assistant',content:initial.plain}]:[];
      $('followup-history').innerHTML='';configureFollowup();
      $('ai-fallback').classList.toggle('hidden',r.ok && !!data.reading);
      $('ai-state').textContent=r.ok&&data.reading?'本站大師':'牌局已保留'; $('ai-state').classList.toggle('offline',!r.ok||!data.reading);
      $('result-title').textContent=result.method==='lenormand'?(result.spread_name||'雷諾曼牌陣'):`${result.deck?.name||'塔羅'} · ${result.cards.length} 張`;
      $('result').classList.remove('hidden'); $('status').textContent=''; $('result').scrollIntoView({behavior:'smooth',block:'start'});
      const u=new URL(location.href);u.searchParams.set('method',state.method);if(state.method==='tarot')u.searchParams.set('deck',state.deck);else u.searchParams.delete('deck');u.searchParams.set('persona',state.persona);if(state.theme)u.searchParams.set('theme',state.theme);history.replaceState({},'',u);
    }catch(e){$('status').className='status error';$('status').textContent=e.message||'發生錯誤。';}
    finally{$('draw').disabled=false;}
  }

  $('draw').onclick=draw;
  $('followup-send').onclick=askFollowup;
  $('followup-input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();askFollowup();}});
  $('new-reading').onclick=()=>{$('result').classList.add('hidden');state.envelope=null;state.history=[];$('followup-history').innerHTML='';$('question').focus();window.scrollTo({top:0,behavior:'smooth'});};
  loadExperienceIdentity().finally(loadMethods);
})();
