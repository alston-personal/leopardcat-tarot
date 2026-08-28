# ArcanaForge Architecture

## Core equation

`SymbolicSystem × SubjectPack × StyleSpec × GenerationProvider -> SymbolicCollection + Assets`

All four inputs are replaceable. Tarot is not Core; it is one built-in `SymbolicSystem` plugin.

## Responsibility boundary

ArcanaForge owns **visual-semantic compilation**:

- canonical symbolic units and invariants
- subject-specific visual translation
- style compilation
- provider-neutral prompts / generation adapters
- asset validation
- portable manifests and downstream asset packages

ArcanaForge does **not** own divination mechanics:

- Tarot shuffle/draw/spreads/reversal probability
- I Ching casting, changing lines, resulting hexagrams, interpretation rules
- session identity, persistence, persona, AI interpretation runtime

Those belong to Divination OS.

## Layers

```text
SymbolicSystem
  -> canonical SymbolicUnit[]
SubjectPack
  -> optional per-unit scene/meaning/metadata translation
StyleSpec
  -> medium/mood/palette/composition rules
Semantic compiler
  -> CompiledUnit(scene, prompt, invariants)
GenerationProvider
  -> assets
Validation
  -> fail closed on missing identity/invariants/assets
Exporter
  -> generic asset pack or method-specific compatible package
```

`SubjectPack` can enrich a unit but cannot replace its symbolic identity or system invariants. This is the core safety rule that allows `Taiwan leopard cat + I Ching` without turning 乾 into a generic cat picture.

## Built-ins in v0.1

- `tarot-rws`: 78 units
- `iching-zhouyi`: 64 King Wen hexagrams, including upper/lower trigrams and canonical bottom-to-top line patterns
- `JsonSymbolicSystem`: custom data-only symbolic systems

## Generation boundary

`GenerationProvider` contains no credentials or billing policy. Host applications own provider credentials and cost policy. `CallableGenerationProvider` adapts any real image backend; `SvgProofProvider` and `PromptFileProvider` provide deterministic/no-cost contracts.

## Downstream exports

- `divination-os.asset-pack/v0.1`: system-neutral semantic/visual pack
- current Divination OS Tarot `deck.json`: Tarot-only adapter

I Ching is never exported as a fake Tarot deck.
