from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SubjectSpec:
    concept: str
    role: str = "recurring visual subject"
    traits: tuple[str, ...] = ()


@dataclass(frozen=True)
class StyleSpec:
    name: str
    medium: str | None = None
    mood: tuple[str, ...] = ()
    palette: tuple[str, ...] = ()
    composition_rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class SymbolicUnit:
    id: str
    number: int
    name: str
    archetype: str
    keywords: tuple[str, ...]
    required_cues: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompiledUnit:
    unit: SymbolicUnit
    scene: str
    prompt: str
    invariants: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["unit"] = asdict(self.unit)
        return value


@dataclass(frozen=True)
class CollectionSpec:
    system: str
    subject: SubjectSpec
    style: StyleSpec
    title: str | None = None


@dataclass(frozen=True)
class SymbolicCollection:
    schema: str
    system: str
    system_version: str
    subject: SubjectSpec
    style: StyleSpec
    units: tuple[CompiledUnit, ...]
    title: str | None = None

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "system": self.system,
            "system_version": self.system_version,
            "title": self.title,
            "subject": asdict(self.subject),
            "style": asdict(self.style),
            "units": [item.to_dict() for item in self.units],
        }
