from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import random
import secrets
import uuid
from typing import Any, Protocol


class DivinationError(ValueError):
    pass


class DivinationMethod(Protocol):
    method_id: str
    def generate(self, *, input_data: dict[str, Any], question: str, rng: random.Random) -> dict[str, Any]: ...


class PersonaPack(Protocol):
    persona_id: str
    def build_prompt(self, *, method_result: dict[str, Any], question: str, lang: str) -> str: ...


@dataclass(frozen=True)
class ReadingRequest:
    method: str
    persona: str
    question: str
    input: dict[str, Any]
    lang: str = "zh-TW"
    seed: str | None = None


@dataclass
class ReadingEnvelope:
    reading_id: str
    method: str
    persona: str
    question: str
    lang: str
    created_at: str
    seed_fingerprint: str
    method_result: dict[str, Any]
    master_prompt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MethodRegistry:
    def __init__(self) -> None:
        self._items: dict[str, DivinationMethod] = {}

    def register(self, method: DivinationMethod) -> None:
        if method.method_id in self._items:
            raise DivinationError(f"duplicate method: {method.method_id}")
        self._items[method.method_id] = method

    def get(self, method_id: str) -> DivinationMethod:
        try:
            return self._items[method_id]
        except KeyError as exc:
            raise DivinationError(f"unsupported method: {method_id}") from exc

    def capabilities(self) -> list[str]:
        return sorted(self._items)


class PersonaRegistry:
    def __init__(self) -> None:
        self._items: dict[str, PersonaPack] = {}

    def register(self, persona: PersonaPack) -> None:
        if persona.persona_id in self._items:
            raise DivinationError(f"duplicate persona: {persona.persona_id}")
        self._items[persona.persona_id] = persona

    def replace(self, persona: PersonaPack) -> None:
        if persona.persona_id not in self._items:
            raise DivinationError(f"unsupported persona: {persona.persona_id}")
        self._items[persona.persona_id] = persona

    def unregister(self, persona_id: str) -> None:
        if persona_id not in self._items:
            raise DivinationError(f"unsupported persona: {persona_id}")
        del self._items[persona_id]

    def get(self, persona_id: str) -> PersonaPack:
        try:
            return self._items[persona_id]
        except KeyError as exc:
            raise DivinationError(f"unsupported persona: {persona_id}") from exc

    def capabilities(self) -> list[str]:
        return sorted(self._items)


def _stable_seed(seed: str | None) -> tuple[random.Random, str]:
    raw = seed or secrets.token_hex(32)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return random.Random(int(digest, 16)), digest[:16]


class DivinationEngine:
    def __init__(self, methods: MethodRegistry, personas: PersonaRegistry) -> None:
        self.methods = methods
        self.personas = personas

    def prepare(self, request: ReadingRequest) -> ReadingEnvelope:
        if not request.question.strip():
            raise DivinationError("question is required")
        rng, fingerprint = _stable_seed(request.seed)
        method = self.methods.get(request.method)
        persona = self.personas.get(request.persona)
        result = method.generate(input_data=request.input, question=request.question.strip(), rng=rng)
        prompt = persona.build_prompt(method_result=result, question=request.question.strip(), lang=request.lang)
        return ReadingEnvelope(
            reading_id=f"rd_{uuid.uuid4().hex}",
            method=request.method,
            persona=request.persona,
            question=request.question.strip(),
            lang=request.lang,
            created_at=datetime.now(timezone.utc).isoformat(),
            seed_fingerprint=fingerprint,
            method_result=result,
            master_prompt=prompt,
        )


class PlaceholderMethod:
    """Capability placeholder: registered only when the real school/ruleset is supplied."""
    def __init__(self, method_id: str, required_inputs: list[str]) -> None:
        self.method_id = method_id
        self.required_inputs = required_inputs

    def generate(self, *, input_data: dict[str, Any], question: str, rng: random.Random) -> dict[str, Any]:
        raise DivinationError(
            f"method '{self.method_id}' is recognized but no ruleset is installed; "
            f"required inputs: {', '.join(self.required_inputs)}"
        )
