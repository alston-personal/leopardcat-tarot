from __future__ import annotations

from dataclasses import replace

from .schema import CollectionSpec, CompiledUnit, StyleSpec, SubjectSpec, SymbolicCollection
from .systems.base import SymbolicSystem
from .systems.iching import IChingSystem
from .systems.tarot import TarotSystem


class ForgeRegistry:
    def __init__(self) -> None:
        self._systems: dict[str, SymbolicSystem] = {}

    def register(self, system: SymbolicSystem) -> None:
        self._systems[system.id] = system

    def get(self, system_id: str) -> SymbolicSystem:
        try:
            return self._systems[system_id]
        except KeyError as exc:
            raise ValueError(f"unknown symbolic system: {system_id}") from exc

    @classmethod
    def defaults(cls) -> "ForgeRegistry":
        registry = cls()
        registry.register(TarotSystem())
        registry.register(IChingSystem())
        return registry


def _coerce_subject(value: SubjectSpec | str) -> SubjectSpec:
    return value if isinstance(value, SubjectSpec) else SubjectSpec(str(value))


def _coerce_style(value: StyleSpec | str) -> StyleSpec:
    return value if isinstance(value, StyleSpec) else StyleSpec(str(value))


def forge(
    *,
    system: str,
    subject: SubjectSpec | str,
    style: StyleSpec | str,
    title: str | None = None,
    registry: ForgeRegistry | None = None,
) -> SymbolicCollection:
    active = registry or ForgeRegistry.defaults()
    symbolic_system = active.get(system)
    subject_spec = _coerce_subject(subject)
    style_spec = _coerce_style(style)
    compiled = []
    for unit in symbolic_system.units():
        prompt, invariants = symbolic_system.compile_prompt(unit, subject_spec, style_spec)
        scene, _ = symbolic_system.compile_scene(unit, subject_spec, style_spec)
        compiled.append(CompiledUnit(unit=unit, scene=scene, prompt=prompt, invariants=invariants))
    return SymbolicCollection(
        schema="arcana-forge.collection/v0.1",
        system=symbolic_system.id,
        system_version=symbolic_system.version,
        subject=subject_spec,
        style=style_spec,
        units=tuple(compiled),
        title=title,
    )
