# iOS Share Runtime v2 Acceptance

This repair is accepted only when all of the following are true:

1. iPhone Safari, installed PWA, iPadOS desktop-mode Safari, and embedded iOS WebView/WKWebView-like runtimes route native-share square rendering to the deterministic Canvas2D renderer rather than DOM rasterization.
2. Runtime selection is not based on a single `iPhone/iPad/iPod` user-agent token.
3. A restored multi-card reading never invokes the legacy single-card social writer as an authoritative state transition.
4. Three-card reading identity, order, and orientation remain canonical through share generation.
5. No timeout-budget increase is accepted as a substitute for renderer/runtime correctness.
6. Product CI must pass the focused runtime/restore monotonicity tests plus existing share monotonicity and timeout regression tests.
7. Production is not considered fixed until exact deployed SHA/artifact parity is proven and a real iPhone three-card + full-Master native-share smoke passes.
