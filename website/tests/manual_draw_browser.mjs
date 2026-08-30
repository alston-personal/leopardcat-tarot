import { chromium } from 'playwright';
import assert from 'node:assert/strict';

// Permanent release gate for the shared shuffle/manual-draw experience.
const base = process.env.TEST_BASE || 'http://127.0.0.1:8088';
const browser = await chromium.launch({ headless: true });

function mockReading(body, ids, suffix='manual') {
  const cards = ids.map((card_id, i) => ({
    card_id,
    position: ['past','present','future'][i] || 'guidance',
    position_label: ['過去／根源','現在／核心','未來／發展'][i] || '核心指引',
    orientation: i === 1 ? 'reversed' : 'upright',
    draw_index: body.input?.draw_indices?.[i] || i + 1,
    meaning: '測試牌義'
  }));
  const now = Math.floor(Date.now()/1000);
  return {
    reading_id: `rd_browser_${suffix}_${Date.now()}`,
    session_token: `private-${suffix}`,
    share_token: `share-${suffix}`,
    expires_at: now + 3600,
    privacy: { question_stored:false, answer_stored:false, symbolic_state_ttl_hours:24 },
    method: 'tarot', persona: 'leopardcat', question: body.question, lang: body.lang || 'zh-TW',
    method_result: {
      method:'tarot',
      deck:{ deck_id:'leopardcat', card_count:78, card_back:'/art/card-back.svg' },
      spread: body.input?.spread || 'single',
      cards,
      rules:{
        draw_mode: Array.isArray(body.input?.draw_indices) ? 'manual' : 'auto',
        draw_indices: body.input?.draw_indices || cards.map((_,i)=>i+1),
        orientation_assigned_at_shuffle_time:true,
        orientation_hidden_until_reveal:true,
        draw_indices_are_1_based:true
      }
    },
    reading: '瀏覽器自動測試：這次牌局已完整建立。<div class="hidden-quote" style="display:none">測試完成</div>'
  };
}

