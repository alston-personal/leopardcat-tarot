# Card Generator

This folder is a self-contained subproject for building tarot card mockups.

It stays inside `leopardcat-tarot` for now, but the structure is designed so it can later be extracted into its own repository with minimal changes.

## Goals

- keep card composition logic separate from deck writing
- support layered card assembly
- make per-card inputs data-driven
- preserve a clean boundary for future extraction

## Current Modules

- `cards/`: one JSON file per card
- `assets/`: reusable frame, ornament, and texture slots
- `render_card.py`: generic renderer for a single card config

## Extraction Boundary

If this becomes a reusable card engine, the intended extraction unit is:

- `generator/README.md`
- `generator/cards/`
- `generator/assets/`
- `generator/render_card.py`

The rest of the repository should treat this folder as an internal tool dependency, not as the main project root.

## Usage

```bash
python3 generator/render_card.py generator/cards/card-00-the-fool.json
```

Optional explicit output:

```bash
python3 generator/render_card.py \
  generator/cards/card-00-the-fool.json \
  --output art/renders/card-00-the-fool-v2.png
```
