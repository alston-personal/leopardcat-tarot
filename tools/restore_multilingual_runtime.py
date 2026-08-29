#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "website" / "main.js"
INDEX = ROOT / "website" / "index.html"
LEDGER = ROOT / "governance" / "capabilities.json"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0:
        if new in text:
            return text
        raise SystemExit(f"restore_multilingual_runtime: expected source not found: {label}")
    if count != 1:
        raise SystemExit(f"restore_multilingual_runtime: ambiguous source ({count} matches): {label}")
    return text.replace(old, new, 1)


def patch_main() -> None:
    text = MAIN.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "window.currentLang = localStorage.getItem('leopard-lang') || 'zh';\nif (!['zh', 'en'].includes(window.currentLang)) window.currentLang = 'zh';",
        """window.requestedLang = localStorage.getItem('leopard-lang') || navigator.language || 'zh';
window.currentLang = window.requestedLang;
window.localeMeta = {
    zh: { label: '中', htmlLang: 'zh-TW' },
    en: { label: 'EN', htmlLang: 'en' }
};

function normalizeLocaleTag(lang) {
    return String(lang || '').trim().replace('_', '-').toLowerCase();
}

function getAvailableLocales() {
    return window.siteData && typeof window.siteData === 'object' ? Object.keys(window.siteData) : [];
}

function resolveLocale(requested) {
    const available = getAvailableLocales();
    if (!available.length) return normalizeLocaleTag(requested) || 'zh';

    const normalized = normalizeLocaleTag(requested);
    const exact = available.find(key => normalizeLocaleTag(key) === normalized);
    if (exact) return exact;

    const family = normalized.split('-')[0];
    const familyMatch = available.find(key => normalizeLocaleTag(key).split('-')[0] === family);
    if (familyMatch) return familyMatch;

    if (available.includes('zh')) return 'zh';
    if (available.includes('en')) return 'en';
    return available[0];
}

function getLocaleData(lang = window.currentLang) {
    const resolved = resolveLocale(lang);
    return (window.siteData && window.siteData[resolved]) || {};
}

function getLocalizedField(value, lang = window.currentLang) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
    const resolved = resolveLocale(lang);
    if (value[resolved] != null) return value[resolved];
    const family = normalizeLocaleTag(resolved).split('-')[0];
    const familyKey = Object.keys(value).find(key => normalizeLocaleTag(key).split('-')[0] === family);
    if (familyKey && value[familyKey] != null) return value[familyKey];
    if (value.zh != null) return value.zh;
    if (value.en != null) return value.en;
    const first = Object.keys(value)[0];
    return first ? value[first] : null;
}

function renderLanguageSwitcher() {
    const host = document.getElementById('lang-switcher');
    if (!host) return;
    const available = getAvailableLocales();
    host.innerHTML = '';
    available.forEach(lang => {
        const meta = window.localeMeta[lang] || {};
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'lang-btn';
        button.id = `btn-${lang}`;
        button.dataset.locale = lang;
        button.textContent = meta.label || lang.toUpperCase();
        button.setAttribute('aria-label', `Language: ${lang}`);
        button.addEventListener('click', () => window.setLanguage(lang));
        host.appendChild(button);
    });
}

function initializeLocaleRuntime() {
    window.currentLang = resolveLocale(window.requestedLang || window.currentLang);
    localStorage.setItem('leopard-lang', window.currentLang);
    renderLanguageSwitcher();
    const meta = window.localeMeta[window.currentLang] || {};
    document.documentElement.lang = meta.htmlLang || window.currentLang;
}""",
        "remove hard-coded locale whitelist",
    )

    text = replace_once(
        text,
        """window.setLanguage = (lang) => {
    console.log(\"Setting language to:\", lang);
    if (lang === window.currentLang) return;
    window.currentLang = lang;
    localStorage.setItem('leopard-lang', lang);
    
    // Reset Dharma name for new language
    localStorage.removeItem('userDharmaName');
    initDharmaIdentity();
    
    applyLanguage();
};""",
        """window.setLanguage = (lang) => {
    console.log(\"Setting language to:\", lang);
    const resolved = resolveLocale(lang);
    if (!getAvailableLocales().includes(resolved)) return;
    if (resolved === window.currentLang) return;
    window.requestedLang = lang;
    window.currentLang = resolved;
    localStorage.setItem('leopard-lang', resolved);
    const meta = window.localeMeta[resolved] || {};
    document.documentElement.lang = meta.htmlLang || resolved;

    // Reset Dharma name for new language
    localStorage.removeItem('userDharmaName');
    initDharmaIdentity();

    applyLanguage();
};""",
        "make setLanguage registry-aware",
    )

    text = replace_once(
        text,
        "const langData = window.siteData[window.currentLang] || window.siteData['zh'] || window.siteData['en'];",
        "const langData = getLocaleData();",
        "use locale resolver for Dharma identity",
    )

    text = replace_once(
        text,
        """            window.siteData = await cR.json();
            await window.loadActiveBrand();
            applyLanguage();""",
        """            window.siteData = await cR.json();
            initializeLocaleRuntime();
            await window.loadActiveBrand();
            applyLanguage();""",
        "initialize locale registry after loading bundle",
    )

    text = replace_once(
        text,
        """    // Normalize language key
    let lang = window.currentLang || 'zh';
    if (!window.siteData[lang]) {
        console.warn(`[i18n] Language '${lang}' not found in window.siteData, falling back to 'zh'`);
        lang = 'zh';
    }
    
    const data = window.siteData[lang];""",
        """    // Resolve against the locale bundle instead of a hard-coded language list.
    const lang = resolveLocale(window.currentLang || window.requestedLang);
    if (lang !== window.currentLang) window.currentLang = lang;
    const data = getLocaleData(lang);""",
        "make applyLanguage data-driven",
    )

    text = replace_once(
        text,
        "document.title = (window.currentLang === 'zh' ? '靈山靈貓 石虎塔羅 | LeopardCat Tarot' : 'LeopardCat Tarot | Hill Spirit Oracle');",
        "document.title = (data.hero && data.hero.title) ? `${data.hero.title} | LeopardCat Tarot` : 'LeopardCat Tarot';",
        "remove binary document title",
    )

    text = replace_once(
        text,
        """    const langData = window.siteData[window.currentLang] || window.siteData['zh'];
    const common = langData.common || {};""",
        """    const langData = getLocaleData();
    const common = langData.common || {};""",
        "make card labels locale-resolved",
    )

    text = replace_once(
        text,
        """    const title = (card.title && typeof card.title === 'object' ? card.title[window.currentLang] : card.title) || 'TBD';
    const meaning = (card.meaning && typeof card.meaning === 'object' ? card.meaning[window.currentLang] : card.meaning) || 'TBD';
    const ecology = (card.ecology && typeof card.ecology === 'object' ? card.ecology[window.currentLang] : card.ecology) || 'TBD';
    
    const lM = common.label_tarot_meaning || (window.currentLang === 'zh' ? '塔羅牌義' : 'Tarot Meaning');
    const lE = common.label_eco_connection || (window.currentLang === 'zh' ? '石虎生態' : 'Eco-Connection');""",
        """    const title = getLocalizedField(card.title) || 'TBD';
    const meaning = getLocalizedField(card.meaning) || 'TBD';
    const ecology = getLocalizedField(card.ecology) || 'TBD';

    const fallbackCommon = (window.siteData && (window.siteData.zh || window.siteData.en) || {}).common || {};
    const lM = common.label_tarot_meaning || fallbackCommon.label_tarot_meaning || 'Tarot Meaning';
    const lE = common.label_eco_connection || fallbackCommon.label_eco_connection || 'Eco-Connection';""",
        "make card content locale-resolved",
    )

    MAIN.write_text(text, encoding="utf-8")


