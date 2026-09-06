# Threads long-share capability evidence

## Failure signature

A full Master interpretation longer than the Threads primary-post limit was copied wholesale into the composer. Real-device evidence showed a negative character counter (`-604`), forcing the user to manually cut/paste content. The share heading also omitted the source author even though the canonical Threads URL contained an `@handle`.

## Falsified assumptions

1. Threads intent would automatically split long text into a thread. False.
2. Source author could be omitted when upstream reader metadata was incomplete. False: the canonical URL itself preserves an authority-preserving `@handle` fallback.

## Canonical rules

- Every Threads intent primary post MUST be <= 500 characters.
- Full text MUST NOT be copied to clipboard as a hidden manual-work fallback.
- Long text is represented as a typed `text_attachment` capability; full automatic publishing requires user-authorized Threads OAuth.
- Source author resolution is monotonic: reader display-name/handle > canonical URL handle > generic heading.

## Forbidden transitions

- `full interpretation > 500` -> `intent text > 500`
- `long share` -> `clipboard full text` -> `user manually edits/pastes`
- `canonical source URL with @handle` -> `anonymous source heading`

## Acceptance

- No composer opens with a negative character budget.
- `@handle` is preserved when available from the canonical URL.
- OAuth publishing may later attach up to the platform-supported long-text payload without changing this bounded intent contract.
