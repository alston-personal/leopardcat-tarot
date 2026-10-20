#!/usr/bin/env python3
"""Read-only, fail-closed production persona acceptance gate.

This is deliberately not a deploy tool or proof of a successful card reading.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request

PERSONA = "ocean-current-master"
PATH = "/api/v1/personas?deck=leopardcat"


def fetch(origin):
    req = urllib.request.Request(origin.rstrip("/") + PATH, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("unexpected HTTP status")
        return json.load(response)


def has_persona(payload):
    def walk(value):
        if isinstance(value, dict):
            if value.get("id") == PERSONA or value.get("persona_id") == PERSONA or value.get("slug") == PERSONA:
                return True
            return any(walk(v) for v in value.values())
        if isinstance(value, list):
            return any(walk(v) for v in value)
        return False
    return walk(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", default="http://127.0.0.1:8088")
    parser.add_argument("--public", default="https://leopardcat-tarot.milkcat.org")
    args = parser.parse_args()
    passed = True
    for name, origin in (("local", args.local), ("public", args.public)):
        try:
            found = has_persona(fetch(origin))
            print(json.dumps({"probe": name, "persona": PERSONA, "present": found}))
            passed &= found
        except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
            print(json.dumps({"probe": name, "persona": PERSONA, "present": False, "error_type": type(exc).__name__}))
            passed = False
    if not passed:
        print("FAIL: backend persona parity is not proven", file=sys.stderr)
        return 1
    print("PASS: persona listed on local and public backend; single-card reading NOT verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
