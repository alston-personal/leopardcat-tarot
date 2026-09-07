# Encrypted Share Snapshot CEIR

Issue: #72

## Problem

A symbolic shared reading correctly preserved immutable cards while refusing to persist the original private question and Master answer. The recipient therefore landed on a technically correct restore state but lost the human meaning of the share.

## Capability

`private reading -> explicit disclosure mode -> immutable share snapshot -> browser-side AES-GCM -> URL fragment -> recipient decrypt/render`

The existing `reading` + `share` query parameters remain the symbolic fallback and social/OG card-preview identity. Private selected content is layered only in the fragment, which is not sent in normal HTTP requests.

## Disclosure modes

- cards only
- cards + editable public question
- cards + Master highlight (recommended default)
- full reading

Question inclusion remains explicit. The public question is editable before disclosure so a user can anonymize names/details.

## Privacy invariants

1. Creating a reading does not persist question/answer.
2. Sharing cards-only does not introduce encrypted private content.
3. Selected private text is encrypted in the browser with a fresh AES-GCM key.
4. No plaintext question/answer is added to query params, backend logs, receipts, or persistent server storage by v1.
5. The decryption material lives only in the URL fragment.
6. Social preview crawlers can still use the symbolic share URL without receiving the fragment key.
7. Snapshot content freezes spread/card ids/orientations/positions and is never re-planned downstream.
8. Expired or corrupted fragments fail closed; symbolic share fallback remains usable while its own receipt exists.

## Evidence hierarchy

`static contract tests < built bundle injection < browser cross-device share < real mobile/social acceptance`

## Known limitation / next capability

Fragment-only encrypted snapshots are zero-server-storage and therefore cannot truly revoke a link already copied by a recipient. True owner revocation requires a later server-held-ciphertext design with a separate owner revocation capability while keeping decryption material out of server custody. Do not claim remote revocation until that design is implemented and accepted.
