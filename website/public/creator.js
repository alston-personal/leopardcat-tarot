(() => {
  const images = document.getElementById('images');
  const cardsEl = document.getElementById('cards');
  const section = document.getElementById('cards-section');
  const count = document.getElementById('count');
  const reversals = document.getElementById('reversals');
  const status = document.getElementById('status');
  const done = document.getElementById('done');
  let cards = [];

  const friendlyName = (filename) => filename.replace(/\.[^.]+$/, '').replace(/^\d+[\s._-]*/, '').replace(/[_-]+/g, ' ').trim();
  const escapeHtml = (s) => String(s || '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

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
    if (contentType.includes('application/json')) {
      return await resp.json();
    }
    const text = await resp.text();
    if (resp.status === 413) {
      throw new Error('這次上傳的圖片總量太大。請稍微減少圖片尺寸或分批建立牌組後再試。');
    }
    if (resp.status === 502 || resp.status === 503 || resp.status === 504) {
      throw new Error('伺服器暫時無法處理，請稍後再試。');
    }
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

  document.getElementById('publish').addEventListener('click', async () => {
    const name = document.getElementById('deck-name').value.trim();
    if (!name) return alert('先幫這副牌取一個名字。');
    if (!cards.length) return alert('請先選取你的牌圖。');
    const missing = cards.find(c => !c.title.trim() || !c.upright.trim());
    if (missing) return alert(`「${missing.title || '某張牌'}」還沒有填牌義。`);
    const btn = document.getElementById('publish');
    btn.disabled = true;
    status.textContent = '正在建立你的占卜頁…';
    try {
      const resp = await fetch('/api/v1/decks', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          name,
          creator: document.getElementById('creator').value.trim(),
          description: document.getElementById('description').value.trim(),
          reversals: reversals.checked,
          cards
        })
      });
      const data = await readApiResponse(resp);
      if (!resp.ok) throw new Error(data.message || '發布失敗');
      const url = new URL(data.share_path, location.origin).href;
      const link = document.getElementById('share-link');
      link.href = url; link.textContent = url;
      done.classList.remove('hidden');
      status.textContent = `完成，共 ${data.card_count} 張牌。`;
      done.scrollIntoView({behavior:'smooth'});
    } catch (e) {
      status.textContent = e.message || '發布失敗，請稍後再試。';
    } finally { btn.disabled = false; }
  });

  document.getElementById('copy').addEventListener('click', async () => {
    const url = document.getElementById('share-link').href;
    await navigator.clipboard.writeText(url);
    document.getElementById('copy').textContent = '已複製';
  });
})();