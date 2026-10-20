# LeopardCat production backend deployment — durable capability record

Status: **RECOVERY REQUIRED**. This is an operational runbook, not an executable deploy path. Never report a merge as a deployment.

## Previously proven capability (historical source)

- Core repository: `alston-personal/agentmanager`
- Carrier branch: `ops/leopardcat-runtime-inspect`
- Workflow: `.github/workflows/ops-leopardcat-runtime-deploy.yml`
- Production runtime path: `/home/<runtime-user>/leopardcat-tarot/website`
- Python service: `fortune_server.py`, port `8088`
- Historical process: pinned SHA fast-forward; dirty-tree allowlist; compile Python; Vite build; preserve runtime statistics; identify port owner and cwd; restart only proven process; check local and public endpoints; rollback on failure
- **Do not run the historical workflow unchanged**: it pins obsolete `EXPECTED_OLD_SHA` and `TARGET_SHA` and depends on an old runner/credential boundary.

## What the current product must provide

1. Resolve a governed production deployment capability through Core/ONE. Check the historical workflow above **before** declaring the capability unavailable.
2. Fetch the actual live runtime HEAD, service PID, process cwd, branch, dirty files and ownership (read-only).
3. Compare with intended immutable `main` SHA; refuse dirty or divergent state except explicit allowlisted runtime data.
4. Submit a typed, bounded deployment request for the exact SHA; no arbitrary SSH or shell payloads and no secret copies into the product repository.
5. Preserve `website/data/`, published decks, personas and uploaded artifacts. Build/compile, transactional update and targeted backend restart with rollback.
6. Persist deployment receipt: project, environment, source repository/ref/SHA, artifact, service identity, old/new HEAD, rollback point, local/public checks.
7. Confirm **both** `http://127.0.0.1:8088/api/v1/personas?deck=leopardcat` and `https://leopardcat-tarot.milkcat.org/api/v1/personas?deck=leopardcat` contain `ocean-current-master`, and perform a single-card read without treating unavailable AI as a successful reading.
8. Close the blocker only after observable production verification, otherwise report the exact missing permission/runner/deploy capability.

## Regression guard / prevent rediscovery

- A green feature CI or merged PR is **not** a deploy receipt.
- If production differs from `main`, search this document, product issue #44, Core issues #165/#288 and historical carrier before proposing new infrastructure.
- An automated release gate must test the deployed backend API and exact runtime SHA, not only front-end page 200 or a local mocked E2E.
- A failed release should produce a durable actionable blocker in the existing issue and resume automatically when a permitted executor becomes available.
- Maintain this file as part of any future migration, and keep one product owner lane (#44) rather than spawning duplicate deployment features.
