from pathlib import Path
p=Path('website/main.js')
s=p.read_text(encoding='utf-8')
old1="""        document.getElementById('share-x').href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(fullShareText)}`;\n        document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encodeURIComponent(fullShareText)}`;\n"""
new1="""        document.getElementById('share-x').href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(fullShareText)}`;\n        const threadsShareU = new URL(shareUrl);\n        threadsShareU.searchParams.set('preview', String(Date.now()));\n        const threadsShareText = `${shareMsg} ${threadsShareU.toString()}`;\n        document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encodeURIComponent(threadsShareText)}`;\n"""
if old1 not in s: raise SystemExit('first threads anchor missing')
s=s.replace(old1,new1,1)
old2="""    const threadsLink = document.getElementById('share-threads');\n    if (threadsLink) threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(fullShareText)}`;\n"""
new2="""    const threadsLink = document.getElementById('share-threads');\n    if (threadsLink) {\n        const threadsShareU = new URL(shareUrl);\n        threadsShareU.searchParams.set('preview', String(Date.now()));\n        const threadsShareText = `${shareMsg} ${threadsShareU.toString()}`;\n        threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(threadsShareText)}`;\n    }\n"""
if old2 not in s: raise SystemExit('second threads anchor missing')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')

t=Path('website/tests/test_reading_og_share_preview.py')
ts=t.read_text(encoding='utf-8')
ts += '''\n\ndef test_threads_share_busts_social_preview_cache_without_changing_reading_identity():\n    js = (ROOT / 'main.js').read_text(encoding='utf-8')\n    assert "threadsShareU.searchParams.set('preview', String(Date.now()))" in js\n    assert "new URL(shareUrl)" in js\n    assert "shareU.searchParams.set('reading'" in js\n    assert "shareU.searchParams.set('share'" in js\n'''
t.write_text(ts,encoding='utf-8')
