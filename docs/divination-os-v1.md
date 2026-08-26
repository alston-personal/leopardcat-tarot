# Divination OS v1 — Product / UX / Test Contract

## Goal
Build a platform where a method, deck, theme, brand and persona are replaceable modules, while the public experience stays simple enough that a first-time visitor can ask a question and draw within seconds.

## Product principles
1. **Strong OS, simple app.** Runtime complexity is hidden from ordinary visitors.
2. **Progressive disclosure.** Question → method/spread → draw → result → interpretation/handoff. Advanced choices stay optional.
3. **Method fidelity.** Tarot, Lenormand and future methods own their rules; UI never fakes a method by generic random sampling.
4. **Portable reading.** Every draw yields a canonical Reading Capsule that can be interpreted by platform AI or external AI without changing the symbolic result.
5. **Zero-cost fail closed.** No paid provider/model fallback. When platform AI is unavailable, external handoff remains usable.
6. **Creator ownership.** New user-published resources get a one-time bearer management token; only its hash is persisted. Token stays in URL fragment, never query string.
7. **Privacy by default.** Questions/answers are not persisted; symbolic session state expires.

## Public UX redesign
### Entry
- Brand header: active deck/experience name.
- One dominant question field.
- Method switcher: Tarot / Lenormand.
- Spread choices are visual chips with card counts.
- One primary CTA: `抽牌`.
- No engine, RNG, provider, persona IDs, JSON, quota internals in the primary flow.

### Result
- Cards/symbols are the visual focus.
- Structural labels remain visible (position, orientation, Lenormand center/adjacency).
- Interpretation appears below the immutable symbolic result.
- Actions:
  - `立即 AI 解讀` (platform, when available)
  - `用自己的 AI` → ChatGPT / Claude / Gemini / Copy Prompt
  - `分享` / `重新抽牌`
- If platform AI quota/upstream fails, keep the draw on screen and promote External AI handoff instead of losing the result.

### Creator
- Existing zero-code deck/theme/persona flow remains.
- After publish, show both public URL and a separate **management link**.
- Explain that the management link is the cross-device recovery key and is shown once.

### Manage
`/manage.html?deck=<id>#token=<secret>` or persona equivalent.
- Fragment token is read by browser and sent only via `X-Management-Token`.
- View/edit metadata.
- Rotate key.
- Delete resource with explicit confirmation.

## Runtime contracts
### Reading Capsule
`schema = divination-reading/1`
- reading_id
- method
- persona
- question
- lang
- immutable method result
- platform integrity/safety contract

### Tarot v1
- single
- three_card
- decision
- deck module + reversal semantics

### Lenormand v1
- canonical Petit Lenormand 36 order
- yes_no (1)
- three (3)
- five (5)
- box9 (9)
- no reversals
- combination priority
- adjacency grammar
- polarity/tendency for yes/no
- center/rows/columns/diagonals for box9

## Acceptance tests
### Unit
- Tarot regression.
- Lenormand 36 unique cards, deterministic spread sizes, without replacement, structural grammar.
- Reading Capsule provider neutrality and no redraw contract.
- Ownership token hash-only storage, authorization, rotation, update and delete.

### API
- `/api/v1/methods`
- reading response contains capsule + external handoff.
- platform AI failure returns the same draw + handoff.
- management APIs reject absent/wrong tokens.
- legacy unmanaged resource cannot be silently claimed.

### Browser E2E
1. Tarot: question → draw → result → external prompt preserves deck/orientation.
2. Lenormand: select box9 → exactly 9 unique cards → center/structure visible → external prompt contains lenormand grammar.
3. AI failure simulation: cards remain visible and external AI controls remain enabled.
4. Creator: publish payload returns management token; management link uses fragment, not query.
5. Manage: correct token loads resource; edit works; rotation invalidates old token; delete requires confirmation.
6. Mobile viewport: first CTA and question visible without horizontal scrolling; cards responsive.

## v1 done definition
A production deployment is accepted only when Python tests, JS syntax, Vite build, Oracle API smoke and Chromium E2E are all green on the same target commit.
