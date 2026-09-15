from pathlib import Path

TARGET = Path('website/main.js')
text = TARGET.read_text(encoding='utf-8')

HELPER = r'''
async function fetchInitJson(resourceName, url, { retry = true } = {}) {
    const attempt = async (attemptNo) => {
        const response = await fetch(url, { cache: 'no-cache' });
        const contentType = response.headers.get('content-type') || '';
        const raw = await response.text();
        if (!response.ok) {
            const error = new Error(`${resourceName} HTTP ${response.status}`);
            error.name = 'InitResourceError';
            error.resource = resourceName;
            error.status = response.status;
            error.contentType = contentType;
            error.preview = raw.slice(0, 120).replace(/\s+/g, ' ');
            throw error;
        }
        try {
            return JSON.parse(raw);
        } catch (cause) {
            if (retry && attemptNo === 1) {
                const retryUrl = new URL(url, location.href);
                retryUrl.searchParams.set('_lc_json_retry', String(Date.now()));
                return attempt(2, retryUrl.toString());
            }
            const error = new Error(`${resourceName} invalid JSON`);
            error.name = 'InitJsonError';
            error.resource = resourceName;
            error.status = response.status;
            error.contentType = contentType;
            error.preview = raw.slice(0, 120).replace(/\s+/g, ' ');
            error.cause = cause;
            throw error;
        }
    };

    const first = new URL(url, location.href);
    if (!first.searchParams.has('_lc_json_probe')) {
        first.searchParams.set('_lc_json_probe', String(Date.now()));
    }
    return attempt(1, first.toString());
}
'''.strip()

anchor = '// Initialize All Systems\n'
if 'async function fetchInitJson(' not in text:
    if anchor not in text:
        raise SystemExit('guard failed: init anchor missing')
    text = text.replace(anchor, HELPER + '\n\n' + anchor, 1)

old_locales = """        const cR = await fetch(`locales_v10.json?v=${ts}`, { cache: 'no-cache' });"""
new_locales = """        const localesUrl = `locales_v10.json?v=${ts}`;"""
if old_locales in text:
    text = text.replace(old_locales, new_locales, 1)

old_locales_block = """        if (cR.ok) {\n            window.siteData = await cR.json();\n            initializeLocaleRuntime();"""
new_locales_block = """        {\n            window.siteData = await fetchInitJson('locales_v10.json', localesUrl);\n            initializeLocaleRuntime();"""
if old_locales_block in text:
    text = text.replace(old_locales_block, new_locales_block, 1)

old_manifest = """            const mR = await fetch(`manifest.json?v=${ts}`, { cache: 'no-cache' });\n            if (mR.ok) {\n                window.cardData = await mR.json();"""
new_manifest = """            const manifestUrl = `manifest.json?v=${ts}`;\n            {\n                window.cardData = await fetchInitJson('manifest.json', manifestUrl);"""
if old_manifest in text:
    text = text.replace(old_manifest, new_manifest, 1)

old_err = """        const errType = err.name || \"Error\";\n        const errMsg = err.message || \"Unknown Failure\";"""
new_err = """        const errType = err.name || \"Error\";\n        const resource = err.resource ? ` [${err.resource}]` : '';\n        const status = err.status ? ` HTTP ${err.status}` : '';\n        const contentType = err.contentType ? ` ${err.contentType}` : '';\n        const preview = err.preview ? ` | response: ${err.preview}` : '';\n        const errMsg = `${err.message || \"Unknown Failure\"}${resource}${status}${contentType}${preview}`;"""
if old_err in text:
    text = text.replace(old_err, new_err, 1)

# Regression guards: initialization JSON must go through the diagnostic loader.
if "await cR.json()" in text:
    raise SystemExit('guard failed: locales still uses naked response.json()')
if "window.cardData = await mR.json()" in text:
    raise SystemExit('guard failed: manifest still uses naked response.json()')
if "fetchInitJson('locales_v10.json'" not in text:
    raise SystemExit('guard failed: locales diagnostic loader missing')
if "fetchInitJson('manifest.json'" not in text:
    raise SystemExit('guard failed: manifest diagnostic loader missing')

TARGET.write_text(text, encoding='utf-8')
print('guarded init JSON diagnostics present')
