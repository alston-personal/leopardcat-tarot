(() => {
  const qs = new URLSearchParams(location.search);
  const state = {
    method: qs.get('method') || 'tarot',
    spread: '',
    deck: qs.get('deck') || 'leopardcat',
    persona: qs.get('persona') || '',
    methods: {},
    handoff: null,
    envelope: null,
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

  function renderReading(text){
    const safe=escapeHtml(text||'').replace(/\n\n+/g,'</p><p>').replace(/\n/g,'<br>');
    $('reading').innerHTML=safe?`<p>${safe}</p>`:'<p>抽牌完成。你可以使用自己的 AI 解讀這份 Reading Capsule。</p>';
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
      renderCards(result); renderReading(data.reading||''); renderHandoff(data.handoff||null);
      $('ai-fallback').classList.toggle('hidden',r.ok && !!data.reading);
      $('ai-state').textContent=r.ok&&data.reading?'本站 AI':'自己的 AI 可用'; $('ai-state').classList.toggle('offline',!r.ok||!data.reading);
      $('result-title').textContent=result.method==='lenormand'?(result.spread_name||'雷諾曼牌陣'):`${result.deck?.name||'塔羅'} · ${result.cards.length} 張`;
      $('result').classList.remove('hidden'); $('status').textContent=''; $('result').scrollIntoView({behavior:'smooth',block:'start'});
      const u=new URL(location.href);u.searchParams.set('method',state.method);if(state.method==='tarot')u.searchParams.set('deck',state.deck);else u.searchParams.delete('deck');u.searchParams.set('persona',state.persona);history.replaceState({},'',u);
    }catch(e){$('status').className='status error';$('status').textContent=e.message||'發生錯誤。';}
    finally{$('draw').disabled=false;}
  }

  $('draw').onclick=draw;
  $('new-reading').onclick=()=>{$('result').classList.add('hidden');$('question').focus();window.scrollTo({top:0,behavior:'smooth'});};
  loadMethods();
})();
