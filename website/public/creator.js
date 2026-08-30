(() => {
  const localeMeta={zh:{label:'中',html:'zh-TW',date:'zh-TW'},en:{label:'EN',html:'en',date:'en-US'},ja:{label:'日本語',html:'ja',date:'ja-JP'},ko:{label:'한국어',html:'ko',date:'ko-KR'},es:{label:'ES',html:'es',date:'es-ES'}};
  let localeCatalog={}; let currentLang='zh';
  const resolveLang=v=>{const n=String(v||'').toLowerCase().replace('_','-'),f=n.split('-')[0];return localeCatalog[n]?n:(localeCatalog[f]?f:(localeCatalog.zh?'zh':'en'));};
  const ct=(key,fallback='',params={})=>String(localeCatalog[currentLang]?.creator?.[key]??fallback).replace(/\{(\w+)\}/g,(_,k)=>params[k]??`{${k}}`);
  const creatorLocale=()=>localeMeta[currentLang]?.date||currentLang||'en-US';
  const apiMessage=(data,key,fallback)=>currentLang==='zh'&&data?.message?data.message:ct(key,fallback);
  function applyCreatorLocale(){document.documentElement.lang=localeMeta[currentLang]?.html||currentLang;document.title=ct('page_title','Create My Tarot Reading');document.querySelectorAll('[data-creator-i18n]').forEach(el=>el.textContent=ct(el.dataset.creatorI18n,el.textContent));document.querySelectorAll('[data-creator-placeholder]').forEach(el=>el.placeholder=ct(el.dataset.creatorPlaceholder,el.placeholder));const sel=document.getElementById('creator-language');if(sel){sel.innerHTML=Object.keys(localeCatalog).filter(x=>localeMeta[x]).map(x=>`<option value=\"${x}\" ${x===currentLang?'selected':''}>${localeMeta[x].label}</option>`).join('');sel.onchange=()=>setCreatorLanguage(sel.value);}renderPublishedHistory();if(personas.length)renderPersonaOptions();if(cards.length)render();}
  function setCreatorLanguage(lang){currentLang=resolveLang(lang);localStorage.setItem('leopard-lang',currentLang);applyCreatorLocale();}
  async function loadCreatorLocale(){try{const r=await fetch('/locales_v10.json',{cache:'no-store'});localeCatalog=await r.json();}catch(_){localeCatalog={zh:{creator:{}}};}currentLang=resolveLang(localStorage.getItem('leopard-lang')||navigator.language||'zh');applyCreatorLocale();}

  const images = document.getElementById('images');
  const cardsEl = document.getElementById('cards');
  const section = document.getElementById('cards-section');
  const count = document.getElementById('count');
  const reversals = document.getElementById('reversals');
  const status = document.getElementById('status');
  const done = document.getElementById('done');
  let cards = [];
  const HISTORY_KEY = 'leopardcat-published-decks-v1';
  const MANAGED_KEY = 'divination-managed-resources-v1';
  const deckSlug = document.getElementById('deck-slug');
  const slugStatus = document.getElementById('slug-status');
  const personaOptions = document.getElementById('persona-options');
  const personaStatus = document.getElementById('persona-status');
  const personaCreateBtn = document.getElementById('create-persona');
  const personaCreateStatus = document.getElementById('persona-create-status');
  let slugCheckTimer = null;
  let slugAvailable = null;
  let personas = [];
  let selectedPersonaId = 'master';

  function normalizeSlug(value) {
    return String(value || '').toLowerCase().trim().replace(/[^a-z0-9-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
  }

  async function checkSlugAvailability(force = false) {
    const slug = normalizeSlug(deckSlug.value);
    if (deckSlug.value !== slug) deckSlug.value = slug;
    if (!slug) { slugAvailable = null; slugStatus.textContent = ct('slug_auto','Leave blank and the system will generate the URL.'); return true; }
    if (slug.length < 3) { slugAvailable = false; slugStatus.textContent = ct('slug_min','Enter at least 3 characters.'); return false; }
    slugStatus.textContent = ct('slug_checking','Checking URL…');
    try {
      const r = await fetch(`/api/v1/deck-slugs/${encodeURIComponent(slug)}`, {cache:'no-store'});
      const data = await r.json();
      slugAvailable = !!data.available;
      slugStatus.textContent = data.available ? ct('slug_available','✓ Available: ?deck={slug}',{slug}) : (data.reserved ? ct('slug_reserved','✗ This name is reserved. Choose another.') : ct('slug_used','✗ This name is already in use. Choose another.'));
      slugStatus.style.color = data.available ? '#2d7a3e' : '#a33a32';
      return slugAvailable;
    } catch (_) {
      slugAvailable = null;
      slugStatus.textContent = force ? ct('slug_check_failed','Unable to check the URL right now.') : '';
      return false;
    }
  }

  deckSlug.addEventListener('input', () => {
    slugAvailable = null;
    clearTimeout(slugCheckTimer);
    slugCheckTimer = setTimeout(() => checkSlugAvailability(false), 350);
  });

  function getPublishedHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); }
    catch (_) { return []; }
  }

  function managementUrl(data) {
    if (!data?.management_token || !data?.manage_path) return '';
    const u = new URL(data.manage_path, location.origin);
    u.hash = `token=${encodeURIComponent(data.management_token)}`;
    return u.href;
  }

  function saveManagedResource(entry) {
    try {
      const rows = JSON.parse(localStorage.getItem(MANAGED_KEY) || '[]').filter(x => !(x.type === entry.type && x.id === entry.id));
      rows.unshift(entry);
      localStorage.setItem(MANAGED_KEY, JSON.stringify(rows.slice(0, 100)));
    } catch (_) {}
  }

  function savePublishedHistory(entry) {
    const rows = getPublishedHistory().filter(x => x.deck_id !== entry.deck_id);
    rows.unshift(entry);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(rows.slice(0, 50)));
    renderPublishedHistory();
  }

  function renderPublishedHistory() {
    const el = document.getElementById('published-history');
    if (!el) return;
    const rows = getPublishedHistory();
    if (!rows.length) {
      el.innerHTML = `<p class="muted">${escapeHtml(ct('history_empty','No publishing history in this browser yet.'))}</p>`;
      return;
    }
    el.innerHTML = rows.map(x => {
      const when = x.published_at ? new Date(x.published_at).toLocaleString(creatorLocale()) : '';
      const manage = x.manage_url ? ` · <a href="${escapeHtml(x.manage_url)}">${escapeHtml(ct('manage','Manage'))}</a>` : '';
      return `<div style="padding:10px 0;border-top:1px solid #eee3d4"><strong>${escapeHtml(x.name || x.deck_id)}</strong><div class="muted">${escapeHtml(when)}</div><a href="${escapeHtml(x.url)}" target="_blank">${escapeHtml(ct('open_reading','Open reading page'))}</a>${manage}</div>`;
    }).join('');
  }

  const friendlyName = (filename) => filename.replace(/\.[^.]+$/, '').replace(/^\d+[\s._-]*/, '').replace(/[_-]+/g, ' ').trim();
  const escapeHtml = (s) => String(s || '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

  function renderPersonaOptions() {
    if (!personaOptions) return;
    if (!personas.length) {
      personaOptions.innerHTML = `<p class="muted">${escapeHtml(ct('generic_persona','General reader'))}</p>`;
      selectedPersonaId = 'master';
      return;
    }
    if (!personas.some(x => x.persona_id === selectedPersonaId)) {
      selectedPersonaId = personas.some(x => x.persona_id === 'master') ? 'master' : personas[0].persona_id;
    }
    personaOptions.innerHTML = personas.map(p => `
      <label class="persona-option">
        <input type="radio" name="default-persona" value="${escapeHtml(p.persona_id)}" ${p.persona_id === selectedPersonaId ? 'checked' : ''}>
        <span><strong>${escapeHtml(p.name)}</strong><span class="muted">${escapeHtml(p.role || '')}</span></span>
      </label>`).join('');
    personaOptions.querySelectorAll('input[name="default-persona"]').forEach(el => {
      el.addEventListener('change', () => {
        if (el.checked) {
          selectedPersonaId = el.value;
          const p = personas.find(x => x.persona_id === selectedPersonaId);
          personaStatus.textContent = p ? ct('persona_default','This deck will open with “{name}” as its default reader.',{name:p.name}) : '';
        }
      });
    });
    const p = personas.find(x => x.persona_id === selectedPersonaId);
    personaStatus.textContent = p ? ct('persona_default','This deck will open with “{name}” as its default reader.',{name:p.name}) : '';
  }

  async function loadPersonas() {
    try {
      const r = await fetch('/api/v1/personas?deck=leopardcat', {cache:'no-store'});
      if (!r.ok) throw new Error('persona catalog unavailable');
      const data = await r.json();
      personas = Array.isArray(data.personas) ? data.personas : [];
      selectedPersonaId = personas.some(x => x.persona_id === 'master') ? 'master' : (data.default_persona || personas[0]?.persona_id || 'master');
      renderPersonaOptions();
    } catch (_) {
      personas = [{persona_id:'master', name:ct('generic_persona','General reader'), role:ct('generic_persona_role','Neutral, careful, practical Tarot interpretation')}];
      selectedPersonaId = 'master';
      renderPersonaOptions();
      personaStatus.textContent = ct('persona_only_generic','Only the general reader is available right now.');
    }
  }

  async function createCustomPersona() {
    const name = document.getElementById('persona-name').value.trim();
    const role = document.getElementById('persona-role').value.trim();
    const voice = document.getElementById('persona-voice').value.trim();
    const principles = document.getElementById('persona-principles').value.trim();
    if (!name) return alert(ct('persona_need_name','Give your reader a name first.'));
    if (!role) return alert(ct('persona_need_role','Describe this reader in one sentence.'));
    if (!voice) return alert(ct('persona_need_voice','Describe at least one speaking style.'));
    if (!principles) return alert(ct('persona_need_principles','Add at least one reading principle.'));

    personaCreateBtn.disabled = true;
    personaCreateStatus.textContent = ct('persona_creating','Creating your reader…');
    try {
      const resp = await fetch('/api/v1/personas', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          name, role, voice, principles,
          worldview: document.getElementById('persona-worldview').value.trim(),
          closing: document.getElementById('persona-closing').value.trim()
        })
      });
      const data = await readApiResponse(resp);
      if (!resp.ok) throw new Error(apiMessage(data,'persona_create_failed','Could not create the reader.'));
      personas = personas.filter(x => x.persona_id !== data.persona_id);
      personas.push(data);
      selectedPersonaId = data.persona_id;
      renderPersonaOptions();
      personaCreateStatus.textContent = ct('persona_created','✓ Created “{name}” and set it as this deck’s default reader.',{name:data.name});
      const manageUrl = managementUrl(data);
      if (manageUrl) {
        const box = document.getElementById('persona-management'); const link = document.getElementById('persona-manage-link');
        link.href = manageUrl; link.textContent = manageUrl; box.classList.remove('hidden');
        saveManagedResource({type:'persona', id:data.persona_id, name:data.name, manage_url:manageUrl, created_at:new Date().toISOString()});
      }
    } catch (e) {
      personaCreateStatus.textContent = e.message || ct('persona_create_failed','Could not create the reader. Try again later.');
    } finally {
      personaCreateBtn.disabled = false;
    }
  }

  if (personaCreateBtn) personaCreateBtn.addEventListener('click', createCustomPersona);

  const optimizeImage = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      const img = new Image();
      img.onerror = reject;
      img.onload = () => {
        const maxEdge = 1800;
        const scale = Math.min(1, maxEdge / Math.max(img.naturalWidth, img.naturalHeight));
        const canvas = document.createElement('canvas');
        canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
        canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL('image/webp', 0.88));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });

  async function readApiResponse(resp) {
    const contentType = (resp.headers.get('content-type') || '').toLowerCase();
    if (contentType.includes('application/json')) return await resp.json();
    const text = await resp.text();
    if (resp.status === 413) throw new Error(ct('upload_too_large','The uploaded images are too large in total.'));
    if (resp.status === 502 || resp.status === 503 || resp.status === 504) throw new Error(ct('server_unavailable','The server is temporarily unavailable.'));
    const preview = text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 120);
    throw new Error(preview ? `${ct('publish_failed_status','Publish failed ({status})',{status:resp.status})}: ${preview}` : ct('publish_failed_status','Publish failed ({status})',{status:resp.status}));
  }

  function render() {
    section.classList.toggle('hidden', cards.length === 0);
    count.textContent = cards.length ? ct('cards_added','Added {count} cards. Images were optimized automatically.',{count:cards.length}) : '';
    cardsEl.innerHTML = '';
    cards.forEach((card, i) => {
      const item = document.createElement('div');
      item.className = 'item';
      item.innerHTML = `
        <img src="${card.image}" alt="">
        <div>
          <label>${escapeHtml(ct('card_name','Card name'))}</label>
          <input data-i="${i}" data-k="title" value="${escapeHtml(card.title)}">
          <label>${escapeHtml(ct('upright_question','What does this card represent?'))}</label>
          <textarea data-i="${i}" data-k="upright" placeholder="${escapeHtml(ct('upright_ph','For example: a new beginning, courage, trusting intuition.'))}">${escapeHtml(card.upright)}</textarea>
          <div class="reverse-field ${reversals.checked ? '' : 'hidden'}">
            <label>${escapeHtml(ct('reverse_question','What does it mean when reversed? (optional)'))}</label>
            <textarea data-i="${i}" data-k="reversed" placeholder="${escapeHtml(ct('reverse_ph','Leave blank if unsure; the main meaning will be reused.'))}">${escapeHtml(card.reversed)}</textarea>
          </div>
        </div>`;
      cardsEl.appendChild(item);
    });
    cardsEl.querySelectorAll('input[data-k],textarea[data-k]').forEach(el => {
      el.addEventListener('input', () => { cards[Number(el.dataset.i)][el.dataset.k] = el.value; });
    });
  }

  images.addEventListener('change', async () => {
    const files = [...images.files].sort((a,b) => a.name.localeCompare(b.name, creatorLocale(), {numeric:true}));
    status.textContent = files.length ? ct('preparing_images','Preparing {count} images…',{count:files.length}) : '';
    cards = [];
    let doneCount = 0;
    for (const file of files) {
      if (!['image/jpeg','image/png','image/webp'].includes(file.type)) continue;
      const optimized = await optimizeImage(file);
      cards.push({ title: friendlyName(file.name) || ct('default_card','Card {count}',{count:cards.length+1}), upright: '', reversed: '', image: optimized });
      doneCount++;
      status.textContent = ct('preparing_progress','Preparing images… {done}/{total}',{done:doneCount,total:files.length});
    }
    status.textContent = '';
    render();
  });

  reversals.addEventListener('change', render);

  const themePreset = document.getElementById('theme-preset');
  const themeCustom = document.getElementById('theme-custom');
  themePreset.addEventListener('change', () => themeCustom.classList.toggle('hidden', themePreset.value !== 'custom'));

  async function fileToThemeData(file) {
    if (!file) return '';
    return await optimizeImage(file);
  }

  async function publishThemeIfNeeded() {
    if (themePreset.value !== 'custom') return themePreset.value;
    status.textContent = ct('preparing_theme','Preparing your page theme…');
    const payload = {
      name: ct('theme_name','{name} theme',{name:document.getElementById('deck-name').value.trim()}),
      colors: {
        background: document.getElementById('theme-bg').value,
        surface: '#171721', accent: document.getElementById('theme-accent').value, text: '#f5f2ea'
      },
      background_image: await fileToThemeData(document.getElementById('theme-background').files[0]),
      card_back: await fileToThemeData(document.getElementById('theme-card-back').files[0])
    };
    const r = await fetch('/api/v1/themes', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const raw = await r.text();
    let data = {}; try { data = JSON.parse(raw); } catch (_) {}
    if (!r.ok) throw new Error(apiMessage(data,r.status===413?'theme_too_large':'theme_failed',r.status===413?'The theme image is too large.':'Could not create the page theme.'));
    return data.theme_id;
  }

  document.getElementById('publish').addEventListener('click', async () => {
    const name = document.getElementById('deck-name').value.trim();
    if (!name) return alert(ct('need_deck_name','Name this deck first.'));
    if (deckSlug.value && !(await checkSlugAvailability(true))) return alert(ct('need_slug','Choose an available custom URL name first.'));
    if (!cards.length) return alert(ct('need_images','Select your card images first.'));
    const missing = cards.find(c => !c.title.trim() || !c.upright.trim());
    if (missing) return alert(ct('missing_meaning','“{name}” is still missing a meaning.',{name:missing.title||ct('unnamed_card','one card')}));
    const btn = document.getElementById('publish');
    btn.disabled = true;
    status.textContent = ct('publishing','Creating your reading page…');
    try {
      const selectedThemeId = await publishThemeIfNeeded();
      const resp = await fetch('/api/v1/decks', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          name,
          slug: normalizeSlug(deckSlug.value),
          creator: document.getElementById('creator').value.trim(),
          description: document.getElementById('description').value.trim(),
          reversals: reversals.checked,
          persona: selectedPersonaId,
          theme: selectedThemeId,
          cards
        })
      });
      const data = await readApiResponse(resp);
      if (!resp.ok) throw new Error(apiMessage(data,'publish_failed','Publishing failed.'));
      const u = new URL(data.share_path, location.origin);
      u.searchParams.set('theme', selectedThemeId);
      const url = u.href;
      const link = document.getElementById('share-link');
      link.href = url; link.textContent = url;
      const manageUrl = managementUrl(data);
      const manageLink = document.getElementById('deck-manage-link');
      if (manageLink && manageUrl) { manageLink.href = manageUrl; manageLink.textContent = manageUrl; }
      savePublishedHistory({ deck_id: data.deck_id, name: data.name || name, theme_id: selectedThemeId, persona_id: data.default_persona || selectedPersonaId, url, manage_url: manageUrl, published_at: new Date().toISOString() });
      if (manageUrl) saveManagedResource({type:'deck', id:data.deck_id, name:data.name || name, manage_url:manageUrl, public_url:url, created_at:new Date().toISOString()});
      done.classList.remove('hidden');
      status.textContent = ct('complete_count','Done — {count} cards.',{count:data.card_count});
      done.scrollIntoView({behavior:'smooth'});
    } catch (e) {
      status.textContent = e.message || ct('publish_failed','Publishing failed. Try again later.');
    } finally { btn.disabled = false; }
  });

  document.getElementById('copy-persona-manage')?.addEventListener('click', async () => {
    const url = document.getElementById('persona-manage-link')?.href || '';
    if (url) await navigator.clipboard.writeText(url);
    document.getElementById('copy-persona-manage').textContent = ct('copied','Copied');
  });
  document.getElementById('copy-deck-manage')?.addEventListener('click', async () => {
    const url = document.getElementById('deck-manage-link')?.href || '';
    if (url) await navigator.clipboard.writeText(url);
    document.getElementById('copy-deck-manage').textContent = ct('copied','Copied');
  });

  document.getElementById('copy').addEventListener('click', async () => {
    const url = document.getElementById('share-link').href;
    await navigator.clipboard.writeText(url);
    document.getElementById('copy').textContent = ct('copied','Copied');
  });

  loadCreatorLocale().then(()=>{ renderPublishedHistory(); loadPersonas(); });
})();