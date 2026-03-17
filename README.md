# LeopardCat Tarot

LeopardCat Tarot is a concept-first documentation project for a tarot deck inspired by the Taiwan leopard cat (`石虎`).

The project treats each card as both:

- a tarot archetype
- a fragment of real ecological reality

## Structure

- `art/`: visual direction and per-card image briefs
- `copy/`: descriptive writing, guidebook text, and narrative copy
- `design/`: design summary, product direction, and system-level decisions
- `generator/`: internal card-generator subproject with a future extraction boundary
- `research/`: audience notes, symbolic mapping, and supporting references

## Local Agent Bridge

This project uses the Antigravity logic/data separation model locally:

- `STATUS.md` -> local symlink to `/home/ubuntu/agent-data/projects/leopardcat-tarot/STATUS.md`
- `memory/` -> local symlink to `/home/ubuntu/agent-data/projects/leopardcat-tarot/memory`

These local bridge paths are intentionally ignored by git and should not be treated as source files for the standalone repo.

## Current Focus

- establish the deck's visual and narrative baseline
- refine major arcana starting with `The Fool`, `The Magician`, and `The High Priestess`
- keep conservation meaning and mystical resonance in balance
- build a reusable card composition tool inside the repo before deciding whether to spin it out
