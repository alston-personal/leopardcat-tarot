from pathlib import Path

main = Path('website/main.js')
src = main.read_text(encoding='utf-8')
old = "        void persistReadingSharePreview(ogBlob); // preview persistence is best-effort and never blocks native share.\n"
new = """        if (isIOSShareRuntime()) {\n            void persistReadingSharePreview(ogBlob); // best-effort: never block iOS native share.\n        } else {\n            await persistReadingSharePreview(ogBlob); // preserve desktop/OG-before-share contract.\n        }\n"""
if src.count(old) != 1:
    raise SystemExit(f'preview persistence anchor mismatch: {src.count(old)}')
main.write_text(src.replace(old, new, 1), encoding='utf-8')

test = Path('website/tests/test_ios_share_renderer.py')
s = test.read_text(encoding='utf-8')
needle = "    assert 'void persistReadingSharePreview(ogBlob)' in src\n"
replacement = "    assert 'void persistReadingSharePreview(ogBlob)' in src\n    assert 'await persistReadingSharePreview(ogBlob)' in src\n"
if s.count(needle) != 1:
    raise SystemExit('focused test anchor mismatch')
test.write_text(s.replace(needle, replacement, 1), encoding='utf-8')

Path('.github/scripts/fix_ios_preview_contract.py').unlink(missing_ok=True)
Path('.github/workflows/fix-ios-preview-contract.yml').unlink(missing_ok=True)
