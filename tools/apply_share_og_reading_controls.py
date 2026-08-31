from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'website'


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing anchor: {label}')
    return text.replace(old, new, 1)

# 1) Group the previously scattered reading controls into one deliberate setup surface.
index = WEB / 'index.html'
s = index.read_text(encoding='utf-8')
old = '''                        <div id="legacy-spread-picker" class="legacy-spread-picker" role="radiogroup" aria-label="Spread">'''
new = '''                        <div id="reading-config-card" class="reading-config-card" aria-label="Reading setup">
                            <div class="reading-config-group reading-config-spread">
                        <div id="legacy-spread-picker" class="legacy-spread-picker" role="radiogroup" aria-label="Spread">'''
s = replace_once(s, old, new, 'reading config start')
old = '''                        </div>
                        <div id="draw-mode-picker" class="legacy-spread-picker draw-mode-picker" role="radiogroup" aria-label="Draw mode">'''
new = '''                        </div>
                            </div>
                            <div class="reading-config-group reading-config-mode">
                        <div id="draw-mode-picker" class="legacy-spread-picker draw-mode-picker" role="radiogroup" aria-label="Draw mode">'''
s = replace_once(s, old, new, 'reading config mode')
old = '''                        </div>
                        <div id="manual-draw-stage" class="manual-draw-stage hidden">'''
new = '''                        </div>
                            </div>
                        <div id="manual-draw-stage" class="manual-draw-stage hidden">'''
s = replace_once(s, old, new, 'manual stage start')
old = '''                            <div id="manual-card-pool" class="manual-card-pool" aria-label="Card backs"></div>
                        </div>
                        <button id="btn-primary-draw"'''
new = '''                            <div id="manual-card-pool" class="manual-card-pool" aria-label="Card backs"></div>
                        </div>
                        </div>
                        <button id="btn-primary-draw"'''
s = replace_once(s, old, new, 'reading config close')
index.write_text(s, encoding='utf-8')

# 2) Render a dedicated 1200x630 social preview while preserving the square downloadable memo.
main = WEB / 'main.js'
s = main.read_text(encoding='utf-8')
old = '''        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
        await persistReadingSharePreview(blob); // social crawlers can now resolve the actual deck-owned share card.
        const filePrefix = window.activeBrand?.file_prefix || 'tarot';'''
new = '''        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));

        // Social crawlers need a landscape Open Graph asset. Keep the downloadable/native
        // share memo square, but reflow the same deck-owned content into 1200x630 for OG.
        let ogBlob = blob;
        template.classList.add('share-og-mode');
        try {
            const ogCanvas = await html2canvas(template, {
                useCORS: true,
                allowTaint: true,
                logging: false,
                backgroundColor: shareTheme.background,
                scale: 1.0,
                width: 1200,
                height: 630,
                imageTimeout: 5000,
                removeContainer: true
            });
            const renderedOgBlob = await new Promise(resolve => ogCanvas.toBlob(resolve, 'image/png'));
            if (renderedOgBlob) ogBlob = renderedOgBlob;
        } finally {
            template.classList.remove('share-og-mode');
        }
        await persistReadingSharePreview(ogBlob); // OG receives the landscape asset; private text is still excluded.
        const filePrefix = window.activeBrand?.file_prefix || 'tarot';'''
s = replace_once(s, old, new, 'persist share preview')
main.write_text(s, encoding='utf-8')

