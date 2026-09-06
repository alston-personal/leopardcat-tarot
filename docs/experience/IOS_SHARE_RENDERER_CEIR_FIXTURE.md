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
