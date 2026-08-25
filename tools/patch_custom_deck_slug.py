from pathlib import Path

root = Path(__file__).resolve().parents[1]

# publishing.py
p = root / 'website/divination/publishing.py'
s = p.read_text(encoding='utf-8')
s = s.replace('''    def publish(self, payload: dict[str, Any]) -> dict[str, Any]:\n        self._check_capacity()\n        name = _clean_text(payload.get("name"), 100)\n''', '''    def slug_available(self, requested: str) -> dict[str, Any]:\n        slug = _clean_text(requested, 64).lower()\n        valid = bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{1,46}[a-z0-9])?", slug)) and 3 <= len(slug) <= 48\n        reserved = {"leopardcat", "admin", "api", "create", "themes", "tarot", "www"}\n        available = valid and slug not in reserved and not (self.root / slug).exists()\n        return {"slug": slug, "valid": valid, "available": available, "reserved": slug in reserved}\n\n    def publish(self, payload: dict[str, Any]) -> dict[str, Any]:\n        self._check_capacity()\n        name = _clean_text(payload.get("name"), 100)\n''')
s = s.replace('''        deck_id = f"{_slug(name)}-{secrets.token_hex(3)}"\n        deck_dir = self.root / deck_id\n        image_dir = deck_dir / "images"\n        image_dir.mkdir(parents=True, exist_ok=False)\n''', '''        requested_slug = _clean_text(payload.get("slug"), 64).lower()\n        if requested_slug:\n            check = self.slug_available(requested_slug)\n            if not check["valid"]:\n                raise DivinationError("專屬網址只能使用 3–48 個英文小寫字母、數字與連字號，且不能以連字號開頭或結尾")\n            if check["reserved"]:\n                raise DivinationError("這個專屬網址名稱為系統保留字，請換一個")\n            if not check["available"]:\n                raise DivinationError("這個專屬網址名稱已被使用，請換一個")\n            deck_id = requested_slug\n        else:\n            deck_id = f"{_slug(name)}-{secrets.token_hex(3)}"\n        deck_dir = self.root / deck_id\n        image_dir = deck_dir / "images"\n        try:\n            image_dir.mkdir(parents=True, exist_ok=False)\n        except FileExistsError:\n            raise DivinationError("這個專屬網址名稱剛被其他人使用，請換一個")\n''')
p.write_text(s, encoding='utf-8')

# fortune_server.py
p = root / 'website/fortune_server.py'
s = p.read_text(encoding='utf-8')
anchor = """        if path.startswith('/api/v1/decks/'):\n"""
insert = """        if path.startswith('/api/v1/deck-slugs/'):\n            slug = path.rsplit('/', 1)[-1].lower()\n            result = DECK_PUBLISHER.slug_available(slug)\n            self.send_response(200)\n            self.send_header('Content-type', 'application/json; charset=utf-8')\n            self.send_header('Cache-Control', 'no-store')\n            self.end_headers()\n            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))\n            return\n"""
if insert not in s:
    s = s.replace(anchor, insert + anchor)
p.write_text(s, encoding='utf-8')

# create.html
p = root / 'website/public/create.html'
s = p.read_text(encoding='utf-8')
old = '''    <label>一句介紹（選填）</label><textarea id="description" placeholder="這副牌想陪伴大家看見什麼？"></textarea>\n  </section>'''
new = '''    <label>一句介紹（選填）</label><textarea id="description" placeholder="這副牌想陪伴大家看見什麼？"></textarea>\n    <label>你的專屬網址名稱（選填）</label>\n    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">\n      <span class="muted">?deck=</span><input id="deck-slug" style="max-width:360px" placeholder="例如 moon-garden" autocomplete="off" spellcheck="false">\n    </div>\n    <p class="muted" style="margin-bottom:4px">留空會自動產生。想自己指定時，只需英文小寫、數字與 -，共 3–48 個字元。</p>\n    <p id="slug-status" class="muted" aria-live="polite"></p>\n  </section>'''
if 'id="deck-slug"' not in s:
    s = s.replace(old, new)
p.write_text(s, encoding='utf-8')

# creator.js
p = root / 'website/public/creator.js'
s = p.read_text(encoding='utf-8')
needle = """  const HISTORY_KEY = 'leopardcat-published-decks-v1';\n"""
addition = """  const deckSlug = document.getElementById('deck-slug');\n  const slugStatus = document.getElementById('slug-status');\n  let slugCheckTimer = null;\n  let slugAvailable = null;\n\n  function normalizeSlug(value) {\n    return String(value || '').toLowerCase().trim().replace(/[^a-z0-9-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '').slice(0, 48);\n  }\n\n  async function checkSlugAvailability(force = false) {\n    const slug = normalizeSlug(deckSlug.value);\n    if (deckSlug.value !== slug) deckSlug.value = slug;\n    if (!slug) { slugAvailable = null; slugStatus.textContent = '留空會由系統自動產生網址。'; return true; }\n    if (slug.length < 3) { slugAvailable = false; slugStatus.textContent = '至少輸入 3 個字元。'; return false; }\n    slugStatus.textContent = '正在檢查網址…';\n    try {\n      const r = await fetch(`/api/v1/deck-slugs/${encodeURIComponent(slug)}`, {cache:'no-store'});\n      const data = await r.json();\n      slugAvailable = !!data.available;\n      slugStatus.textContent = data.available ? `✓ 可以使用：?deck=${slug}` : (data.reserved ? '✗ 這個名稱是系統保留字，請換一個。' : '✗ 這個名稱已被使用，請換一個。');\n      slugStatus.style.color = data.available ? '#2d7a3e' : '#a33a32';\n      return slugAvailable;\n    } catch (_) {\n      slugAvailable = null;\n      slugStatus.textContent = force ? '目前無法檢查網址，請稍後再試。' : '';\n      return false;\n    }\n  }\n\n  deckSlug.addEventListener('input', () => {\n    slugAvailable = null;\n    clearTimeout(slugCheckTimer);\n    slugCheckTimer = setTimeout(() => checkSlugAvailability(false), 350);\n  });\n\n"""
if 'checkSlugAvailability' not in s:
    s = s.replace(needle, needle + addition)

old = """    if (!name) return alert('先幫這副牌取一個名字。');\n    if (!cards.length) return alert('請先選取你的牌圖。');\n"""
new = """    if (!name) return alert('先幫這副牌取一個名字。');\n    if (deckSlug.value && !(await checkSlugAvailability(true))) return alert('請先換一個可以使用的專屬網址名稱。');\n    if (!cards.length) return alert('請先選取你的牌圖。');\n"""
s = s.replace(old, new)
old = """          name,\n          creator: document.getElementById('creator').value.trim(),\n"""
new = """          name,\n          slug: normalizeSlug(deckSlug.value),\n          creator: document.getElementById('creator').value.trim(),\n"""
s = s.replace(old, new)
p.write_text(s, encoding='utf-8')

print('custom_deck_slug_patch=applied')
