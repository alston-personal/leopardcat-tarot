#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = "governance/capabilities.json"
MIGRATIONS = ROOT / "governance" / "migrations"


def die(message: str) -> None:
    raise SystemExit(f"CAPABILITY LEDGER REGRESSION: {message}")


def load_current() -> dict:
    return json.loads((ROOT / LEDGER_PATH).read_text(encoding="utf-8"))


def load_base() -> dict | None:
    # In the bootstrap PR the base branch legitimately has no ledger yet.
    # Once merged, every later PR is checked against origin/main.
    proc = subprocess.run(
        ["git", "show", f"origin/main:{LEDGER_PATH}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return json.loads(proc.stdout)


def migration_exists(capability: str) -> bool:
    if not MIGRATIONS.exists():
        return False
    for path in MIGRATIONS.glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if record.get("capability") == capability and record.get("change_type") in {"deprecate", "remove"}:
            required = {"rationale", "replacement", "user_impact", "approval_reference"}
            if all(str(record.get(key, "")).strip() for key in required):
                return True
    return False


def main() -> None:
    current = load_current().get("protected_capabilities", {})
    base_doc = load_base()
    if base_doc is None:
        print("Capability ledger bootstrap: no origin/main ledger yet; monotonic comparison starts after merge.")
        return

    base = base_doc.get("protected_capabilities", {})
    for name, old in base.items():
        if name not in current:
            if not migration_exists(name):
                die(f"protected capability disappeared without migration: {name}")
            continue

        new = current[name]
        if old.get("status") == "protected" and new.get("status") != "protected":
            if not migration_exists(name):
                die(f"protected capability was downgraded: {name}")

        old_contract = set(old.get("contract", []))
        new_contract = set(new.get("contract", []))
        removed_clauses = old_contract - new_contract
        if removed_clauses and not migration_exists(name):
            die(f"contract clauses were removed from {name}: {sorted(removed_clauses)}")

    print(f"Capability ledger monotonicity passed: {len(base)} base capabilities -> {len(current)} current capabilities.")


if __name__ == "__main__":
    main()
