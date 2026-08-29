# Capability Migration Records

Protected capabilities are monotonic by default. A protected capability or contract clause may only be deprecated or removed with an explicit JSON migration record in this directory.

Required fields:

```json
{
  "capability": "example.capability",
  "change_type": "deprecate",
  "rationale": "Why preserving the old capability is no longer correct or possible.",
  "replacement": "The compatible replacement or migration path for users.",
  "user_impact": "What existing users lose or must change.",
  "approval_reference": "A real issue/PR/decision reference approving the intentional regression."
}
```

`change_type` must be `deprecate` or `remove`.

Do not create placeholder approvals. If there is no real approval reference, the capability must remain protected.
