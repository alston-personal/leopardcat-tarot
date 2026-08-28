from __future__ import annotations

from abc import ABC, abstractmethod

from arcana_forge.schema import StyleSpec, SubjectSpec, SymbolicUnit


class SymbolicSystem(ABC):
    id: str
    version: str = "1"

    @abstractmethod
    def units(self) -> tuple[SymbolicUnit, ...]: ...

    def compile_scene(self, unit: SymbolicUnit, subject: SubjectSpec, style: StyleSpec) -> tuple[str, tuple[str, ...]]:
        cues = ", ".join(unit.required_cues) if unit.required_cues else ", ".join(unit.keywords)
        scene = f"{subject.concept} embodies {unit.name}: {unit.archetype}; preserve visual cues: {cues}."
        invariants = (
            f"Preserve symbolic identity: {unit.name}",
            *(f"Preserve cue: {cue}" for cue in unit.required_cues),
        )
        return scene, invariants

    def compile_prompt(self, unit: SymbolicUnit, subject: SubjectSpec, style: StyleSpec) -> tuple[str, tuple[str, ...]]:
        scene, invariants = self.compile_scene(unit, subject, style)
        medium = f", medium: {style.medium}" if style.medium else ""
        mood = f", mood: {', '.join(style.mood)}" if style.mood else ""
        palette = f", palette: {', '.join(style.palette)}" if style.palette else ""
        prompt = f"Create a symbolic illustration. System={self.id}; unit={unit.name}; subject={subject.concept}; style={style.name}{medium}{mood}{palette}. {scene}"
        return prompt, invariants
