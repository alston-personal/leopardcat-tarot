(() => {
  const qs = new URLSearchParams(location.search);
  const frag = new URLSearchParams(location.hash.replace(/^#/,''));
  const token = frag.get('token') || '';
  const deckId = qs.get('deck');
  const personaId = qs.get('persona');
  const type = deckId ? 'decks' : (personaId ? 'personas' : '');
  const id = deckId || personaId || '';
  let current = null;
  const $ = id => document.getElementById(id);
  const headers = () => ({'X-Management-Token': token, 'Content-Type':'application/json'});
  const api = () => `/api/v1/manage/${type}/${encodeURIComponent(id)}`;

  function showMissing(){ $('loading').classList.add('hidden'); $('editor').classList.add('hidden'); $('missing').classList.remove('hidden'); }
  function status(text, error=false){ $('status').textContent=text; $('status').className='status'+(error?' error':''); }

  function fill(data){
    current=data; $('loading').classList.add('hidden'); $('missing').classList.add('hidden'); $('editor').classList.remove('hidden');
    if(data.resource_type==='deck'){
      $('resource-chip').textContent='牌組'; $('resource-title').textContent=data.name; $('resource-meta').textContent=`${data.card_count} 張牌 · ${data.deck_id}`;
      $('deck-fields').classList.remove('hidden'); $('persona-fields').classList.add('hidden');
      $('deck-name').value=data.name||''; $('deck-creator').value=data.creator||''; $('deck-description').value=data.description||''; $('deck-persona').value=data.default_persona||'master';
    } else {
      $('resource-chip').textContent='解牌師'; $('resource-title').textContent=data.name; $('resource-meta').textContent=data.persona_id;
      $('persona-fields').classList.remove('hidden'); $('deck-fields').classList.add('hidden');
      $('persona-name').value=data.name||''; $('persona-role').value=data.role||''; $('persona-voice').value=data.voice||''; $('persona-principles').value=data.principles||''; $('persona-worldview').value=data.worldview||''; $('persona-closing').value=data.closing||'';
    }
  }

  async function load(){
    if(!type || !id || !token){showMissing();return;}
    try{
      const r=await fetch(api(),{headers:headers(),cache:'no-store'}); const d=await r.json();
      if(!r.ok) throw new Error(d.message||'管理連結無效或已失效。'); fill(d);
    }catch(e){$('loading').classList.add('hidden');$('missing').classList.remove('hidden');$('missing').innerHTML=`<h2>無法開啟管理頁</h2><p class="notice">${String(e.message||e)}</p>`;}
  }

  $('save').onclick=async()=>{
    const payload=current.resource_type==='deck'?{
      name:$('deck-name').value.trim(),creator:$('deck-creator').value.trim(),description:$('deck-description').value.trim(),persona:$('deck-persona').value.trim()
    }:{
      name:$('persona-name').value.trim(),role:$('persona-role').value.trim(),voice:$('persona-voice').value.trim(),principles:$('persona-principles').value.trim(),worldview:$('persona-worldview').value.trim(),closing:$('persona-closing').value.trim()
    };
    status('正在儲存…');
    try{const r=await fetch(api(),{method:'PATCH',headers:headers(),body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)throw new Error(d.message||'儲存失敗');fill(d);status('✓ 已儲存。');}catch(e){status(e.message||'儲存失敗',true);}
  };

  $('rotate').onclick=async()=>{
    if(!confirm('更換管理金鑰後，現在這條管理連結會立刻失效。確定繼續？'))return;
    status('正在更換金鑰…');
    try{
      const r=await fetch(api()+'/rotate',{method:'POST',headers:headers(),body:'{}'}); const d=await r.json(); if(!r.ok)throw new Error(d.message||'更換失敗');
      const u=new URL(d.manage_path,location.origin);u.hash='token='+encodeURIComponent(d.management_token);$('new-manage-link').href=u.href;$('new-manage-link').textContent=u.href;$('rotated').classList.remove('hidden');$('editor').classList.add('hidden');history.replaceState({},'',u.href);
    }catch(e){status(e.message||'更換失敗',true);}
  };

  $('copy-new').onclick=async()=>{await navigator.clipboard.writeText($('new-manage-link').href);$('copy-new').textContent='已複製';};

  $('delete').onclick=async()=>{
    const label=current?.name||id; if(!confirm(`確定永久刪除「${label}」？這個動作不能復原。`))return;
    const typed=prompt(`請輸入 DELETE 確認刪除「${label}」`); if(typed!=='DELETE')return;
    status('正在刪除…');
    try{const r=await fetch(api(),{method:'DELETE',headers:headers()});let d={};try{d=await r.json();}catch(_){}if(!r.ok)throw new Error(d.message||'刪除失敗');$('editor').innerHTML='<h2>已刪除</h2><p class="notice">這項內容已從平台移除。</p>';}
    catch(e){status(e.message||'刪除失敗',true);}
  };

  load();
})();
