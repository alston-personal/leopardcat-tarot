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
DYNAMIC_PATTERNS = {
    "navigator.language": re.compile(r"navigator\.languages?|navigator\.language", re.I),
    "translation/translate API": re.compile(r"translate|translation|translator", re.I),
    "Google translation marker": re.compile(r"google.{0,30}translat|translat.{0,30}google", re.I | re.S),
    "DeepL marker": re.compile(r"deepl", re.I),
    "locale-family codes": re.compile(r"['\"](?:ja|jp|ko|fr|es|de|it|pt|th|vi|id|ms)['\"]", re.I),
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


def main() -> None:
    commits = [c for c in git("rev-list", "--all", "--", "website").splitlines() if c]
    locale_findings: dict[tuple[str, tuple[str, ...]], tuple[str, str, str]] = {}
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
                keys = tuple(payload.keys())
                # Keep unique commit+keyset evidence; this catches any historical
                # bundle with >2 languages without guessing which languages existed.
                locale_findings[(commit, keys)] = (date, subject, path)

        for path in CODE_PATHS:
            text = show(commit, path)
            if text is None:
                continue
            labels = [label for label, pattern in DYNAMIC_PATTERNS.items() if pattern.search(text)]
            if labels:
                dynamic_findings[(commit, path)] = (date, subject, labels)

    locale_rows = []
    for (commit, keys), (date, subject, path) in locale_findings.items():
        locale_rows.append((date, commit, path, list(keys), subject))
    locale_rows.sort()

    dynamic_rows = []
    for (commit, path), (date, subject, labels) in dynamic_findings.items():
        dynamic_rows.append((date, commit, path, labels, subject))
    dynamic_rows.sort()

    multi = [row for row in locale_rows if len(row[3]) > 2]
    non_zh_en = [row for row in locale_rows if set(row[3]) - {"zh", "en"}]

    lines = [
        "# i18n Full-History Audit",
        "",
        "Generated from `git rev-list --all -- website`; this inspects all locally fetched branches/tags/history rather than only current `main`.",
        "",
        f"- Website commits scanned: **{len(commits)}**",
        f"- Locale snapshots found: **{len(locale_rows)}**",
        f"- Snapshots with more than two top-level locale keys: **{len(multi)}**",
        f"- Snapshots containing keys other than `zh`/`en`: **{len(non_zh_en)}**",
        f"- Code snapshots with translation/language markers: **{len(dynamic_rows)}**",
        "",
        "## Locale snapshots beyond zh/en",
        "",
    ]

    if non_zh_en:
        for date, commit, path, keys, subject in non_zh_en:
            lines.append(f"- `{date}` `{commit[:12]}` `{path}` keys={json.dumps(keys, ensure_ascii=False)} — {subject}")
    else:
        lines.append("No canonical Git snapshot inspected here contains a locale JSON top level beyond `zh` and `en`.")

    lines += ["", "## Dynamic multilingual markers", ""]
    if dynamic_rows:
        # Collapse consecutive repeated blob-equivalent signals to a readable evidence list.
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
        "This report is evidence, not a license to invent missing translations. If the user-visible service previously supported more languages but no canonical Git snapshot contains them, the missing source may have been runtime-generated, deployed outside this repository, stored in another repository, or lost before commit. Keep `ui.multilingual` marked `regression-open` until that source is identified or an explicitly approved replacement restores equivalent capability.",
        "",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}; scanned={len(commits)} locale_snapshots={len(locale_rows)} beyond_zh_en={len(non_zh_en)} dynamic={len(dynamic_rows)}")


if __name__ == "__main__":
    main()
