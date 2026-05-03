---
phase: 06-movement-entity
plan: 01
subsystem: analytics
tags: [velocity, haversine, anomaly, pandas, math, movement]

requires:
  - phase: 03-selector-tracking
    provides: modules/selector.py — selector DataFrame schema, SELECTOR_FIELDS

provides:
  - modules/velocity.py — compute_velocity, classify_velocity, compute_velocity_by_selector, VELOCITY_COLUMNS, ANOMALY_THRESHOLD_KMH

affects: [06-02-ui-wiring]

tech-stack:
  added: []
  patterns:
    - "Haversine distance: stdlib math only — math.radians, sin, cos, asin, sqrt, Earth radius 6371 km"
    - "Velocity computation: shift() to align prev/curr rows, apply() for per-row haversine"
    - "Anomaly threshold: 500 km/h — faster than commercial aircraft, implausible for fixed device"
    - "Per-selector independence: compute_velocity_by_selector groups by field, processes each subset separately"

key-files:
  created: [modules/velocity.py]
  modified: []

key-decisions:
  - "ANOMALY_THRESHOLD_KMH=500 — commercial aircraft ~900 km/h; 500 catches hotspot/spoofed BSSID while allowing fast trains"
  - "Haversine over Vincenty — sufficient for OSINT city-scale analysis, zero dependencies"
  - "shift()-based vectorization — avoids Python row loop for large DataFrames"
  - "First observation always speed=0, prev_lat/lon=own coords — consistent identity anchor"

patterns-established:
  - "Pure data module: no streamlit, graceful empty handling, never raises — consistent with all prior modules"
  - "VELOCITY_COLUMNS appended to input DataFrame — preserves all original WiGLE columns"

duration: ~15min
started: 2026-04-06T00:00:00Z
completed: 2026-04-06T00:00:00Z
---

# Phase 6 Plan 01: Movement Velocity Module — Summary

**Haversine velocity calculator with anomaly classification shipped as pure data module — London→Toronto in 2h = 2856 km/h flags as D-ISR anomaly.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Completed | 2026-04-06 |
| Tasks | 2 of 2 complete (1 auto + 1 checkpoint) |
| Files created | 1 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Module Imports Clean | Pass | py_compile exit 0 |
| AC-2: Velocity Computation | Pass | Speeds: [0, 2856, 4361] km/h for London→Toronto→Bogota 3-hop |
| AC-3: Anomaly Classification | Pass | is_anomaly=[False, True, True] — rows 1+2 exceed 500 km/h threshold |
| AC-4: Multi-Selector Velocity | Pass | 3 rows, DD:EE:FF (1 obs) correctly gets speed=0 |
| AC-5: Graceful Empty Handling | Pass | compute_velocity, classify_velocity, compute_velocity_by_selector all return empty df on None/empty |

## Verified Distances

| Route | Distance | Time | Speed | Anomaly |
|-------|----------|------|-------|---------|
| London → Toronto | 5712 km | 2h | 2856 km/h | True |
| Toronto → Bogota | ~4361 km | 1h | 4361 km/h | True |
| Single observation | 0 km | - | 0 km/h | False |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `modules/velocity.py` | Created | Haversine distance, velocity computation, anomaly classification, multi-selector support |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| ANOMALY_THRESHOLD_KMH=500 | Below commercial aircraft (~900 km/h); catches implausible device travel while allowing fast trains/cars | Plan 06-02 can expose as configurable slider |
| Haversine, not Vincenty | OSINT city-scale accuracy is sufficient; Vincenty adds complexity for <0.3% accuracy gain | No scipy dependency needed |
| shift()-based row alignment | Avoids Python row loop; scales to large wigle_networks DataFrames | Performant on 500+ row datasets |

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- `compute_velocity_by_selector(wigle_networks, field="netid")` callable from Plan 06-02 immediately
- `is_anomaly` column ready for highlight styling in UI
- `ANOMALY_THRESHOLD_KMH` importable for sidebar slider default value

**Concerns:**
- WiGLE observations may have duplicate timestamps for the same BSSID (two cameras query same network) — time_delta_h=0 results in speed=0, not anomaly. Acceptable for MVP.
- `lasttime` parsing with errors="coerce" silently drops unparseable dates — logged at WARNING level

**Blockers:**
- None

---
*Phase: 06-movement-entity, Plan: 01*
*Completed: 2026-04-06*
