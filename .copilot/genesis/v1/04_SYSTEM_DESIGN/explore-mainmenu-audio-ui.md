# Explore: Main Menu Error + BGM Reliability + Flow Map Branch Styling

## Phase 1 - Hypothesis and Bounds
- H1: Main menu error originates from `Image.load_from_file` usage on imported resource path.
- H2: No-BGM symptom can persist when manager path silently fails or bus starts effectively muted.
- H3: Flow-map readability/aesthetics can improve by replacing sterile spline lines with branch-like connectors.

Bounds:
- Do not alter chapter graph data model.
- Keep save/load behavior intact.
- Apply minimal invasive UI rendering changes.

## Phase 2 - Lightweight Option Comparison
1. Background loading:
- Option A: keep `Image.load_from_file` and sanitize image file.
- Option B (selected): resource-style `load(Texture2D)` with fallback candidates.

2. BGM startup:
- Option A: manager-only playback.
- Option B (selected): manager-first + local player fallback + generator tone fallback.

3. Flow-map connectors:
- Option A: arrowed Bezier polylines.
- Option B (selected): branch-trunk plus twig sub-branches and endpoint buds.

## Phase 3 - Decision
- Continue with selected options (B/B/B).
- Keep branch-style as current default and iterate color/material polish in next pass.

## Risks
- Audio generator fallback requires continuous frame feeding; mitigated by `_process` refill.
- Branch lines may feel too decorative for dense maps; mitigate via line width/color tuning toggle in next iteration.

## Next Action
- Add a user toggle for connector style (`branch` vs `classic`) in flow-map toolbar.
