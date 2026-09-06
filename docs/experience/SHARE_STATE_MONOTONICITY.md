# Experience IR — Share State Monotonicity

## Failure signature

A multi-card reading was correctly rendered from reading-level state, then a downstream legacy helper rebuilt social metadata from `currentDrawnCard`, collapsing the result to one card (often the first card). In parallel, deployment/parity ambiguity made the regression look like an old bundle had overwritten a newer one.

## Root cause

The system had multiple writers for the same semantic output: the canonical reading-level share context and a legacy single-card helper. Tests proved that the new spread-aware capability existed, but did not prove that later code could not downgrade it.

## Canonical rule

`reading receipt/state -> resolved share context -> rendered cards + share URL/text` is the only authoritative chain for an active reading. Once reading-level state exists, downstream helpers may format it but must not re-author it from `currentDrawnCard` or another lossy projection.

## Regression invariant

For an N-card reading, every share surface must preserve N-card identity unless a surface has an explicit documented reduction contract. A generic legacy helper is not such a contract.

## Merge gate

Any change touching reading, share, social metadata, deep links, rendering, or deployment must preserve:

1. reading-level state is authoritative;
2. three-card readings render three cards;
3. share text is derived from all reading entries;
4. receipt/deep-link identity wins over single-card fallback;
5. no later call may overwrite spread-aware state from `currentDrawnCard`;
6. production evidence must identify exact deployed SHA/artifact before a regression is classified as fixed.

## Generalized lesson

Capability tests must be monotonic, not merely existential. Do not only assert “new capability is present”; assert “no later legacy path can reduce or overwrite it.” When old and new representations coexist, define one canonical writer and turn every other path into a read-only adapter.
