# CEIR Teacher Fixture — iOS share renderer timeout

## Hypothesis that failed
Mobile Safari was assumed to be merely slower than desktop, so the square render budget was raised from 20s to 60s.

## Falsifying production evidence
A real iPhone produced `[RENDER_ERR] TIMEOUT:square:60000`, proving the DOM raster itself can stall beyond the enlarged budget.

## Architectural correction
For iOS native sharing, square PNG generation is now derived directly from canonical `shareContext/shareEntries` through Canvas2D. `html2canvas` is no longer authoritative for the iOS native-share asset. OG generation/persistence is best-effort and cannot block native share.

## Protected invariants
- N-card reading remains N cards in the image.
- Orientation is rendered from canonical entry orientation.
- A lossy `currentDrawnCard` projection cannot re-author spread share state.
- Increasing timeout again is a superseded path unless new evidence establishes a different bounded wait.
- Preview/OG failure cannot deny native-share capability.

## Code Evolution IR mapping
- hypothesis: Mobile Safari render is healthy but slow
- observation: 60s square timeout on real iPhone
- result: hypothesis falsified
- failed_path: increase DOM-raster timeout
- decision: deterministic Canvas2D renderer from canonical reading state
- forbidden_transition: canonical spread state -> DOM/current-card lossy projection -> authoritative native share


## Follow-up: runtime classification and restore projection

Real-device reproduction after the first Canvas2D change exposed two additional causal edges:

- platform routing itself is an authority decision: a UA-only classifier can incorrectly route an iOS WebView/PWA back to the superseded DOM-raster path;
- restoring an N-card reading and then invoking a single-card social writer is another forbidden lossy transition, even if the initial draw path is monotonic.

New invariants:

1. runtime classification for safety-critical renderer selection must use multiple platform/capability signals, not a single UA token;
2. `reading_state(cards.length > 1) -> currentDrawnCard -> social/share authority` is forbidden in restore paths as well as fresh-reading paths;
3. a fix is not accepted until the actual production artifact identity is proven and real-device evidence passes.
