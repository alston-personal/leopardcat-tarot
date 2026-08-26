(() => {
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
    if (!slug) { slugAvailable = null; slugStatus.textContent = '留空會由系統自動產生網址。'; return true; }
    if (slug.length < 3) { slugAvailable = false; slugStatus.textContent = '至少輸入 3 個字元。'; return false; }
    slugStatus.textContent = '正在檢查網址…';
    try {
      const r = await fetch(`/api/v1/deck-slugs/${encodeURIComponent(slug)}`, {cache:'no-store'});
      const data = await r.json();
      slugAvailable = !!data.available;
      slugStatus.textContent = data.available ? `✓ 可以使用：?deck=${slug}` : (data.reserved ? '✗ 這個名稱是系統保留字，請換一個。' : '✗ 這個名稱已被使用，請換一個。');
      slugStatus.style.color = data.available ? '#2d7a3e' : '#a33a32';
      return slugAvailable;
    } catch (_) {
      slugAvailable = null;
      slugStatus.textContent = force ? '目前無法檢查網址，請稍後再試。' : '';
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
      el.innerHTML = '<p class="muted">這個瀏覽器還沒有發布紀錄。</p>';
      return;
    }
    el.innerHTML = rows.map(x => {
      const when = x.published_at ? new Date(x.published_at).toLocaleString('zh-TW') : '';
      const manage = x.manage_url ? ` · <a href="${escapeHtml(x.manage_url)}">管理</a>` : '';
      return `<div style="padding:10px 0;border-top:1px solid #eee3d4"><strong>${escapeHtml(x.name || x.deck_id)}</strong><div class="muted">${escapeHtml(when)}</div><a href="${escapeHtml(x.url)}" target="_blank">開啟占卜頁</a>${manage}</div>`;
    }).join('');
  }

  const friendlyName = (filename) => filename.replace(/\.[^.]+$/, '').replace(/^\d+[\s._-]*/, '').replace(/[_-]+/g, ' ').trim();
  const escapeHtml = (s) => String(s || '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

  function renderPersonaOptions() {
    if (!personaOptions) return;
    if (!personas.length) {
      personaOptions.innerHTML = '<p class="muted">目前使用通用解牌師。</p>';
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
          personaStatus.textContent = p ? `這副牌發布後會預設由「${p.name}」解讀。` : '';
        }
      });
    });
    const p = personas.find(x => x.persona_id === selectedPersonaId);
    personaStatus.textContent = p ? `這副牌發布後會預設由「${p.name}」解讀。` : '';
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
      personas = [{persona_id:'master', name:'通用解牌師', role:'中立、謹慎、實用的塔羅解讀'}];
      selectedPersonaId = 'master';
      renderPersonaOptions();
      personaStatus.textContent = '目前只顯示通用解牌師；其他解牌風格稍後可再切換。';
    }
  }

  async function createCustomPersona() {
    const name = document.getElementById('persona-name').value.trim();
    const role = document.getElementById('persona-role').value.trim();
    const voice = document.getElementById('persona-voice').value.trim();
    const principles = document.getElementById('persona-principles').value.trim();
    if (!name) return alert('先幫你的解牌師取一個名字。');
    if (!role) return alert('請用一句話介紹這位解牌師。');
    if (!voice) return alert('請描述至少一種說話風格。');
    if (!principles) return alert('請填至少一條解讀原則。');

    personaCreateBtn.disabled = true;
    personaCreateStatus.textContent = '正在建立你的解牌師…';
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
      if (!resp.ok) throw new Error(data.message || '建立解牌師失敗');
      personas = personas.filter(x => x.persona_id !== data.persona_id);
      personas.push(data);
      selectedPersonaId = data.persona_id;
      renderPersonaOptions();
      personaCreateStatus.textContent = `✓ 已建立「${data.name}」，並設為這副牌的預設解牌師。`;
      const manageUrl = managementUrl(data);
      if (manageUrl) {
        const box = document.getElementById('persona-management'); const link = document.getElementById('persona-manage-link');
        link.href = manageUrl; link.textContent = manageUrl; box.classList.remove('hidden');
        saveManagedResource({type:'persona', id:data.persona_id, name:data.name, manage_url:manageUrl, created_at:new Date().toISOString()});
      }
    } catch (e) {
      personaCreateStatus.textContent = e.message || '建立解牌師失敗，請稍後再試。';
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
    if (resp.status === 413) throw new Error('這次上傳的圖片總量太大。請稍微減少圖片尺寸或分批建立牌組後再試。');
    if (resp.status === 502 || resp.status === 503 || resp.status === 504) throw new Error('伺服器暫時無法處理，請稍後再試。');
    const preview = text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 120);
    throw new Error(preview ? `發布失敗（${resp.status}）：${preview}` : `發布失敗（${resp.status}）`);
  }

  function render() {
    section.classList.toggle('hidden', cards.length === 0);
    count.textContent = cards.length ? `已加入 ${cards.length} 張牌。圖片已自動最佳化，不需要自己縮圖。` : '';
    cardsEl.innerHTML = '';
    cards.forEach((card, i) => {
      const item = document.createElement('div');
      item.className = 'item';
      item.innerHTML = `
        <img src="${card.image}" alt="">
        <div>
          <label>牌名</label>
          <input data-i="${i}" data-k="title" value="${escapeHtml(card.title)}">
          <label>這張牌代表什麼？</label>
          <textarea data-i="${i}" data-k="upright" placeholder="例如：新的開始、勇敢嘗試、相信直覺。不用寫得很專業。">${escapeHtml(card.upright)}</textarea>
          <div class="reverse-field ${reversals.checked ? '' : 'hidden'}">
            <label>如果倒著抽到，它代表什麼？（選填）</label>
            <textarea data-i="${i}" data-k="reversed" placeholder="不知道也可以留空，系統會沿用主要牌義。">${escapeHtml(card.reversed)}</textarea>
          </div>
        </div>`;
      cardsEl.appendChild(item);
    });
    cardsEl.querySelectorAll('input[data-k],textarea[data-k]').forEach(el => {
      el.addEventListener('input', () => { cards[Number(el.dataset.i)][el.dataset.k] = el.value; });
    });
  }

  images.addEventListener('change', async () => {
    const files = [...images.files].sort((a,b) => a.name.localeCompare(b.name, 'zh-Hant', {numeric:true}));
    status.textContent = files.length ? `正在準備 ${files.length} 張圖片…` : '';
    cards = [];
    let doneCount = 0;
    for (const file of files) {
      if (!['image/jpeg','image/png','image/webp'].includes(file.type)) continue;
      const optimized = await optimizeImage(file);
      cards.push({ title: friendlyName(file.name) || `牌 ${cards.length + 1}`, upright: '', reversed: '', image: optimized });
      doneCount++;
      status.textContent = `正在準備圖片… ${doneCount}/${files.length}`;
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
    status.textContent = '正在準備你的頁面風格…';
    const payload = {
      name: `${document.getElementById('deck-name').value.trim()} 的風格`,
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
    if (!r.ok) throw new Error(data.message || (r.status === 413 ? '主題圖片太大，請換較小的圖片。' : '建立頁面風格失敗。'));
    return data.theme_id;
  }

  document.getElementById('publish').addEventListener('click', async () => {
    const name = document.getElementById('deck-name').value.trim();
    if (!name) return alert('先幫這副牌取一個名字。');
    if (deckSlug.value && !(await checkSlugAvailability(true))) return alert('請先換一個可以使用的專屬網址名稱。');
    if (!cards.length) return alert('請先選取你的牌圖。');
    const missing = cards.find(c => !c.title.trim() || !c.upright.trim());
    if (missing) return alert(`「${missing.title || '某張牌'}」還沒有填牌義。`);
    const btn = document.getElementById('publish');
    btn.disabled = true;
    status.textContent = '正在建立你的占卜頁…';
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
          cards
        })
      });
      const data = await readApiResponse(resp);
      if (!resp.ok) throw new Error(data.message || '發布失敗');
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
      status.textContent = `完成，共 ${data.card_count} 張牌。`;
      done.scrollIntoView({behavior:'smooth'});
    } catch (e) {
      status.textContent = e.message || '發布失敗，請稍後再試。';
    } finally { btn.disabled = false; }
  });

  document.getElementById('copy-persona-manage')?.addEventListener('click', async () => {
    const url = document.getElementById('persona-manage-link')?.href || '';
    if (url) await navigator.clipboard.writeText(url);
    document.getElementById('copy-persona-manage').textContent = '已複製';
  });
  document.getElementById('copy-deck-manage')?.addEventListener('click', async () => {
    const url = document.getElementById('deck-manage-link')?.href || '';
    if (url) await navigator.clipboard.writeText(url);
    document.getElementById('copy-deck-manage').textContent = '已複製';
  });

  document.getElementById('copy').addEventListener('click', async () => {
    const url = document.getElementById('share-link').href;
    await navigator.clipboard.writeText(url);
    document.getElementById('copy').textContent = '已複製';
  });

  renderPublishedHistory();
  loadPersonas();
})();