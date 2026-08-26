from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from typing import Any


SCHEMA = "divination-reading/1"


def build_capsule(*, reading_id: str, method: str, persona: str, question: str, lang: str, method_result: dict[str, Any]) -> dict[str, Any]:
    """Build a portable, provider-neutral reading IR without persisting it."""
    return {
        "schema": SCHEMA,
        "reading_id": reading_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "persona": persona,
        "question": question,
        "lang": lang,
        "result": deepcopy(method_result),
        "contract": {
            "immutable_result": True,
            "redraw_forbidden": True,
            "certainty_forbidden": True,
            "preserve_positions": True,
        },
    }


def compile_prompt(capsule: dict[str, Any], provider: str = "generic") -> str:
    """Compile the canonical capsule into a self-contained external-AI prompt."""
    provider = str(provider or "generic").lower()
    lang = str(capsule.get("lang") or "zh-TW")
    language_rule = "請使用台灣繁體中文回答。" if lang.lower().startswith("zh") else "Reply in the seeker's language."
    payload = json.dumps(capsule, ensure_ascii=False, indent=2)
    provider_hint = {
        "chatgpt": "You are interpreting a portable Divination Reading Capsule in ChatGPT.",
        "claude": "You are interpreting a portable Divination Reading Capsule in Claude.",
        "gemini": "You are interpreting a portable Divination Reading Capsule in Gemini.",
    }.get(provider, "You are interpreting a portable Divination Reading Capsule.")
    return f"""{provider_hint}

Rules:
1. The symbolic result inside the capsule is immutable. Never redraw, replace, reorder, flip, or invent cards/symbols.
2. Respect spread positions, orientation, combination grammar, and method-specific structural fields.
3. Divination is reflective guidance, not certain prediction, diagnosis, legal advice, or financial certainty.
4. {language_rule}
5. First explain the structure, then synthesize the reading, then give 1–3 practical reflective actions.

Reading Capsule JSON:
{payload}
"""


def public_handoff(capsule: dict[str, Any]) -> dict[str, Any]:
    """Return copyable prompts + provider destinations. No provider is auto-paid or auto-selected."""
    return {
        "capsule": capsule,
        "providers": [
            {"id": "chatgpt", "name": "ChatGPT", "url": "https://chatgpt.com/", "prompt": compile_prompt(capsule, "chatgpt")},
            {"id": "claude", "name": "Claude", "url": "https://claude.ai/", "prompt": compile_prompt(capsule, "claude")},
            {"id": "gemini", "name": "Gemini", "url": "https://gemini.google.com/", "prompt": compile_prompt(capsule, "gemini")},
        ],
        "generic_prompt": compile_prompt(capsule),
    }
