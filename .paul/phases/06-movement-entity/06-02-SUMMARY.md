---
phase: 06-movement-entity
plan: 02
subsystem: ui
tags: [velocity, movement, entity-graph, streamlit, selector-view, column_config]

requires:
  - phase: 06-01
    provides: modules/velocity.py — compute_velocity, ANOMALY_THRESHOLD_KMH, VELOCITY_COLUMNS
  - phase: 03-selector-tracking
    provides: render_selector_view() — coloc variable, filtered DataFrame

provides:
  - render_selector_view(): "Movement Analysis" expander — velocity table with ProgressColumn, threshold slider, anomaly count
  - render_selector_view(): "Entity Co-occurrence" expander — coloc sorted by coloc_count

affects: []

tech-stack:
  added: []
  patterns:
    - "st.column_config.ProgressColumn for speed_kmh — no matplotlib required"
    - "coloc reused from existing scope — no re-computation"
    - "Movement Analysis auto-computes on expander open — no button needed"

key-files:
  created: []
  modified: [app.py]

key-decisions:
  - "ProgressColumn over background_gradient — matplotlib not installed in WRAITH env; Streamlit native column_config is zero-dep"
  - "max_value = max(actual_max_speed, threshold) — prevents progress bar overflow when speed exceeds threshold"
  - "Entity Co-occurrence reuses coloc variable — already computed above insertion point, no redundant work"

patterns-established:
  - "Final Selector view panel order: Co-location → Shodan → OSM → Telegram → Movement → Entity → Raw observations"

duration: ~15min
started: 2026-04-06T00:00:00Z
completed: 2026-04-06T00:00:00Z
---

# Phase 6 Plan 02: Movement + Entity UI Wiring — Summary

**Movement Analysis and Entity Co-occurrence panels complete the Selector view — velocity table with ProgressColumn speed bars, configurable anomaly threshold, and co-occurrence ranking.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Completed | 2026-04-06 |
| Tasks | 2 of 2 complete (1 auto + 1 checkpoint) |
| Files modified | 1 (app.py) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Movement Analysis Panel Present | Pass | Velocity table with ProgressColumn + threshold slider |
| AC-2: Anomaly Count Summary | Pass | Caption updates with slider value |
| AC-3: Entity Co-occurrence Panel | Pass | Sorted by coloc_count, caption explains edge weight |
| AC-4: No Crash on Single Observation | Pass | speed_kmh=0 renders correctly as empty progress bar |
| AC-5: App Loads Clean | Pass | py_compile exit 0 |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `app.py` | Modified | Movement Analysis + Entity Co-occurrence expanders in render_selector_view() |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| ProgressColumn over background_gradient | matplotlib not installed; Streamlit native, zero-dep | Speed bars render in all environments without extra install |
| max_value = max(actual_max, threshold) | Prevents progress bar clamping when speed > threshold | Bar always shows meaningful proportion |

## Deviations from Plan

**1. background_gradient replaced with ProgressColumn**
- **Found during:** Checkpoint verification
- **Issue:** `pandas Styler.background_gradient` requires matplotlib, which is not installed in the WRAITH environment
- **Fix:** Replaced with `st.column_config.ProgressColumn` — Streamlit native, no external dependency
- **Impact:** Visual styling differs (progress bar vs color gradient) but functionally equivalent — speed magnitude is clear

## Next Phase Readiness

Phase 6 is the final phase of milestone v0.1 WiGLE Core. All planned features are complete. Ready for milestone closure.

**Blockers:**
- None

---
*Phase: 06-movement-entity, Plan: 02*
*Completed: 2026-04-06*
