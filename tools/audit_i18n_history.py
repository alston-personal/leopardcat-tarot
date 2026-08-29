#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "i18n-history-audit.md"

LOCALE_PATHS = [
    "website/public/locales_v10.json",
    "website/public/content.json",
    "website/content.json",
]
CODE_PATHS = ["website/main.js", "website/index.html", "website/fortune_server.py"]

# Constrain detection to plausible language roots so ordinary JSON sections such
# as nav/hero/meta are not misreported as languages. Region/script suffixes are
# still accepted (for example zh-TW, pt-BR, zh-Hant).
LANGUAGE_ROOTS = {
    "ar", "bg", "ca", "cs", "da", "de", "el", "en", "es", "fi", "fr",
    "he", "hi", "hr", "hu", "id", "it", "ja", "ko", "ms", "nl", "no",
    "pl", "pt", "ro", "ru", "sk", "sv", "th", "tl", "tr", "uk", "vi", "zh",
}
LOCALE_TAG = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")

DYNAMIC_PATTERNS = {
    "navigator.language": re.compile(r"navigator\.languages?|navigator\.language", re.I),
    "translation/translate API": re.compile(r"translate|translation|translator", re.I),
    "Google translation marker": re.compile(r"google.{0,30}translat|translat.{0,30}google", re.I | re.S),
    "DeepL marker": re.compile(r"deepl", re.I),
    "extra locale-family codes": re.compile(r"['\"](?:ja|ko|fr|es|de|it|pt|ru|th|vi|id|ms|ar|hi)['\"]", re.I),
}


def git(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if check and proc.returncode:
        raise RuntimeError(proc.stderr.strip() or "git command failed")
    return proc.stdout


def show(commit: str, path: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, text=True, capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


def meta(commit: str) -> tuple[str, str]:
    raw = git("show", "-s", "--format=%cI%x00%s", commit).rstrip("\n")
    date, _, subject = raw.partition("\x00")
    return date, subject


def locale_keys(payload: dict) -> tuple[str, ...]:
    keys: list[str] = []
    for key, value in payload.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        if not LOCALE_TAG.fullmatch(key):
            continue
        root = key.split("-", 1)[0].lower()
        if root in LANGUAGE_ROOTS:
            keys.append(key)
    return tuple(keys)


def main() -> None:
    commits = [c for c in git("rev-list", "--all", "--", "website").splitlines() if c]
    locale_findings: dict[tuple[str, str, tuple[str, ...]], tuple[str, str]] = {}
    dynamic_findings: dict[tuple[str, str], tuple[str, str, list[str]]] = {}

    for commit in commits:
        date, subject = meta(commit)
        for path in LOCALE_PATHS:
            text = show(commit, path)
            if text is None:
                continue
            try:
                payload = json.loads(text)
            except Exception:
                continue
            if isinstance(payload, dict):
                keys = locale_keys(payload)
                if keys:
                    locale_findings[(commit, path, keys)] = (date, subject)

        for path in CODE_PATHS:
            text = show(commit, path)
            if text is None:
                continue
            labels = [label for label, pattern in DYNAMIC_PATTERNS.items() if pattern.search(text)]
            if labels:
                dynamic_findings[(commit, path)] = (date, subject, labels)

    locale_rows = []
    for (commit, path, keys), (date, subject) in locale_findings.items():
        locale_rows.append((date, commit, path, list(keys), subject))
    locale_rows.sort()

    dynamic_rows = []
    for (commit, path), (date, subject, labels) in dynamic_findings.items():
        dynamic_rows.append((date, commit, path, labels, subject))
    dynamic_rows.sort()

    multi = [row for row in locale_rows if len(row[3]) > 2]
    non_zh_en = [row for row in locale_rows if {key.split("-", 1)[0].lower() for key in row[3]} - {"zh", "en"}]

    lines = [
        "# i18n Full-History Audit",
        "",
        "Generated from `git rev-list --all -- website`; this inspects all fetched branches, tags and website history rather than only current `main`.",
        "",
        "Locale detection only counts dictionary-valued BCP-47-like keys whose language root is in the audit's language-root registry. Ordinary JSON sections such as `nav`, `hero` or `meta` are not languages.",
        "",
        f"- Website commits scanned: **{len(commits)}**",
        f"- Locale-bearing snapshots found: **{len(locale_rows)}**",
        f"- Snapshots with more than two locale keys: **{len(multi)}**",
        f"- Snapshots containing language roots beyond `zh`/`en`: **{len(non_zh_en)}**",
        f"- Code snapshots with translation/language markers: **{len(dynamic_rows)}**",
        "",
        "## Locale snapshots beyond zh/en",
        "",
    ]

    if non_zh_en:
        for date, commit, path, keys, subject in non_zh_en:
            lines.append(f"- `{date}` `{commit[:12]}` `{path}` locales={json.dumps(keys, ensure_ascii=False)} — {subject}")
    else:
        lines.append("No canonical Git snapshot inspected here contains a locale dictionary beyond the zh/en language families.")

    lines += ["", "## Dynamic multilingual markers", ""]
    if dynamic_rows:
        seen = set()
        for date, commit, path, labels, subject in dynamic_rows:
            signature = (path, tuple(labels), subject)
            if signature in seen:
                continue
            seen.add(signature)
            lines.append(f"- `{date}` `{commit[:12]}` `{path}`: {', '.join(labels)} — {subject}")
    else:
        lines.append("No configured dynamic translation marker was found in the inspected website code paths.")

    lines += [
        "",
        "## Interpretation guardrail",
        "",
        "A commit message containing 'multilingual' or a generic word such as 'translate' is not by itself evidence of UI locale support. UI locale evidence requires an actual locale dictionary or explicit runtime translation implementation. AI response-language support is tracked separately under `ai.multilingual`.",
        "",
        "If the user-visible service previously supported additional UI languages but no canonical Git snapshot contains them, the missing source may have been runtime-generated, deployed outside this repository, stored in another repository, or lost before commit. Keep `ui.multilingual` marked `regression-open` until that source is identified or an explicitly approved replacement restores equivalent capability.",
        "",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; scanned={len(commits)} locale_snapshots={len(locale_rows)} beyond_zh_en={len(non_zh_en)} dynamic={len(dynamic_rows)}")
    for date, commit, path, keys, subject in non_zh_en:
        print(f"EXTRA_LOCALE {date} {commit[:12]} {path} {json.dumps(keys, ensure_ascii=False)} {subject}")


if __name__ == "__main__":
    main()
