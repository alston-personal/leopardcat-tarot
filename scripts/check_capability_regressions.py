#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = ROOT / "governance" / "capabilities.json"


def fail(message: str) -> None:
    raise SystemExit(f"CAPABILITY REGRESSION: {message}")


def require(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        fail(f"required evidence disappeared: {path}")
    return p.read_text(encoding="utf-8")


def main() -> None:
    ledger = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
    protected = ledger.get("protected_capabilities", {})
    if not protected:
        fail("capability ledger is empty")

    main_js = require("website/main.js")
    locales_text = require("website/public/locales_v10.json")
    personas = require("website/divination/personas.py")
    fortune_server = require("website/fortune_server.py")
    style_css = require("website/style.css")

    try:
        locales = json.loads(locales_text)
    except json.JSONDecodeError as exc:
        fail(f"locale bundle is invalid JSON: {exc}")

    if len(locales) < 2:
        fail("UI locale bundle shrank below two locales")

    # A fixed allow-list is the exact regression pattern that collapsed a
    # previously extensible multilingual UI to zh/en. Do not re-introduce it.
    hardcoded_patterns = [
        r"\[\s*['\"]zh['\"]\s*,\s*['\"]en['\"]\s*\]\.includes\(window\.currentLang\)",
        r"SUPPORTED_LANG(?:UAGE)?S?\s*=\s*\[\s*['\"]zh['\"]\s*,\s*['\"]en['\"]\s*\]",
    ]
    for pattern in hardcoded_patterns:
        if re.search(pattern, main_js):
            status = protected.get("ui.multilingual", {}).get("status")
            if status != "regression-open":
                fail("multilingual UI was narrowed by a hard-coded zh/en allow-list")


    # Responsive presence is not enough: protected navigation must remain reachable.
    if protected.get("navigation.mobile-reachability", {}).get("status") == "protected":
        marker = "/* Governed mobile nav reachability v3: wrap, never hide capabilities for space. */"
        if marker not in style_css:
            fail("mobile navigation reachability contract has no governed responsive implementation")
        mobile = style_css.split(marker, 1)[1]
        required_visible = [
            "#global-stats",
            ".nav-links > a",
            "#user-spirit-badge",
            "#user-dharma-name",
            ".lang-switcher",
        ]
        for selector in required_visible:
            if selector not in mobile:
                fail(f"mobile navigation reachability evidence missing selector: {selector}")
        if "flex-wrap: wrap !important" not in mobile:
            fail("mobile navigation must wrap instead of deleting capabilities for space")
        if "overflow-x: hidden !important" not in mobile:
            fail("mobile navbar horizontal-scroll regression protection disappeared")
        if "document.createElement('select')" not in main_js or "language-select" not in main_js:
            fail("compact data-driven locale selector disappeared")

    # Preserve AI multilingual platform rules.
    if "the seeker's language" not in personas:
        fail("AI multilingual response contract disappeared from personas.py")
    if "Traditional Chinese (Taiwan)" not in personas and "台灣繁體中文" not in personas:
        fail("Traditional Chinese (Taiwan) language rule disappeared")

    # Preserve zero-cost fail-closed semantics. The exact implementation may
    # evolve, but a paid fallback must never be introduced silently.
    lowered = fortune_server.lower()
    if "paid_fallback" in lowered and "paid_fallback=false" not in lowered and '"paid_fallback": false' not in lowered:
        fail("paid AI fallback appears to be enabled or ambiguous")

    print(f"Capability guard passed with {len(protected)} protected capabilities and {len(locales)} UI locale entries.")


if __name__ == "__main__":
    main()
