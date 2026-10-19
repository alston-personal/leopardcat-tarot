import { chromium } from 'playwright';
import assert from 'node:assert/strict';
const base='http://127.0.0.1:8088';
const browser=await chromium.launch({headless:true});
try {
  const page=await browser.newPage();
  await page.goto(base+'/create.html',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.querySelectorAll('#cards .item').length===78);
  assert.equal(await page.locator('#cards .item').count(),78);
  assert.equal(await page.locator('input[name="image-source"]:checked').inputValue(),'leopardcat');
  assert.equal(await page.locator('#cards .item img').count(),78);
  await page.locator('#deck-name').fill('Builtin Source E2E');
  await page.locator('#reversals').check();
  await page.locator('#cards textarea[data-k="upright"]').first().fill('測試專屬正位');
  await page.locator('#cards textarea[data-k="reversed"]').first().fill('測試專屬逆位');
  await page.locator('#publish').click();
  await page.waitForFunction(()=>!document.getElementById('done').classList.contains('hidden'),{timeout:30000});
  const href=await page.locator('#share-link').getAttribute('href');
  assert.ok(href.includes('deck='));
  const response=await page.request.get(href);
  assert.equal(response.status(),200);
  console.log('builtin_artwork_creator_publish_e2e=passed',href);
} finally {await browser.close();}
