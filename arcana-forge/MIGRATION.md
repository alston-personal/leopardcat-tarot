# ArcanaForge Extraction / Migration

ArcanaForge is staged under `leopardcat-tarot/arcana-forge/` only because the current GitHub connector cannot create a repository. The directory is self-contained and is intended to move unchanged to `alston-personal/arcana-forge`.

## LeopardCat migration

The legacy project already contains 78 rich card definitions under `generator/cards/`. They are not discarded.

```bash
arcana-forge-migrate-leopardcat generator/cards leopardcat.subject-pack.json
```

The one-shot importer converts legacy data into `arcana-forge.subject-pack/v0.1`:

- `generation.narrative` -> per-unit scene translation
- upright/reversed meanings -> Subject Pack meanings
- ecology, ornaments, website metadata and palette -> visual metadata
- legacy card IDs -> canonical ArcanaForge Tarot IDs

After this export, the resulting Subject Pack is standalone. Normal ArcanaForge execution no longer needs the LeopardCat repository or its legacy generator files.

## What remains in LeopardCat Tarot

After the dedicated repository exists and compatibility is proven:

- generated/current LeopardCat visual assets
- LeopardCat Subject Pack / product preset
- Divination OS product integration

The old `generator/` can then be retired or retained only as historical source evidence. It should not remain the canonical generator implementation.

## Repository move

Once `alston-personal/arcana-forge` exists:

1. copy the contents of this `arcana-forge/` directory to repository root;
2. preserve package tests and CI contract;
3. run all contracts in the new repository;
4. migrate LeopardCat 78-card definitions to a portable Subject Pack;
5. make LeopardCat consume the package/pack rather than internal generator code;
6. only then remove duplicated generator implementation from LeopardCat.

No Divination OS casting/draw logic moves into ArcanaForge.
