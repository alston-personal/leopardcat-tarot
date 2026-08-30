from pathlib import Path

root = Path(__file__).resolve().parents[1]
main_path = root / 'website/main.js'
test_path = root / 'website/tests/test_reading_based_share_reload.py'

main = main_path.read_text(encoding='utf-8')
main = main.replace(
    "window.activeBrand = null; // Brand Pack: presentation/social identity, independent from Tarot logic\n\nconst READING_SNAPSHOT_KEY",
    "window.activeBrand = null; // Brand Pack: presentation/social identity, independent from Tarot logic\nwindow.currentShareReceipt = null; // read-only receipt identity; never grants follow-up authority\n\nconst READING_SNAPSHOT_KEY",
    1,
)
main = main.replace(
    "    window.currentReadingEnvelope = local ? data : null; // public share token never grants continuation authority.\n    window.currentReadingState",
    "    window.currentReadingEnvelope = local ? data : null; // public share token never grants continuation authority.\n    window.currentShareReceipt = data?.reading_id ? {reading_id: data.reading_id, share_token: data.share_token || shareToken || null} : null;\n    window.currentReadingState",
    1,
)
main = main.replace(
    "    window.currentReadingEnvelope = data;\n    window.currentReadingState = {",
    "    window.currentReadingEnvelope = data;\n    window.currentShareReceipt = data?.reading_id ? {reading_id: data.reading_id, share_token: data.share_token || null} : null;\n    window.currentReadingState = {",
    1,
)
main = main.replace("        const envelope = window.currentReadingEnvelope;", "        const envelope = window.currentShareReceipt || window.currentReadingEnvelope;", 1)
main = main.replace("    const envelope = window.currentReadingEnvelope;", "    const envelope = window.currentShareReceipt || window.currentReadingEnvelope;", 1)
main = main.replace(
    "    window.currentReadingEnvelope = null;\n    window.currentReadingState = null;",
    "    window.currentReadingEnvelope = null;\n    window.currentShareReceipt = null;\n    window.currentReadingState = null;",
    1,
)
if main.count('window.currentShareReceipt || window.currentReadingEnvelope') != 2:
    raise SystemExit('share receipt routing refinement incomplete')
main_path.write_text(main, encoding='utf-8')

test = test_path.read_text(encoding='utf-8')
test = test.replace("    assert 'question' not in endpoint\n    assert 'answer' not in endpoint\n", "    assert \"'question':\" not in endpoint\n    assert \"'reading':\" not in endpoint\n    assert \"'session_token':\" not in endpoint\n")
test = test.replace(
    "    assert 'session_token' not in JS.split('function updateSocialLinks',1)[1].split('function modularErrorMessage',1)[0]\n",
    "    assert 'session_token' not in JS.split('function updateSocialLinks',1)[1].split('function modularErrorMessage',1)[0]\n    assert JS.count('window.currentShareReceipt || window.currentReadingEnvelope') == 2\n",
)
test_path.write_text(test, encoding='utf-8')
print('reading-based share assertions and public reshare state refined')
