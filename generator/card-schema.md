# Card Schema

## Goal

One card file should support both:

- visual rendering
- future reading and website usage

This means card JSON is not only a render config. It is the shared product data layer.

## Suggested Top-Level Structure

```json
{
  "id": "card-00-the-fool",
  "arcana": "major",
  "number": "0",
  "title": "THE FOOL",
  "subtitle": "Threshold / Curiosity / Risk",
  "slug": "the-fool",
  "status": "draft",
  "size": {},
  "palette": {},
  "scene": {},
  "main_image": null,
  "generation": {},
  "ornaments": [],
  "output": "art/renders/card-00-the-fool.png",
  "meanings": {},
  "ecology": {},
  "website": {}
}
```

## Required Render Fields

- `id`
- `number`
- `title`
- `subtitle`
- `size`
- `palette`
- `output`

## Optional Generation Fields

```json
"generation": {
  "model": "gemini-2.5-flash",
  "image_size": "1K",
  "aspect_ratio": "2:3",
  "image_prompt": "A Taiwan leopard cat at a forest-road threshold..."
}
```

## Recommended Meaning Fields

```json
"meanings": {
  "upright": "New beginnings, openness, curiosity, unguarded trust.",
  "reversed": "Naivety, avoidable risk, misread danger, poor timing.",
  "keywords": ["beginnings", "risk", "curiosity", "threshold"]
}
```

## Recommended Ecology Fields

```json
"ecology": {
  "species_focus": "Taiwan leopard cat",
  "life_stage": "juvenile",
  "habitat_fragment": "forest edge and roadside grass",
  "risk_theme": "road mortality during dispersal",
  "mapping_note": "The tarot threshold becomes a literal roadside boundary."
}
```

## Recommended Website Fields

```json
"website": {
  "excerpt": "A young leopard cat steps toward the road edge, where curiosity and danger meet.",
  "seo_title": "The Fool - LeopardCat Tarot",
  "seo_description": "The Fool reimagined through juvenile leopard cat dispersal and roadside risk.",
  "tags": ["major-arcana", "road-ecology", "threshold", "leopard-cat"]
}
```

## Rules

- card files must remain readable by humans
- render-only settings should not erase interpretive meaning
- website fields should not dictate generator internals
- image paths should stay repo-relative

## 🧠 Prompt Architecture (Dual-Layer Memory)

To ensure consistency and allow for future "re-skinning" (e.g., converting Tarot to Poker cards), prompts are split into two layers:

### Layer 1: Style/Canvas Layer (Project Level)
This layer defines "How" the card looks. It is managed by Antigravity in the specific service configuration.
- **Constraints**: 2:3 vertical ratio, bold ink outlines, 1900s lithography style.
- **Rules**: Upright anthropomorphic posture, specific biological markers (ear spots, forehead stripes).

### Layer 2: Narrative/Content Layer (Card Level)
This layer defines "What" is on the card. It is stored in the `generation` field of each JSON.
- **Components**: The specific scene, tarot archetypal behavior, and ecological symbolisms.

---

## Evolution Path
... (existing stages)
Stage 5: Implement dynamic style swapping by decoupling style prompts from card-specific descriptions.