# 3) Append scoped CSS so existing IDs/event handlers remain untouched.
style = WEB / 'style.css'
s = style.read_text(encoding='utf-8')
marker = '/* === Reading Control Surface + Social OG v1 === */'
if marker not in s:
    s += r'''

/* === Reading Control Surface + Social OG v1 === */
.reading-config-card {
  margin: 14px 0 18px;
  padding: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  border: 1px solid rgba(212,175,55,.22);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(212,175,55,.07), rgba(5,12,10,.45));
  box-shadow: inset 0 1px rgba(255,255,255,.025), 0 12px 32px rgba(0,0,0,.14);
}
.reading-config-group {
  min-width: 0;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(2,9,7,.36);
  border: 1px solid rgba(255,255,255,.045);
}
.reading-config-card .legacy-spread-picker {
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  display: grid !important;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  align-items: center;
}
.reading-config-card .legacy-spread-label {
  grid-column: 1 / -1;
  margin: 0 0 2px;
  font-size: .68rem;
  line-height: 1.2;
  letter-spacing: .13em;
  color: rgba(244,241,234,.58);
  text-transform: uppercase;
}
.reading-config-card .legacy-spread-btn {
  min-height: 38px;
  margin: 0 !important;
  padding: 8px 12px !important;
  border-radius: 999px !important;
  border: 1px solid rgba(212,175,55,.18) !important;
  background: rgba(255,255,255,.025) !important;
  color: rgba(244,241,234,.74) !important;
  font-weight: 700;
  transition: transform .18s ease, border-color .18s ease, background .18s ease, color .18s ease, box-shadow .18s ease;
}
.reading-config-card .legacy-spread-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(212,175,55,.5) !important;
}
.reading-config-card .legacy-spread-btn.active {
  color: #111 !important;
  background: linear-gradient(135deg, #f2d878, #c9a542) !important;
  border-color: rgba(255,232,145,.8) !important;
  box-shadow: 0 5px 18px rgba(212,175,55,.18);
}
.reading-config-card .manual-draw-stage {
  grid-column: 1 / -1;
  margin: 0;
  padding: 12px 12px 8px;
  border-top: 1px solid rgba(212,175,55,.15);
}
.reading-config-card .manual-draw-toolbar {
  justify-content: center;
  gap: 12px;
}
.reading-config-card .manual-draw-status {
  color: rgba(244,241,234,.68);
  font-size: .72rem;
}

/* Same semantic share card, purpose-built landscape composition for social crawlers. */
.share-card-body.share-og-mode {
  width: 1200px !important;
  height: 630px !important;
  padding: 24px 42px !important;
  border-width: 10px !important;
}
.share-card-body.share-og-mode .share-header {
  padding-bottom: 8px;
}
.share-card-body.share-og-mode .share-main {
  min-height: 0;
  padding: 10px 0 8px;
  display: grid;
  grid-template-columns: minmax(520px, .9fr) minmax(0, 1.1fr);
  align-items: center;
  gap: 36px;
}
.share-card-body.share-og-mode .share-card-frame,
.share-card-body.share-og-mode .share-card-frame.share-three-card {
  width: 100%;
  max-width: 610px;
  margin: 0 auto;
  padding: 10px 12px;
  justify-content: center;
  gap: 10px;
}
.share-card-body.share-og-mode .share-card-frame.share-three-card .share-card-slot {
  width: 170px;
}
.share-card-body.share-og-mode .share-card-frame.share-three-card img {
  width: 146px;
  max-height: 245px;
}
.share-card-body.share-og-mode .share-card-frame.share-three-card .share-card-caption {
  max-width: 165px;
  font-size: 11px;
  line-height: 1.3;
}
.share-card-body.share-og-mode .share-info {
  min-width: 0;
  text-align: left;
  align-self: center;
}
.share-card-body.share-og-mode .share-info h2 {
  margin: 0 0 14px;
  font-size: 2rem;
  line-height: 1.2;
}
.share-card-body.share-og-mode .share-quote-container {
  gap: 4px;
}
.share-card-body.share-og-mode .share-quote {
  max-width: 510px;
  padding: 0;
  font-size: 1.48rem;
  line-height: 1.48;
  font-style: normal;
  text-wrap: balance;
}
.share-card-body.share-og-mode .quote-mark {
  font-size: 2.2rem;
}
.share-card-body.share-og-mode .share-footer {
  padding-top: 8px;
}

@media (max-width: 700px) {
  .reading-config-card {
    grid-template-columns: 1fr;
    padding: 10px;
    gap: 8px;
    border-radius: 14px;
  }
  .reading-config-group { padding: 9px 10px; }
  .reading-config-card .manual-draw-stage { grid-column: 1; padding-left: 4px; padding-right: 4px; }
}
'''
style.write_text(s, encoding='utf-8')

# 4) Focused regression tests.
test = WEB / 'tests' / 'test_share_og_and_reading_controls.py'
test.write_text(r'''from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_reading_controls_are_grouped_without_changing_controller_ids():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    css = (ROOT / 'style.css').read_text(encoding='utf-8')
    assert 'id="reading-config-card"' in html
    assert 'id="legacy-spread-picker"' in html
    assert 'id="draw-mode-picker"' in html
    assert 'id="manual-draw-stage"' in html
    assert '.reading-config-card .legacy-spread-btn.active' in css
    assert '@media (max-width: 700px)' in css


def test_social_preview_has_dedicated_landscape_render():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    css = (ROOT / 'style.css').read_text(encoding='utf-8')
    assert "template.classList.add('share-og-mode')" in js
    assert "template.classList.remove('share-og-mode')" in js
    assert 'width: 1200' in js
    assert 'height: 630' in js
    assert 'persistReadingSharePreview(ogBlob)' in js
    assert '.share-card-body.share-og-mode' in css
    assert 'width: 1200px !important' in css
    assert 'height: 630px !important' in css


def test_square_native_share_is_preserved_separately_from_og_blob():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    assert "const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))" in js
    assert 'let ogBlob = blob' in js
    assert 'const file = new File([blob]' in js
''', encoding='utf-8')

# 5) Protect both UX contracts from future regressions.
cap_path = ROOT / 'governance' / 'capabilities.json'
data = json.loads(cap_path.read_text(encoding='utf-8'))
protected = data['protected_capabilities']
og = protected['sharing.reading-og-share-preview']
og['contract'] = [
    'A reading share URL MUST expose Open Graph metadata from the immutable read-only reading receipt rather than falling back to an unrelated deck card.',
    'The browser MUST preserve the user-facing square/native share memo separately from a purpose-built 1200x630 landscape Open Graph preview for social crawlers.',
    'The landscape OG preview MUST reuse the same deck-owned cards, spread order, orientations, branding and share quote without uploading the private question or full AI answer.',
    'If no persisted share image exists, social preview MUST degrade to a card image from the same reading/deck instead of a global LeopardCat fallback.'
]
if 'website/tests/test_share_og_and_reading_controls.py' not in og.setdefault('evidence', []):
    og['evidence'].append('website/tests/test_share_og_and_reading_controls.py')
protected['reading.control-surface'] = {
    'status': 'protected',
    'owner': 'website',
    'contract': [
        'Spread selection, draw-mode selection and manual-shuffle controls remain a visually coherent reading setup surface instead of unrelated controls scattered through the ritual panel.',
        'The redesign MUST preserve the existing controller IDs and automatic/manual draw semantics.',
        'The reading setup surface MUST remain usable without horizontal page overflow on mobile.'
    ],
    'evidence': [
        'website/index.html',
        'website/style.css',
        'website/tests/test_share_og_and_reading_controls.py'
    ]
}
cap_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
