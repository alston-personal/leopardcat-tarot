from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import DivinationError


class ConfigurablePersona:
    def __init__(self, pack_path: str | Path) -> None:
        self.pack_path = Path(pack_path)
        try:
            self.config = json.loads(self.pack_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise DivinationError(f"invalid oracle pack: {self.pack_path}") from exc
        self.persona_id = str(self.config.get("id") or "").strip()
        if not self.persona_id:
            raise DivinationError(f"oracle pack missing id: {self.pack_path}")

    def public_info(self) -> dict[str, Any]:
        identity = self.config.get("identity") or {}
        return {
            "persona_id": self.persona_id,
            "name": str(identity.get("name") or self.persona_id),
            "role": str(identity.get("role") or ""),
            "source": "pack",
        }

    def build_prompt(self, *, method_result: dict[str, Any], question: str, lang: str) -> str:
        language = "台灣繁體中文" if lang.lower().startswith("zh") else "the seeker's language"
        payload = json.dumps(method_result, ensure_ascii=False, indent=2)
        identity = self.config.get("identity", {})
        voice = self.config.get("voice", [])
        principles = self.config.get("interpretation_principles", [])
        domain_context = self.config.get("domain_context", [])
        closing = self.config.get("closing_instruction", "")
        safety = self.config.get("safety", [])

        def bullets(items: Any) -> str:
            if not isinstance(items, list):
                return ""
            return "\n".join(f"- {x}" for x in items)

        return f"""You are {identity.get('name', self.persona_id)}.
{identity.get('role', '')}
The divination method engine has already produced the immutable symbolic result below. Never redraw, replace, flip, alter, or invent method output.

Voice:
{bullets(voice)}

Domain context:
{bullets(domain_context)}

Interpretation discipline:
{bullets(principles)}

Safety and epistemic boundaries:
{bullets(safety)}

Language: answer in {language}. For Chinese, strictly use Traditional Chinese (Taiwan).
{closing}

Seeker question:
{question}

Immutable divination result:
{payload}
"""


class GenericMasterPersona:
    persona_id = "master"

    def public_info(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "name": "通用解牌師",
            "role": "中立、謹慎、實用的塔羅解讀 Persona",
            "source": "builtin",
        }

    def build_prompt(self, *, method_result: dict[str, Any], question: str, lang: str) -> str:
        payload = json.dumps(method_result, ensure_ascii=False, indent=2)
        language = "Traditional Chinese (Taiwan)" if lang.lower().startswith("zh") else "the seeker's language"
        return f"""You are a careful divination interpreter. The method engine has already produced the immutable symbolic result below. Do not redraw or alter it. Interpret structure and interactions faithfully, avoid deterministic claims, and give practical reflective guidance in {language}.

Question: {question}
Result:
{payload}
"""


def persona_public_info(persona: Any) -> dict[str, Any]:
    if hasattr(persona, "public_info"):
        data = persona.public_info()
        if isinstance(data, dict):
            return data
    return {
        "persona_id": str(getattr(persona, "persona_id", "unknown")),
        "name": str(getattr(persona, "persona_id", "unknown")),
        "role": "",
        "source": "unknown",
    }
