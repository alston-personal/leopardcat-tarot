# Project Map

## Three Capability Domains

LeopardCat Tarot now spans three related but distinct capability domains:

1. `card-design`
2. `card-generator`
3. `reading-website`

They belong to the same product vision, but they should not be treated as the same engineering surface.

## 1. Card Design

Purpose:

- define the deck's world
- map tarot archetypes to leopard cat ecology
- shape the visual language
- write the guidebook and interpretive voice

Current folders:

- `art/`
- `copy/`
- `design/`
- `research/`

Primary outputs:

- card briefs
- narrative meaning
- art direction
- audience positioning

## 2. Card Generator

Purpose:

- turn structured card data into production assets
- compose card frames, text, ornaments, and exported PNGs
- eventually support AI-generated main images and human-made illustration sources

Current folder:

- `generator/`

Primary outputs:

- review PNGs
- presentation PNGs
- future print variants
- image delivery for Telegram and downstream apps

## 3. Reading Website

Purpose:

- display the deck as a digital product
- let users browse cards
- support draws, spreads, and interpretation flows
- connect symbolism, ecology, and reflective reading

Future concerns:

- frontend application
- reading logic
- analysis prompts
- content API or static content build

## Dependency Direction

The intended dependency direction is:

`card-design -> card-data -> generator -> reading-website`

Meaning:

- design defines the source meaning
- card data stores the structured version of that meaning
- generator renders visual assets from the data
- website consumes the same data and image outputs

The website should not become the source of truth for card meaning.

The generator should not become the source of truth for narrative interpretation.

## Recommended Repository Strategy

Current stage:

- keep everything in `leopardcat-tarot`
- treat `generator/` as an internal subproject

Future split triggers:

- split `card-generator` when it becomes reusable beyond this deck
- split `reading-website` when interaction design becomes a standalone application

## Current Development Priority

1. strengthen card data schema
2. add more real card configs
3. support real main images in the generator
4. keep render outputs stable for review workflows
5. postpone website implementation until the card data model is stable