try {
  const page = await browser.newPage({ viewport:{width:1280,height:900} });
  await page.addInitScript(() => localStorage.setItem('leopard-lang','zh'));
  await page.goto(base+'/?deck=leopardcat', { waitUntil:'networkidle' });
  await page.waitForFunction(() => Array.isArray(window.cardData) && window.cardData.length >= 78);
  const ids = await page.evaluate(() => window.cardData.slice(0,3).map(c=>c.id));
  assert.equal(ids.length,3);

  let manualBody = null;
  await page.route('**/api/v1/readings', async route => {
    const req = route.request();
    manualBody = req.postDataJSON();
    await route.fulfill({
      status:200,
      contentType:'application/json',
      body:JSON.stringify(mockReading(manualBody, ids, 'manual'))
    });
  });

  await page.locator('#fortune-question').fill('手動抽三牌測試');
  await page.locator('[data-spread-choice="three_card"]').click();
  await page.locator('[data-draw-mode="manual"]').click();
  assert.ok(await page.locator('#manual-draw-stage').isVisible());
  assert.ok(await page.locator('#btn-primary-draw').isHidden());
  await page.locator('#btn-manual-shuffle').click();
  await page.waitForSelector('#manual-card-pool .manual-card-back');
  assert.equal(await page.locator('#manual-card-pool .manual-card-back').count(),78);
  assert.match(await page.locator('#manual-draw-status').innerText(), /0\s*\/\s*3/);

  const backs = page.locator('#manual-card-pool .manual-card-back');
  await backs.nth(2).click();
  await backs.nth(75).click();
  await backs.nth(54).click();
  await page.waitForFunction(() => window.currentReadingState?.cards?.length === 3);

  assert.ok(manualBody);
  assert.equal(manualBody.method,'tarot');
  assert.equal(manualBody.input.spread,'three_card');
  assert.equal(manualBody.input.deck_id,'leopardcat');
  assert.deepEqual(manualBody.input.draw_indices,[3,76,55]);
  assert.equal(typeof manualBody.seed,'string');
  assert.ok(manualBody.seed.length >= 32);
  assert.equal(await page.locator('#pinned-card-display .pinned-card-content').count(),3);
  assert.deepEqual(await page.evaluate(() => window.currentReadingState.draw_indices),[3,76,55]);
  assert.equal(await page.evaluate(() => window.currentReadingState.draw_mode),'manual');
  assert.ok(new URL(page.url()).searchParams.get('reading'));
  assert.ok(new URL(page.url()).searchParams.get('share'));
  console.log('browser_manual_three_card_indices=passed');

  await page.reload({ waitUntil:'networkidle' });
  await page.waitForFunction(() => window.currentReadingState?.cards?.length === 3);
  assert.deepEqual(await page.evaluate(() => window.currentReadingState.draw_indices),[3,76,55]);
  assert.equal(await page.locator('#pinned-card-display .pinned-card-content').count(),3);
  assert.match(await page.locator('#chat-history').innerText(), /手動抽三牌測試/);
  console.log('browser_manual_reload_continuity=passed');

  const cardBack = await page.request.get(base+'/art/card-back.svg');
  assert.equal(cardBack.status(),200);
  const svg = await cardBack.text();
  assert.ok(svg.includes('scale(-1 1)') && svg.includes('scale(1 -1)') && svg.includes('scale(-1 -1)'));
  assert.ok(!svg.toLowerCase().includes('<text'));
  console.log('browser_four_way_card_back=passed');

  const auto = await browser.newPage({ viewport:{width:900,height:800} });
  await auto.addInitScript(() => localStorage.setItem('leopard-lang','zh'));
  await auto.goto(base+'/?deck=leopardcat', { waitUntil:'networkidle' });
  await auto.waitForFunction(() => Array.isArray(window.cardData) && window.cardData.length >= 78);
  const autoId = await auto.evaluate(() => window.cardData[0].id);
  let autoBody = null;
  await auto.route('**/api/v1/readings', async route => {
    autoBody = route.request().postDataJSON();
    await route.fulfill({ status:200, contentType:'application/json', body:JSON.stringify(mockReading(autoBody,[autoId],'auto')) });
  });
  await auto.locator('#fortune-question').fill('自動抽牌測試');
  assert.ok((await auto.locator('[data-draw-mode="auto"]').getAttribute('class')).includes('active'));
  await auto.locator('#btn-primary-draw').click();
  await auto.waitForFunction(() => window.currentReadingState?.cards?.length === 1);
  assert.ok(autoBody);
  assert.equal(autoBody.input.spread,'single');
  assert.equal(Object.prototype.hasOwnProperty.call(autoBody.input,'draw_indices'),false);
  assert.equal(Object.prototype.hasOwnProperty.call(autoBody,'seed'),false);
  console.log('browser_auto_controller_same_pipeline=passed');

  const mobile = await browser.newPage({ viewport:{width:375,height:812} });
  await mobile.addInitScript(() => localStorage.setItem('leopard-lang','zh'));
  await mobile.goto(base+'/?deck=leopardcat', { waitUntil:'networkidle' });
  await mobile.waitForFunction(() => Array.isArray(window.cardData) && window.cardData.length >= 78);
  await mobile.locator('#fortune-question').fill('手機手動抽牌');
  await mobile.locator('[data-draw-mode="manual"]').click();
  await mobile.locator('#btn-manual-shuffle').click();
  assert.equal(await mobile.locator('#manual-card-pool .manual-card-back').count(),78);
  const overflow = await mobile.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `manual draw horizontal overflow ${overflow}px`);
  const poolBox = await mobile.locator('#manual-card-pool').boundingBox();
  assert.ok(poolBox && poolBox.width <= 375);
  console.log('browser_manual_mobile_layout=passed');
} finally {
  await browser.close();
}
