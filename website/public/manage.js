(() => {
  const localeMeta={zh:{label:'中',html:'zh-TW'},en:{label:'EN',html:'en'},ja:{label:'日本語',html:'ja'},ko:{label:'한국어',html:'ko'},es:{label:'ES',html:'es'}};
  let localeCatalog={}; let currentLang='zh';
  const resolveLang=v=>{const n=String(v||'').toLowerCase().replace('_','-'),f=n.split('-')[0];return localeCatalog[n]?n:(localeCatalog[f]?f:(localeCatalog.zh?'zh':'en'));};
  const mt=(key,fallback='',params={})=>String(localeCatalog[currentLang]?.manage?.[key]??fallback).replace(/\{(\w+)\}/g,(_,k)=>params[k]??`{${k}}`);
  const apiMessage=(data,key,fallback)=>currentLang==='zh'&&data?.message?data.message:mt(key,fallback);
  function applyManageLocale(){document.documentElement.lang=localeMeta[currentLang]?.html||currentLang;document.title=mt('page_title','Manage My Divination Content');document.querySelectorAll('[data-manage-i18n]').forEach(el=>el.textContent=mt(el.dataset.manageI18n,el.textContent));const sel=document.getElementById('manage-language');if(sel){sel.innerHTML=Object.keys(localeCatalog).filter(x=>localeMeta[x]).map(x=>`<option value=\"${x}\" ${x===currentLang?'selected':''}>${localeMeta[x].label}</option>`).join('');sel.onchange=()=>setManageLanguage(sel.value);}if(current)fill(current);}
  function setManageLanguage(lang){currentLang=resolveLang(lang);localStorage.setItem('leopard-lang',currentLang);applyManageLocale();}
  async function loadManageLocale(){try{const r=await fetch('/locales_v10.json',{cache:'no-store'});localeCatalog=await r.json();}catch(_){localeCatalog={zh:{manage:{}}};}currentLang=resolveLang(localStorage.getItem('leopard-lang')||navigator.language||'zh');applyManageLocale();}

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
      $('resource-chip').textContent=mt('deck_chip','Deck'); $('resource-title').textContent=data.name; $('resource-meta').textContent=mt('cards_meta','{count} cards · {id}',{count:data.card_count,id:data.deck_id});
      $('deck-fields').classList.remove('hidden'); $('persona-fields').classList.add('hidden');
      $('deck-name').value=data.name||''; $('deck-creator').value=data.creator||''; $('deck-description').value=data.description||''; $('deck-persona').value=data.default_persona||'master';
    } else {
      $('resource-chip').textContent=mt('persona_chip','Reader'); $('resource-title').textContent=data.name; $('resource-meta').textContent=data.persona_id;
      $('persona-fields').classList.remove('hidden'); $('deck-fields').classList.add('hidden');
      $('persona-name').value=data.name||''; $('persona-role').value=data.role||''; $('persona-voice').value=data.voice||''; $('persona-principles').value=data.principles||''; $('persona-worldview').value=data.worldview||''; $('persona-closing').value=data.closing||'';
    }
  }

  async function load(){
    if(!type || !id || !token){showMissing();return;}
    try{
      const r=await fetch(api(),{headers:headers(),cache:'no-store'}); const d=await r.json();
      if(!r.ok) throw new Error(apiMessage(d,'invalid_link','The management link is invalid or has expired.')); fill(d);
    }catch(e){$('loading').classList.add('hidden');$('missing').classList.remove('hidden');$('missing').innerHTML=`<h2>${mt('open_failed','Unable to open management page')}</h2><p class="notice">${String(e.message||e)}</p>`;}
  }

  $('save').onclick=async()=>{
    const payload=current.resource_type==='deck'?{
      name:$('deck-name').value.trim(),creator:$('deck-creator').value.trim(),description:$('deck-description').value.trim(),persona:$('deck-persona').value.trim()
    }:{
      name:$('persona-name').value.trim(),role:$('persona-role').value.trim(),voice:$('persona-voice').value.trim(),principles:$('persona-principles').value.trim(),worldview:$('persona-worldview').value.trim(),closing:$('persona-closing').value.trim()
    };
    status(mt('saving','Saving…'));
    try{const r=await fetch(api(),{method:'PATCH',headers:headers(),body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)throw new Error(apiMessage(d,'save_failed','Save failed'));fill(d);status(mt('saved','✓ Saved.'));}catch(e){status(e.message||mt('save_failed','Save failed'),true);}
  };

  $('rotate').onclick=async()=>{
    if(!confirm(mt('rotate_confirm','Rotating the management key immediately invalidates this link. Continue?')))return;
    status(mt('rotating','Rotating key…'));
    try{
      const r=await fetch(api()+'/rotate',{method:'POST',headers:headers(),body:'{}'}); const d=await r.json(); if(!r.ok)throw new Error(apiMessage(d,'rotate_failed','Rotation failed'));
      const u=new URL(d.manage_path,location.origin);u.hash='token='+encodeURIComponent(d.management_token);$('new-manage-link').href=u.href;$('new-manage-link').textContent=u.href;$('rotated').classList.remove('hidden');$('editor').classList.add('hidden');history.replaceState({},'',u.href);
    }catch(e){status(e.message||mt('rotate_failed','Rotation failed'),true);}
  };

  $('copy-new').onclick=async()=>{await navigator.clipboard.writeText($('new-manage-link').href);$('copy-new').textContent=mt('copied','Copied');};

  $('delete').onclick=async()=>{
    const label=current?.name||id; if(!confirm(mt('delete_confirm','Permanently delete “{name}”? This cannot be undone.',{name:label})))return;
    const typed=prompt(mt('delete_prompt','Type DELETE to confirm deleting “{name}”',{name:label})); if(typed!=='DELETE')return;
    status(mt('deleting','Deleting…'));
    try{const r=await fetch(api(),{method:'DELETE',headers:headers()});let d={};try{d=await r.json();}catch(_){}if(!r.ok)throw new Error(apiMessage(d,'delete_failed','Delete failed'));$('editor').innerHTML=`<h2>${mt('deleted','Deleted')}</h2><p class="notice">${mt('deleted_note','This content has been removed from the platform.')}</p>`;}
    catch(e){status(e.message||mt('delete_failed','Delete failed'),true);}
  };

  loadManageLocale().then(load);
})();
