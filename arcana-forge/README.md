# ArcanaForge

ArcanaForge is a system-agnostic symbolic asset compiler.

`SymbolicSystem × Subject × Style -> SymbolicCollection`

It does **not** implement divination logic. Tarot spreads, I Ching casting/changing-line rules, and interpretation runtime belong to Divination OS. ArcanaForge defines what symbolic units mean, how a subject/style may translate them visually, and exports portable manifests for renderers and downstream products.

## v0.1

- pluggable `SymbolicSystem`
- full 78-unit Tarot system
- full 64-unit I Ching system
- subject/style specs
- deterministic semantic scene plans
- provider-neutral generation prompts
- Divination OS exporter
- LeopardCat reference preset

```python
from arcana_forge import forge

collection = forge(
    system="iching",
    subject="Taiwan leopard cat",
    style="sacred Chinese ink",
)
assert len(collection.units) == 64
```

The directory is intentionally self-contained so it can be moved unchanged into the dedicated `alston-personal/arcana-forge` repository.
