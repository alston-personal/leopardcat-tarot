# Generator Architecture

## Design Intent

The generator should eventually support a layered workflow:

1. main illustration
2. optional ornaments
3. frame overlay
4. text overlay
5. texture / finishing layer
6. export variants

The current MVP keeps the contract simple while leaving room to swap in better art sources later.

## Data Contract

Each card JSON should describe:

- `id`
- `number`
- `title`
- `subtitle`
- `size`
- `palette`
- `scene`
- `main_image` or scene fallback data
- `ornaments`
- `output`

## Separation Rule

The renderer should know how to compose a card.

The card JSON should know what to compose.

The project documentation should explain why the card exists and what it means.

## Future Extraction Checklist

- move `generator/` into a dedicated repository
- add packaging metadata
- convert hard-coded fallback illustration helpers into reusable modules
- support external assets instead of procedural placeholders
- add batch rendering for full decks
