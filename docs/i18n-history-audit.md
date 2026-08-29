# i18n Full-History Audit

Generated from `git rev-list --all -- website`; this inspects all fetched branches, tags and website history rather than only current `main`.

Locale detection only counts dictionary-valued BCP-47-like keys whose language root is in the audit's language-root registry. Ordinary JSON sections such as `nav`, `hero` or `meta` are not languages.

- Website commits scanned: **144**
- Locale-bearing snapshots found: **366**
- Snapshots with more than two locale keys: **0**
- Snapshots containing language roots beyond `zh`/`en`: **0**
- Code snapshots with translation/language markers: **109**

## Locale snapshots beyond zh/en

No canonical Git snapshot inspected here contains a locale dictionary beyond the zh/en language families.

## Dynamic multilingual markers

- `2026-03-19T10:51:48Z` `7d1e718fa069` `website/main.js`: translation/translate API — feat: finalize Major Arcana (16-21) with Master-Grade Composite Overlay and luxury UI polish
- `2026-03-20T00:17:28Z` `a726ae550f00` `website/main.js`: translation/translate API — feat: complete Masterpiece V9 - Artifact-Grade metallic title, mobile support, and scaled support block
- `2026-03-20T01:51:30Z` `38b0eee65b57` `website/main.js`: translation/translate API — fix: mobile card visibility via Safe-Observe pattern and CSS fallbacks
- `2026-03-20T02:21:22Z` `7154b845be05` `website/main.js`: translation/translate API — fix: add mobile visual debugger and hardened element visibility
- `2026-03-20T04:52:01Z` `60c837c35cf5` `website/main.js`: translation/translate API — chore: final production cleanup and V10 masterpiece launch
- `2026-03-20T04:56:22Z` `ef0a12684c90` `website/main.js`: translation/translate API — fix: restore missing revealObserver global and rebuild dist
- `2026-03-20T08:43:30Z` `d0c18ca9f1d3` `website/main.js`: translation/translate API — chore: milestone - all major arcana defined and rendered; saving state before refining card overlay aesthetics
- `2026-03-20T09:21:47Z` `c1c5f945eb8e` `website/main.js`: translation/translate API — chore: implement logic/data separation and architecture refinement
- `2026-03-21T23:26:33Z` `323ba27a4037` `website/main.js`: translation/translate API — feat(website): inject AI Fortune Teller UI with Chat Quota mechanics
- `2026-03-22T00:49:04Z` `bd576a640787` `website/main.js`: translation/translate API — feat(website): add nav link and CTA button referencing fortune teller
- `2026-03-22T00:53:29Z` `61def0d65130` `website/main.js`: translation/translate API — fix(website): implement multi-language support (i18n) for fortune teller UI
- `2026-03-22T01:01:39Z` `a73d1a526a0d` `website/main.js`: translation/translate API — feat(api): create python backend for real LLM tarot readings
- `2026-03-23T22:00:03Z` `f5dd51353107` `website/main.js`: translation/translate API — fix: standardize court card numbering and resolve Knight of Wands style drift
- `2026-05-21T06:08:17Z` `7d6aab329181` `website/fortune_server.py`: extra locale-family codes — clean: remove obsolete png renders and point card definitions to webp
- `2026-08-14T08:46:30+08:00` `241dae3d6333` `website/fortune_server.py`: extra locale-family codes — chore(leopardcat-tarot): update project progress and sync state
- `2026-08-25T07:30:22Z` `f7d12ecf3459` `website/fortune_server.py`: extra locale-family codes — feat(divination): connect web UI to modular reading API
- `2026-08-25T07:57:31Z` `62d1218659ab` `website/fortune_server.py`: extra locale-family codes — feat(platform): integrate private sessions and creator pages
- `2026-08-25T08:43:41Z` `768f44d36b8f` `website/fortune_server.py`: extra locale-family codes — feat(platform): themes and zero-cost AI gateway
- `2026-08-25T08:59:57Z` `094b5f534a05` `website/fortune_server.py`: extra locale-family codes — fix(ui): remember published decks and scroll long meanings
- `2026-08-25T09:05:41Z` `448cf8b9db40` `website/fortune_server.py`: extra locale-family codes — feat(deck): allow custom share URLs
- `2026-08-25T09:23:55Z` `73d87c319899` `website/fortune_server.py`: extra locale-family codes — fix(ui): give card meanings wheel priority
- `2026-08-25T09:33:10Z` `b99abcac5e1b` `website/fortune_server.py`: extra locale-family codes — fix(ui): release page scroll at card meaning boundaries
- `2026-08-25T09:40:51Z` `d8bd19b186e1` `website/fortune_server.py`: extra locale-family codes — feat(ui): show custom deck card gallery
- `2026-08-25T10:51:47Z` `5b6971972717` `website/fortune_server.py`: extra locale-family codes — refactor(ui): share tarot experience across decks
- `2026-08-25T11:19:39Z` `d05e612aecdc` `website/fortune_server.py`: extra locale-family codes — fix(ui): prevent custom deck bootstrap race
- `2026-08-25T12:17:36Z` `7e9cb4536797` `website/fortune_server.py`: extra locale-family codes — feat(brand): route UI sharing and OG through brand packs
- `2026-08-25T13:13:51Z` `cfaa621de437` `website/fortune_server.py`: extra locale-family codes — feat(persona): route readings through persona packs
- `2026-08-25T14:17:16Z` `2f74695acb74` `website/fortune_server.py`: extra locale-family codes — feat(persona): wire structured persona creator runtime
- `2026-08-25T15:11:01+08:00` `70a67b1651e0` `website/fortune_server.py`: extra locale-family codes — feat(divination): add modular method and persona engine
- `2026-08-25T15:11:13+08:00` `a570a9a1a871` `website/fortune_server.py`: extra locale-family codes — feat(divination): add tarot method with reversals and spreads
- `2026-08-25T15:11:27+08:00` `319b8f79bc00` `website/fortune_server.py`: extra locale-family codes — feat(divination): add swappable oracle persona packs
- `2026-08-25T15:11:33+08:00` `ca60238eb5fa` `website/fortune_server.py`: extra locale-family codes — feat(divination): expose default modular engine
- `2026-08-25T15:11:46+08:00` `08f659cd3c24` `website/fortune_server.py`: extra locale-family codes — feat(divination): add provider-neutral v1 reading API
- `2026-08-25T15:12:44+08:00` `147374218ff9` `website/fortune_server.py`: extra locale-family codes — refactor(divination): load persona behavior from oracle packs
- `2026-08-25T15:12:55+08:00` `9f4f05bfa88e` `website/fortune_server.py`: extra locale-family codes — feat(divination): extract LeopardCat master into oracle pack
- `2026-08-25T15:13:04+08:00` `c7b01ba7a991` `website/fortune_server.py`: extra locale-family codes — refactor(divination): load LeopardCat as data pack
- `2026-08-25T15:34:14+08:00` `38889cb6749e` `website/fortune_server.py`: extra locale-family codes — feat: modular divination master core
- `2026-08-25T15:46:08+08:00` `d993227f744f` `website/fortune_server.py`: extra locale-family codes — feat(decks): add flexible custom deck registry
- `2026-08-25T15:46:19+08:00` `12d8c7532ce2` `website/fortune_server.py`: extra locale-family codes — feat(privacy): add ephemeral reading session store
- `2026-08-25T15:46:32+08:00` `9a1a10d884c5` `website/fortune_server.py`: extra locale-family codes — refactor(tarot): support arbitrary deck sizes
- `2026-08-25T15:46:44+08:00` `3ac00b869599` `website/fortune_server.py`: extra locale-family codes — refactor(divination): wire deck registry into engine
- `2026-08-25T15:47:09+08:00` `b64eec9386c0` `website/fortune_server.py`: extra locale-family codes — feat(decks): add nontechnical deck publishing service
- `2026-08-25T15:47:31+08:00` `ffb0eec0ed51` `website/fortune_server.py`: extra locale-family codes — feat(creator): add simple custom deck publishing wizard
- `2026-08-25T15:47:48+08:00` `4fef5bce42dc` `website/fortune_server.py`: extra locale-family codes — feat(creator): add zero-code deck upload flow
- `2026-08-25T15:55:34+08:00` `00c510a5996e` `website/fortune_server.py`: extra locale-family codes — feat(creator): auto-optimize uploaded card images
- `2026-08-25T15:55:55+08:00` `3eb3c1d7e82d` `website/fortune_server.py`: extra locale-family codes — security(decks): normalize creator text input
- `2026-08-25T16:00:04+08:00` `e8114ca90168` `website/fortune_server.py`: extra locale-family codes — security(decks): add coarse publishing quotas
- `2026-08-25T16:01:16+08:00` `322cc5ed19a7` `website/fortune_server.py`: extra locale-family codes — feat: privacy-safe sessions and zero-code custom decks
- `2026-08-25T16:13:18+08:00` `cb8ecf0691d0` `website/fortune_server.py`: extra locale-family codes — fix(creator): handle non-JSON upload errors clearly
- `2026-08-25T16:46:56+08:00` `32a9be52150c` `website/fortune_server.py`: extra locale-family codes — feat: modular themes and zero-cost AI policy
- `2026-08-25T17:06:20+08:00` `1e50efc0a12c` `website/fortune_server.py`: extra locale-family codes — feat: custom deck share URLs
- `2026-08-25T17:42:30+08:00` `009199c68af5` `website/fortune_server.py`: extra locale-family codes — feat(api): expose public deck cards for gallery
- `2026-08-25T19:06:27+08:00` `48cd9bcb2c31` `website/fortune_server.py`: extra locale-family codes — refactor: unify shared Tarot experience across decks
- `2026-08-25T19:20:27+08:00` `ff3ef92c5ce4` `website/fortune_server.py`: extra locale-family codes — fix: make deck bootstrap mutually exclusive
- `2026-08-25T20:13:25+08:00` `6312d8f3734c` `website/fortune_server.py`: extra locale-family codes — feat(brand): add brand pack registry
- `2026-08-25T20:13:52+08:00` `85bb3dacab55` `website/fortune_server.py`: extra locale-family codes — test(brand): cover built-in and custom brand packs
- `2026-08-25T21:11:05+08:00` `be126ad7f6e2` `website/fortune_server.py`: extra locale-family codes — feat(persona): declare deck default persona
- `2026-08-25T21:11:23+08:00` `da3ef5c1ee28` `website/fortune_server.py`: extra locale-family codes — feat(persona): expose persona pack metadata
- `2026-08-25T21:12:32+08:00` `59a81d241731` `website/fortune_server.py`: extra locale-family codes — test(persona): cover deck persona defaults
- `2026-08-25T21:15:35+08:00` `8591556e9f15` `website/fortune_server.py`: extra locale-family codes — feat: modular persona packs and data-driven defaults
- `2026-08-25T21:55:49+08:00` `8acf4cab5da1` `website/fortune_server.py`: extra locale-family codes — feat(creator): add default persona choice
- `2026-08-25T21:56:28+08:00` `a20b2e90e14d` `website/fortune_server.py`: extra locale-family codes — feat(creator): publish selected default persona
- `2026-08-25T22:00:33+08:00` `19b021640446` `website/fortune_server.py`: extra locale-family codes — fix(persona): localize public display metadata
- `2026-08-25T22:00:47+08:00` `338f47165017` `website/fortune_server.py`: extra locale-family codes — fix(persona): add Traditional Chinese public role
- `2026-08-25T22:10:50+08:00` `febfc8fee061` `website/fortune_server.py`: extra locale-family codes — feat(persona): add structured persona publisher
- `2026-08-25T22:11:14+08:00` `83838cb533fb` `website/fortune_server.py`: extra locale-family codes — feat(persona): expose source and harden custom prompt boundary
- `2026-08-25T22:11:24+08:00` `b6aa2c1a187d` `website/fortune_server.py`: extra locale-family codes — feat(persona): load persisted custom persona packs
- `2026-08-25T22:20:54+08:00` `5510813e093f` `website/fortune_server.py`: extra locale-family codes — test(persona): add permanent Persona Creator contracts
- `2026-08-25T22:25:10+08:00` `83d0c97f46c5` `website/fortune_server.py`: extra locale-family codes — feat: structured custom Persona creator
- `2026-08-25T22:30:51+08:00` `2e34dd735b21` `website/fortune_server.py`: extra locale-family codes — feat(ownership): add hashed creator management tokens
- `2026-08-25T22:31:27+08:00` `b3393a9d89da` `website/fortune_server.py`: extra locale-family codes — feat(ownership): issue and enforce deck management tokens
- `2026-08-25T22:33:51+08:00` `96f31c0713c2` `website/fortune_server.py`: extra locale-family codes — feat(ownership): support managed Persona replacement and removal
- `2026-08-25T22:34:22+08:00` `5d770b7a2626` `website/fortune_server.py`: extra locale-family codes — feat(ownership): issue and manage Persona ownership tokens
- `2026-08-26T06:29:24Z` `e19d3ab3837f` `website/fortune_server.py`: extra locale-family codes — feat(v1): wire server capsule ownership and focused reading UX
- `2026-08-26T07:59:15Z` `02bec3fb6802` `website/fortune_server.py`: extra locale-family codes — fix(ux): keep primary tarot reading on deck page
- `2026-08-26T14:16:20+08:00` `dabf2ab4b38f` `website/fortune_server.py`: extra locale-family codes — feat(v1): add portable Reading Capsule contract
- `2026-08-26T14:17:02+08:00` `25829154a1e2` `website/fortune_server.py`: extra locale-family codes — feat(v1): add deterministic Lenormand method and grammar
- `2026-08-26T14:17:22+08:00` `5233532f60db` `website/fortune_server.py`: extra locale-family codes — feat(v1): register Lenormand as a real method
- `2026-08-26T14:17:44+08:00` `0933470b285f` `website/fortune_server.py`: extra locale-family codes — feat(v1): make generic interpreter method-neutral
- `2026-08-26T14:18:03+08:00` `063bf84dfd09` `website/fortune_server.py`: extra locale-family codes — test(v1): lock Reading Capsule portability contract
- `2026-08-26T14:18:15+08:00` `660c672cb122` `website/fortune_server.py`: extra locale-family codes — test(v1): lock Lenormand spread and grammar contracts
- `2026-08-26T14:18:32+08:00` `31b5ca4cff9d` `website/fortune_server.py`: extra locale-family codes — test(v1): lock creator ownership token contracts
- `2026-08-26T14:19:28+08:00` `625b36bb6ceb` `website/fortune_server.py`: extra locale-family codes — feat(ui): add progressive-disclosure reading experience
- `2026-08-26T14:19:56+08:00` `489e39a98f3e` `website/fortune_server.py`: extra locale-family codes — feat(ui): style focused mobile-first reading flow
- `2026-08-26T14:20:31+08:00` `aec0c57704d8` `website/fortune_server.py`: extra locale-family codes — feat(ui): wire Tarot Lenormand and external AI handoff
- `2026-08-26T14:20:50+08:00` `9fef21de9b91` `website/fortune_server.py`: extra locale-family codes — feat(ui): add zero-login cross-device management page
- `2026-08-26T14:21:11+08:00` `27917b10934c` `website/fortune_server.py`: extra locale-family codes — feat(ui): wire management token edit rotate delete flow
- `2026-08-26T14:21:52+08:00` `1702573722f4` `website/fortune_server.py`: extra locale-family codes — fix(v1): enforce persona method capabilities
- `2026-08-26T14:28:19+08:00` `8b67ddbc713b` `website/fortune_server.py`: extra locale-family codes — fix(v1): preserve generic persona public name contract
- `2026-08-26T14:28:36+08:00` `10311185d6c2` `website/fortune_server.py`: extra locale-family codes — test(v1): align management textarea contract
- `2026-08-26T14:34:59+08:00` `1175cb33efd4` `website/fortune_server.py`: extra locale-family codes — fix(ui): preserve deck default Persona in focused reading
- `2026-08-26T14:35:48+08:00` `7e7f5cca24ff` `website/fortune_server.py`: extra locale-family codes — fix(ui): correct focused reading HTML escaping
- `2026-08-26T15:15:24+08:00` `0ad8dc7e171d` `website/fortune_server.py`: extra locale-family codes — fix(ai): fail closed on empty or malformed Gemini responses
- `2026-08-26T15:15:40+08:00` `e73720d57978` `website/fortune_server.py`: extra locale-family codes — test(ai): lock malformed provider response fail-closed contract
- `2026-08-26T15:42:25+08:00` `52249e4a89c4` `website/fortune_server.py`: extra locale-family codes — fix(reading): keep master follow-up inside branded experience
- `2026-08-26T15:43:12+08:00` `d7e2bee27342` `website/fortune_server.py`: extra locale-family codes — fix(reading): preserve brand theme and in-site follow-up
- `2026-08-26T15:43:42+08:00` `f9f64c1f00d9` `website/fortune_server.py`: extra locale-family codes — style(reading): inherit deck theme across focused mode
- `2026-08-26T15:44:01+08:00` `3dd1566eea50` `website/fortune_server.py`: extra locale-family codes — fix(persona): restore leopardcat master voice without forcing ecology
- `2026-08-26T15:44:47+08:00` `e458bf751436` `website/fortune_server.py`: extra locale-family codes — test(reading): lock branded in-site master experience
- `2026-08-26T15:56:36Z` `668502f0e6da` `website/fortune_server.py`: extra locale-family codes — fix(ux): enforce one reading request flow
- `2026-08-26T16:01:06+08:00` `02a024b4632f` `website/fortune_server.py`: extra locale-family codes — test(ux): lock primary tarot entry to in-page fortune
- `2026-08-27T00:02:55+08:00` `f586b5c4f010` `website/fortune_server.py`: extra locale-family codes — fix(ux): guard against duplicate reading flows
- `2026-08-27T00:03:48+08:00` `b9a6838940ee` `website/fortune_server.py`: extra locale-family codes — fix(ux): load single reading flow guard
- `2026-08-27T00:05:31+08:00` `21638f24ce23` `website/fortune_server.py`: extra locale-family codes — chore: keep only permanent single reading flow fix
- `2026-08-27T00:07:57+08:00` `678a8211f551` `website/fortune_server.py`: extra locale-family codes — fix(ux): enforce one master reading request flow
- `2026-08-27T00:10:32+08:00` `45f0198002e7` `website/fortune_server.py`: extra locale-family codes — test: lock single master reading flow contract
- `2026-08-27T00:11:19+08:00` `f44db405678c` `website/fortune_server.py`: extra locale-family codes — fix: enforce a single in-page master reading flow
- `2026-08-29T00:27:19Z` `5dd701db0d10` `website/fortune_server.py`: extra locale-family codes — fix(i18n): restore data-driven multilingual UI runtime
- `2026-08-29T00:27:19Z` `5dd701db0d10` `website/main.js`: navigator.language — fix(i18n): restore data-driven multilingual UI runtime

## Interpretation guardrail

A commit message containing 'multilingual' or a generic word such as 'translate' is not by itself evidence of UI locale support. UI locale evidence requires an actual locale dictionary or explicit runtime translation implementation. AI response-language support is tracked separately under `ai.multilingual`.

If the user-visible service previously supported additional UI languages but no canonical Git snapshot contains them, the missing source may have been runtime-generated, deployed outside this repository, stored in another repository, or lost before commit. Keep `ui.multilingual` marked `regression-open` until that source is identified or an explicitly approved replacement restores equivalent capability.
