# 📜 LeopardCat Tarot: Project Protocol & Style Bible
**Target**: Ensure consistent generation of the Taiwan Leopard Cat Tarot deck.

---

## 🎨 1. The Dual-Layer Prompt Rule (CRITICAL)
Every image generation MUST combine two distinct layers to maintain style consistency and narrative depth.

### Layer 1: The Style Baseline (Constant)
**Prompt Snippet**: 
> "Vertical 2:3 aspect ratio, 1900s mystical tarot lithography, bold ink outlines, aged paper texture. Anthropomorphic Taiwan leopard cat with distinct white ear-spots, facial stripes, and rosette patterns. Classical esoteric woodcut aesthetic."

### Layer 2: The Narrative Content (Variable)
**Definition**: The specific scene described in the card's `JSON` or `Markdown` description.

---

## 🧬 2. Biological Consistency
- **Species**: Prionailurus bengalensis chinensis (Taiwan Leopard Cat).
- **Mandatory Features**:
    - White spots on the back of the ears.
    - Two prominent white stripes on the forehead and facial markings.
    - Distinctive dark rosettes (not just spots) on the body and tail.
- **Forbidden**: Do not use generic "leopard" or "domestic cat" patterns.

---

## 📂 3. Technical Specs
- **Aspect Ratio**: 2:3
- **Resolution Target**: 1K (1024x1536)
- **Model Preference**: Gemini 2.0 Flash (Experimental Image Generation) or specialized image generation tools.
- **Reference Files**:
    - `/home/ubuntu/leopardcat-tarot/generator/card-schema.md`
    - `/home/ubuntu/leopardcat-tarot/generator/SERVICE_SPEC.md`

---

## 🛡️ 4. Agent Execution Rule
Whenever an Agent works on this project, it **MUST** read this `PROTOCOL.md` first to avoid "style drift" or "context forgetting".
