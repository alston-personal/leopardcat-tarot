# Threads OAuth + Text Attachment Capability

Status: implementation candidate for Issue #65.

## Canonical capability chain

`explicit user OAuth -> server-only ephemeral token -> account identity -> bounded primary post (<=500) -> official text_attachment -> explicit publish action`

## Security invariants

- Threads App Secret and user access tokens never enter browser JavaScript.
- OAuth state is random, single-use, expires after ten minutes, and is bound to the HttpOnly browser session cookie.
- Tokens are held only in process memory; restart disconnects the account instead of persisting credentials.
- Browser can read only `configured`, `connected`, and public account identity.
- Publishing requires an explicit confirmation naming the target Threads account.
- Questions and Master answers are not added to server persistence by this capability.

## Monotonic share invariant

A long Master interpretation may be upgraded from bounded intent to OAuth `text_attachment`, but it may never regress to an over-limit intent or clipboard/manual-paste workflow.

## Platform contract checked 2026-09-06

Meta Threads API uses OAuth authorization code flow with `threads_basic` + `threads_content_publish`; publishing text supports `text_attachment`, and `auto_publish_text=true` can publish a text container directly. Re-check the official contract before production acceptance because platform APIs can change.

## Remaining production prerequisites

- Configure `THREADS_APP_ID`, `THREADS_APP_SECRET`, and exact `THREADS_REDIRECT_URI` on Oracle.
- Register that redirect URI in the Meta App Threads use case.
- Perform a real-account OAuth + iPhone publish acceptance before closing #65.
