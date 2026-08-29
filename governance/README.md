# Capability Preservation Governance

LeopardCat Tarot follows an **additive-by-default** change policy.

## Non-regression rule

A change that adds, refactors, modularizes, optimizes or fixes one feature MUST NOT silently remove, narrow, reset or replace an existing user-visible capability.

Examples of prohibited changes:

- replacing a data-driven multilingual UI with a hard-coded `zh/en` whitelist;
- replacing a shared deck flow with a LeopardCat-only implementation;
- adding a new reading path that bypasses privacy, immutable-result, theme, persona or sharing contracts;
- changing an AI provider in a way that silently enables paid fallback;
- rebuilding a component from scratch and dropping behavior that existed before the rewrite.

## Required change procedure

For every non-trivial product change:

1. **Read the capability ledger first** (`governance/capabilities.json`).
2. Classify the change as `add`, `extend`, `refactor`, `deprecate`, or `remove`.
3. For `add`, `extend`, and `refactor`, all protected capabilities are preservation constraints.
4. `deprecate` or `remove` requires an explicit migration record explaining the user-visible loss, replacement path and approval rationale.
5. Run the capability guard in CI before merge.
6. A rewrite is not considered successful merely because the new feature works; existing protected behavior must still pass.

## Compatibility principle

When old and new implementations conflict, prefer **adapter/migration/integration** over replacement. New modules consume existing contracts; they do not redefine those contracts accidentally.

## Multilingual regression

`ui.multilingual` is currently marked `regression-open` because the present website source contains a hard-coded `zh/en` restriction even though multilingual UI existed previously. Restoration must be additive: recover the prior locale capability without reverting the newer modular deck/theme/persona/reading work.

After restoration is verified, change its status to `protected` and record the restored locale registry as a baseline.
