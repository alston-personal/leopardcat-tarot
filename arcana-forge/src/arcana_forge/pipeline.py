from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .exporters.divination_os import export_divination_os, export_tarot_deck_manifest
from .forge import ForgeRegistry, forge
from .generation import GeneratedAsset, GenerationProvider, generate_collection
from .schema import StyleSpec, SubjectSpec, SymbolicCollection
from .validation import require_valid_assets, require_valid_collection


@dataclass(frozen=True)
class ForgeBuild:
    collection: SymbolicCollection
    assets: tuple[GeneratedAsset, ...]

    def asset_map(self) -> dict[str, str]:
        return {asset.unit_id: asset.uri for asset in self.assets}

    def export_asset_pack(self, *, collection_id: str) -> dict:
        return export_divination_os(self.collection, collection_id=collection_id)

    def export_tarot_deck(
        self,
        *,
        deck_id: str,
        creator: str = "ArcanaForge",
        description: str = "",
        default_persona: str = "master",
        reversals: bool = True,
    ) -> dict:
        return export_tarot_deck_manifest(
            self.collection,
            deck_id=deck_id,
            creator=creator,
            description=description,
            default_persona=default_persona,
            reversals=reversals,
            image_paths=self.asset_map(),
        )


class ForgePipeline:
    def __init__(self, registry: ForgeRegistry | None = None) -> None:
        self.registry = registry or ForgeRegistry.defaults()

    def compile(
        self,
        *,
        system: str,
        subject: SubjectSpec | str,
        style: StyleSpec | str,
        title: str | None = None,
    ) -> SymbolicCollection:
        collection = forge(
            system=system,
            subject=subject,
            style=style,
            title=title,
            registry=self.registry,
        )
        return require_valid_collection(collection)

    def build(
        self,
        *,
        system: str,
        subject: SubjectSpec | str,
        style: StyleSpec | str,
        provider: GenerationProvider,
        output_dir: str | Path,
        title: str | None = None,
    ) -> ForgeBuild:
        collection = self.compile(system=system, subject=subject, style=style, title=title)
        assets = generate_collection(collection, provider, output_dir=output_dir)
        require_valid_assets(collection, assets)
        return ForgeBuild(collection=collection, assets=assets)