def patch_index() -> None:
    text = INDEX.read_text(encoding="utf-8")
    text = replace_once(
        text,
        """            <div class=\"lang-switcher\">
                <button onclick=\"window.setLanguage('zh')\" class=\"lang-btn active\" id=\"btn-zh\">中</button>
                <button onclick=\"window.setLanguage('en')\" class=\"lang-btn\" id=\"btn-en\">EN</button>
            </div>""",
        """            <div class=\"lang-switcher\" id=\"lang-switcher\" aria-label=\"Language selector\"></div>""",
        "replace hard-coded language buttons",
    )
    INDEX.write_text(text, encoding="utf-8")


def protect_capability() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    cap = ledger["protected_capabilities"]["ui.multilingual"]
    cap["status"] = "protected"
    cap["implementation"] = {
        "locale_source": "website/public/locales_v10.json top-level keys",
        "runtime": "website/main.js data-driven locale resolver",
        "switcher": "website/index.html#lang-switcher rendered from available locale keys",
        "baseline_note": "Do not invent or delete locale payloads. Historical locale payload recovery is tracked separately from runtime extensibility."
    }
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    patch_main()
    patch_index()
    protect_capability()
    print("Multilingual runtime restored without replacing current modular architecture.")


if __name__ == "__main__":
    main()
