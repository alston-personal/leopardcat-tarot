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
  "model": "gemini-2.5-flash-image",
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

## Evolution Path

Stage 1:

- use card JSON for generator only

Stage 2:

- enrich card JSON with meanings and ecology

Stage 3:

- use the same JSON as website content input

Stage 4:

- add automated prompt generation and analysis from the same data source
