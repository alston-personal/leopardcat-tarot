# Master Spread Authority — CEIR

Issue: #69

## Failure pattern

The product had two independent spread planners:

1. browser-side `automaticSpreadForQuestion()` reduced `auto` to `single`/`three_card` before the request reached the divination engine;
2. server-side Tarot `_auto_spread()` had a different keyword policy.

A typed short question could therefore become a one-card reading while a Threads-source question, after resolution to longer source text, usually became a three-card reading. The share renderer then faithfully rendered the already-diverged reading receipt, making the problem look like a share-only regression.

## Canonical invariant

`resolved question text -> one server-side spread planner -> immutable reading receipt -> draw -> interpretation -> share`

Downstream layers must never re-plan or reduce the spread.

- question source is metadata, not spread authority;
- typed text and resolved Threads text use the same planner contract;
- automatic frontend requests send `spread=auto` unchanged;
- manual draw may ask the server for a plan before the user selects cards, only to learn the canonical card count;
- after draw, `method_result.spread`, `spread_plan`, and `cards[N]` are authoritative;
- share rendering must preserve N cards from canonical reading state;
- a legacy first-card projection (`currentDrawnCard`) cannot overwrite an N-card reading.

## Capability floor

The canonical Tarot registry must include at least:

- single
- clarifier
- three_card
- situation_advice
- decision
- relationship
- career
- path
- celtic_cross

A refactor that silently shrinks this registry is a capability regression even if basic Tarot drawing still works.

## Share monotonicity

The renderer has explicit 1-card, 2–3-card, 4–6-card, and 7–10-card layout regimes. The semantic rule is independent of layout:

`reading cards[N] -> share cards[N]`

No question source, restore path, social target, or rendering fallback may change N.

## Evidence hierarchy

1. focused planner/layout contract tests;
2. repository-wide CI and browser regression checks;
3. deployed source/artifact parity;
4. real-device acceptance using at least one 1-card, 5-card, and 10-card reading.

Do not claim production acceptance from source CI alone.
