from __future__ import annotations

from .schema import CompiledUnit, StyleSpec, SubjectPack, SubjectSpec, SymbolicCollection
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


def _coerce_subject(value: SubjectPack | SubjectSpec | str) -> tuple[SubjectSpec, SubjectPack | None]:
    if isinstance(value, SubjectPack):
        return value.subject, value
    if isinstance(value, SubjectSpec):
        return value, None
    return SubjectSpec(str(value)), None


def _coerce_style(value: StyleSpec | str) -> StyleSpec:
    return value if isinstance(value, StyleSpec) else StyleSpec(str(value))


def forge(
    *,
    system: str,
    subject: SubjectPack | SubjectSpec | str,
    style: StyleSpec | str,
    title: str | None = None,
    registry: ForgeRegistry | None = None,
) -> SymbolicCollection:
    active = registry or ForgeRegistry.defaults()
    symbolic_system = active.get(system)
    subject_spec, subject_pack = _coerce_subject(subject)
    style_spec = _coerce_style(style)
    compiled = []
    known_unit_ids = {unit.id for unit in symbolic_system.units()}
    if subject_pack:
        unknown = sorted(set(subject_pack.unit_overrides) - known_unit_ids)
        if unknown:
            raise ValueError(f"subject pack contains overrides for unknown system units: {', '.join(unknown)}")

    for unit in symbolic_system.units():
        scene, invariants = symbolic_system.compile_scene(unit, subject_spec, style_spec)
        override = subject_pack.unit_overrides.get(unit.id) if subject_pack else None
        meanings: dict[str, str] = {}
        visual_metadata: dict = {}
        if override:
            if override.scene:
                scene = override.scene
            meanings = dict(override.meanings)
            visual_metadata = dict(override.metadata)
        prompt = symbolic_system.compose_prompt(unit, subject_spec, style_spec, scene)
        if override and override.prompt_addendum:
            prompt += " Subject-pack directive: " + override.prompt_addendum.strip()
        compiled.append(CompiledUnit(
            unit=unit,
            scene=scene,
            prompt=prompt,
            invariants=invariants,
            meanings=meanings,
            visual_metadata=visual_metadata,
        ))

    return SymbolicCollection(
        schema="arcana-forge.collection/v0.1",
        system=symbolic_system.id,
        system_version=symbolic_system.version,
        subject=subject_spec,
        style=style_spec,
        units=tuple(compiled),
        title=title,
        subject_pack_id=subject_pack.id if subject_pack else None,
        metadata=dict(subject_pack.metadata) if subject_pack else {},
    )
