---
phase: 08-raven-ingest
plan: 01
subsystem: ingest
tags: [raven, shodan, fofa, json, camera, classifier, mock, base64]

requires: []

provides:
  - modules/raven_ingest.py — RAVEN_SCHEMA_COLUMNS, Shodan/FOFA parsers, file loader, mock generator
  - modules/raven_matcher.py — camera classifier, filter, type tagger

affects: [08-02, 09-public-feeds, 10-raven-map-view]

tech-stack:
  added: []
  patterns:
    - "RAVEN unified schema — 13-column contract shared by all downstream modules"
    - "_empty_record() base — all parsers merge into empty dict so columns never KeyError"
    - "Never-raise pattern — load_raven_file catches all exceptions, returns empty DF"
    - "Deterministic mock — hash-seeded rng ensures reproducible test data per (lat,lon,n)"

key-files:
  created: [modules/raven_ingest.py, modules/raven_matcher.py]
  modified: []

key-decisions:
  - "RAVEN_SCHEMA_COLUMNS defined in raven_ingest.py — single source of truth for all phases"
  - "raven_matcher.py replaces early stub — existing file had wrong purpose (file-path media matcher)"
  - "CAMERA_PORTS set not list — O(1) lookup for port classification"
  - "classify_camera never raises — returns False on any exception, safe for df.apply()"

patterns-established:
  - "All RAVEN parsers merge into _empty_record() — downstream code can rely on all 13 columns present"
  - "load_raven_file detects format automatically — Shodan search / single host / FOFA / NDJSON"

duration: ~15min
started: 2026-05-02T00:00:00Z
completed: 2026-05-02T00:00:00Z
---

# Phase 8 Plan 01: RAVEN Ingest Engine — Summary

**Shodan/FOFA JSON parser and camera classifier established: unified 13-column RAVEN schema, format auto-detection, deterministic mock generator with embedded base64 thumbnails, keyword+port camera classification.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Completed | 2026-05-02 |
| Tasks | 2 auto + 1 checkpoint — all complete |
| Files created | 2 |
| Files modified | 0 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Unified Schema | Pass | All 13 RAVEN_SCHEMA_COLUMNS present on every parsed record via _empty_record() merge |
| AC-2: Mock Generator | Pass | generate_mock_raven(n=10) → 10 rows, all columns, image_b64 non-null for all |
| AC-3: File Loader | Pass | load_raven_file() handles Shodan/FOFA/NDJSON, returns empty DF on error, never raises |
| AC-4: Camera Filter | Pass | filter_cameras() returned 10/10 mock records as cameras; tag_camera_type() added column |
| AC-5: Pure Modules | Pass | Neither file contains streamlit import |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `modules/raven_ingest.py` | Created (replaced stub) | RAVEN schema, Shodan/FOFA parsers, file loader, mock generator |
| `modules/raven_matcher.py` | Created (replaced stub) | Camera keyword+port classifier, DataFrame filter, type tagger |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Replace existing stubs entirely | Prior raven_ingest.py had no schema/mock; raven_matcher.py was a file-path media matcher — wrong purpose | Clean foundation for downstream phases |
| RAVEN_SCHEMA_COLUMNS in raven_ingest.py | Single source of truth; all phases import from here | All downstream modules import RAVEN_SCHEMA_COLUMNS from raven_ingest |
| CAMERA_PORTS as set not list | O(1) membership test; ports checked per-row in df.apply() | Minor perf gain with correct semantics |
| NDJSON detection in load_raven_file | Shodan bulk exports are one-record-per-line; multi-line text triggers NDJSON path | Handles real Shodan export format, not just API response format |

## Deviations from Plan

| Type | Detail | Impact |
|------|--------|--------|
| Files replaced, not created | raven_ingest.py and raven_matcher.py existed as early stubs from prior session | No impact — stubs were incomplete and did not match plan spec |

## Next Phase Readiness

**Ready:**
- RAVEN_SCHEMA_COLUMNS established as shared contract — Plan 08-02 (raven_media.py) imports directly
- generate_mock_raven() provides test data for all downstream UI development
- filter_cameras() and tag_camera_type() ready for use in Phase 10 map view

**Blockers:** None

---
*Phase: 08-raven-ingest, Plan: 01*
*Completed: 2026-05-02*
