from __future__ import annotations

import json
from pathlib import Path

from .exporters.divination_os import export_divination_os, export_tarot_deck_manifest
from .forge import ForgeRegistry, forge
from .generation import PromptFileProvider, SvgProofProvider, generate_collection
from .packs import load_subject_pack
from .systems import JsonSymbolicSystem
from .validation import require_valid_assets, require_valid_collection


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="arcana-forge")
    parser.add_argument("system", help="built-in system id, e.g. tarot-rws or iching-zhouyi")
    parser.add_argument("subject", nargs="?", help="recurring subject/concept; omit when --subject-pack is used")
    parser.add_argument("style", help="visual style")
    parser.add_argument("--system-file", help="JSON symbolic-system plugin to register before forging")
    parser.add_argument("--subject-pack", help="portable ArcanaForge subject-pack JSON")
    parser.add_argument("--title")
    parser.add_argument("--format", choices=["collection", "asset-pack", "tarot-deck"], default="collection")
    parser.add_argument("--id", dest="collection_id", help="collection/deck id for exported formats")
    parser.add_argument("--divination-os-id", help="backward-compatible alias for --format asset-pack --id")
    parser.add_argument("--provider", choices=["none", "prompt", "svg"], default="none")
    parser.add_argument("--generate-dir", help="materialize provider output here")
    parser.add_argument("--output", help="write JSON manifest to this path instead of stdout")
    parser.add_argument("--creator", default="ArcanaForge")
    parser.add_argument("--default-persona", default="master")
    parser.add_argument("--no-reversals", action="store_true")
    args = parser.parse_args()

    registry = ForgeRegistry.defaults()
    if args.system_file:
        registry.register(JsonSymbolicSystem.from_file(args.system_file))

    if args.subject_pack and args.subject:
        parser.error("use either positional subject or --subject-pack, not both")
    if not args.subject_pack and not args.subject:
        parser.error("subject is required unless --subject-pack is provided")
    subject = load_subject_pack(args.subject_pack) if args.subject_pack else args.subject

    collection = require_valid_collection(forge(
        system=args.system,
        subject=subject,
        style=args.style,
        title=args.title,
        registry=registry,
    ))

    assets = ()
    if args.provider != "none":
        if not args.generate_dir:
            parser.error("--generate-dir is required when --provider is prompt or svg")
        provider = PromptFileProvider() if args.provider == "prompt" else SvgProofProvider()
        assets = generate_collection(collection, provider, output_dir=args.generate_dir)
        require_valid_assets(collection, assets)

    output_format = args.format
    collection_id = args.collection_id
    if args.divination_os_id:
        output_format = "asset-pack"
        collection_id = args.divination_os_id

    if output_format == "collection":
        payload = collection.to_manifest()
    elif output_format == "asset-pack":
        if not collection_id:
            parser.error("--id is required for asset-pack export")
        payload = export_divination_os(collection, collection_id=collection_id)
        if assets:
            asset_map = {asset.unit_id: asset.uri for asset in assets}
            for unit in payload["units"]:
                unit["asset"] = asset_map.get(unit["id"])
    else:
        if not collection_id:
            parser.error("--id is required for tarot-deck export")
        payload = export_tarot_deck_manifest(
            collection,
            deck_id=collection_id,
            creator=args.creator,
            default_persona=args.default_persona,
            reversals=not args.no_reversals,
            image_paths={asset.unit_id: asset.uri for asset in assets} if assets else None,
        )

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
