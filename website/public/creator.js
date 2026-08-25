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
  const readFile = file => new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(file);
  });

  function render() {
    section.classList.toggle('hidden', cards.length === 0);
    count.textContent = cards.length ? `已加入 ${cards.length} 張牌。` : '';
    cardsEl.innerHTML = '';
    cards.forEach((card, i) => {
      const item = document.createElement('div');
      item.className = 'item';
      item.innerHTML = `
        <img src="${card.image}" alt="">
        <div>
          <label>牌名</label>
          <input data-i="${i}" data-k="title" value="${card.title.replace(/"/g, '&quot;')}">
          <label>正位／主要牌義</label>
          <textarea data-i="${i}" data-k="upright" placeholder="用你自己的話描述這張牌代表什麼。">${card.upright}</textarea>
          <div class="reverse-field ${reversals.checked ? '' : 'hidden'}">
            <label>逆位牌義</label>
            <textarea data-i="${i}" data-k="reversed" placeholder="若沒有特別逆位牌義，也可以留空。">${card.reversed}</textarea>
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
    status.textContent = files.length ? '正在讀取圖片…' : '';
    cards = [];
    for (const file of files) {
      if (!['image/jpeg','image/png','image/webp'].includes(file.type)) continue;
      cards.push({ title: friendlyName(file.name) || `牌 ${cards.length + 1}`, upright: '', reversed: '', image: await readFile(file) });
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
    if (missing) return alert(`「${missing.title || '某張牌'}」還沒有填主要牌義。`);
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
      const data = await resp.json();
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