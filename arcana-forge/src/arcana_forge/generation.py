from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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
    """Zero-cost reference provider: materialize generation prompts as auditable files."""

    id = "prompt-files"

    def generate(self, unit: CompiledUnit, *, output_dir: Path) -> GeneratedAsset:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{unit.unit.id}.prompt.txt"
        path.write_text(unit.prompt + "\n\nINVARIANTS\n" + "\n".join(unit.invariants) + "\n", encoding="utf-8")
        return GeneratedAsset(unit.unit.id, str(path), self.id, {"kind": "prompt"})


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
