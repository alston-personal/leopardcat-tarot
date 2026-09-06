from pathlib import Path

patcher = Path('.github/scripts/patch_ios_share_renderer.py')
text = patcher.read_text(encoding='utf-8')
old = 'anchor = "// 📸 Share Image Generator\\n"\n'
new = 'anchor = "// 📸 Share Image Generator\\nwindow.generateShareImage = async function() {\\n"\n'
if text.count(old) != 1:
    raise SystemExit(f'patcher anchor declaration mismatch: {text.count(old)}')
text = text.replace(old, new, 1)
# The helper must be inserted before the complete generator header, then restore that header.
old_replace = "src = src.replace(anchor, helper + anchor, 1)\n"
new_replace = "src = src.replace(anchor, helper + anchor, 1)\n"
if text.count(old_replace) != 1:
    raise SystemExit('patcher replace expression mismatch')
exec(compile(text, str(patcher), 'exec'), {'__name__': '__main__'})
Path('.github/scripts/patch_ios_share_renderer_v2.py').unlink(missing_ok=True)
