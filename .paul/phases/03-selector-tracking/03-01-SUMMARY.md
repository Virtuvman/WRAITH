---
phase: 03-selector-tracking
plan: 01
subsystem: analytics
tags: [selector, temporal-filter, co-location, plotly, pandas]

requires:
  - phase: 01-wigle-ingestion
    provides: modules/wigle.py — wigle_networks DataFrame schema
  - phase: 02-heatmap-visualization
    provides: st.session_state.wigle_networks — populated by sidebar fetch

provides:
  - modules/selector.py — query_selector, apply_temporal_filter, find_collocated
  - "Selector" view in app.py — field/value query, date range slider, filtered globe, co-location table
  - SELECTOR_FIELDS constant defining queryable fields

affects: [04-cross-source-enrichment, 06-entity-graph]

tech-stack:
  added: []
  patterns:
    - "Selector query: partial case-insensitive str.contains on SELECTOR_FIELDS"
    - "Temporal filter: pd.to_datetime(errors=coerce) + .dt.date range check"
    - "Co-location: Euclidean lat/lon distance, coloc_count aggregation"

key-files:
  created: [modules/selector.py]
  modified: [app.py]

key-decisions:
  - "Euclidean distance for co-location — sufficient for OSINT city-scale proximity, avoids haversine complexity"
  - "Selector view uses natural earth projection (flat) — easier to read movement patterns than orthographic"
  - "coloc_count column added to co-location results — ranks networks by how frequently they appear near selector"

patterns-established:
  - "query_selector + apply_temporal_filter are composable — chain them for filtered results"
  - "All selector functions return empty DataFrame (never raise) on empty/None input"
  - "Selector view is self-contained in render_selector_view() — reads only session state"

duration: ~20min
started: 2026-04-05T00:00:00Z
completed: 2026-04-05T00:00:00Z
---

# Phase 3 Plan 01: Selector Tracking & Temporal Filter — Summary

**Selector-based querying, date range filtering, and co-location detection shipped as a pure data module and interactive Selector view in WRAITH-WiGLE.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~20 min |
| Completed | 2026-04-05 |
| Tasks | 3 of 3 complete |
| Files modified | 2 (1 created, 1 modified) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Selector Module Imports Clean | Pass | py_compile clean; all imports verified |
| AC-2: Selector Query | Pass | Partial case-insensitive match; empty DataFrame on no match |
| AC-3: Temporal Filter | Pass | pd.to_datetime coerce; inclusive date range; empty on out-of-range |
| AC-4: Co-location Detection | Pass | Euclidean proximity; excludes selector netids; coloc_count column |
| AC-5: Selector View in App | Pass | Field/value input, date slider, filtered globe, co-location table, raw obs expander |

## Accomplishments

- `modules/selector.py` created as a pure data module — no UI dependencies, fully testable
- All three selector functions handle empty/None input gracefully (return empty DataFrame, never raise)
- Selector view wired into WRAITH navigation between Heatmap and Data Table
- Co-location table ranked by `coloc_count` — immediately surfaces frequently co-located infrastructure

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `modules/selector.py` | Created | query_selector, apply_temporal_filter, find_collocated, SELECTOR_FIELDS |
| `app.py` | Modified | "Selector" added to view_options; render_selector_view() added and wired |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Euclidean distance for co-location | Sufficient for city-scale OSINT; avoids haversine overhead | Simpler, fast on large DataFrames; acceptable precision for ~1km radius |
| Natural earth projection in Selector view | Movement patterns easier to read on flat map than orthographic | Consistent with flat map view; user can cross-reference |
| coloc_count ranks co-location results | Higher count = stronger association signal | Phase 6 entity graph can use coloc_count as edge weight |

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- `query_selector` + `apply_temporal_filter` are composable — Phase 4 enrichment can filter before cross-referencing Shodan/OSM
- `find_collocated` returns a ranked DataFrame — Phase 6 entity graph can use `coloc_count` as edge weight
- Selector view is the operator's primary ISR interface — Phase 4 will extend it with enrichment annotations

**Concerns:**
- `find_collocated` iterates over all selector rows × full_df — may be slow on very large wigle_networks (>10k rows). Phase 6 should consider vectorized spatial indexing if needed.

**Blockers:**
- None

---
*Phase: 03-selector-tracking, Plan: 01*
*Completed: 2026-04-05*
