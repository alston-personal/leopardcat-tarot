from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Callable

from .schema import CompiledUnit, SymbolicCollection


@dataclass(frozen=True)
class GeneratedAsset:
    unit_id: str
    uri: str
    provider: str
    metadata: dict


class GenerationProvider(ABC):
    """Provider boundary. ArcanaForge never embeds provider credentials or billing policy."""

    id: str

    @abstractmethod
    def generate(self, unit: CompiledUnit, *, output_dir: Path) -> GeneratedAsset:
        raise NotImplementedError


class PromptFileProvider(GenerationProvider):
    """Zero-cost provider: materialize generation prompts as auditable files."""

    id = "prompt-files"

    def generate(self, unit: CompiledUnit, *, output_dir: Path) -> GeneratedAsset:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{unit.unit.id}.prompt.txt"
        path.write_text(unit.prompt + "\n\nINVARIANTS\n" + "\n".join(unit.invariants) + "\n", encoding="utf-8")
        return GeneratedAsset(unit.unit.id, str(path), self.id, {"kind": "prompt"})


class SvgProofProvider(GenerationProvider):
    """Deterministic visual proof provider used for end-to-end contracts without external model cost."""

    id = "svg-proof"

    def generate(self, unit: CompiledUnit, *, output_dir: Path) -> GeneratedAsset:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{unit.unit.id}.svg"
        title = escape(unit.unit.name)
        archetype = escape(unit.unit.archetype[:180])
        cue_lines = "".join(
            f'<text x="48" y="{540 + i*28}" font-size="18">• {escape(cue[:72])}</text>'
            for i, cue in enumerate(unit.unit.required_cues[:5])
        )
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="768" height="1344" viewBox="0 0 768 1344">
<rect width="768" height="1344" fill="#f5f0e6"/><rect x="24" y="24" width="720" height="1296" rx="24" fill="none" stroke="#222" stroke-width="4"/>
<text x="384" y="110" text-anchor="middle" font-size="40" font-family="serif">{title}</text>
<text x="384" y="165" text-anchor="middle" font-size="20">ArcanaForge semantic proof</text>
<rect x="72" y="230" width="624" height="240" rx="20" fill="#e5dfd2"/>
<text x="96" y="285" font-size="22" font-family="serif">{archetype}</text>
{cue_lines}
<text x="48" y="1250" font-size="16">{escape(unit.unit.id)}</text>
</svg>'''
        path.write_text(svg, encoding="utf-8")
        return GeneratedAsset(unit.unit.id, str(path), self.id, {"kind": "svg", "proof_only": True})


class CallableGenerationProvider(GenerationProvider):
    """Adapter for an application-supplied image model/function.

    The callback owns provider credentials and writes the resulting asset to the supplied path.
    """

    def __init__(self, provider_id: str, callback: Callable[[str, Path], dict | None], *, suffix: str = ".png") -> None:
        self.id = provider_id
        self.callback = callback
        self.suffix = suffix if suffix.startswith(".") else "." + suffix

    def generate(self, unit: CompiledUnit, *, output_dir: Path) -> GeneratedAsset:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{unit.unit.id}{self.suffix}"
        metadata = self.callback(unit.prompt, path) or {}
        if not path.exists():
            raise RuntimeError(f"generation callback did not create asset: {path}")
        return GeneratedAsset(unit.unit.id, str(path), self.id, dict(metadata))


def generate_collection(
    collection: SymbolicCollection,
    provider: GenerationProvider,
    *,
    output_dir: str | Path,
) -> tuple[GeneratedAsset, ...]:
    root = Path(output_dir)
    assets = []
    for unit in collection.units:
        asset = provider.generate(unit, output_dir=root)
        if asset.unit_id != unit.unit.id:
            raise ValueError(f"provider returned mismatched unit id: {asset.unit_id} != {unit.unit.id}")
        assets.append(asset)
    return tuple(assets)
