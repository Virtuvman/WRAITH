---
phase: 09-public-feeds
plan: 01
subsystem: feeds
tags: [raven, caltrans, wsdot, youtube, csv, municipal, feeds, ingest, mock]

requires:
  - phase: 08-raven-ingest
    plan: 01
    provides: RAVEN_SCHEMA_COLUMNS, MOCK_B64_PNG, _safe_float
  - phase: 08-raven-ingest
    plan: 02
    provides: raven_media pipeline ready for Phase 10

provides:
  - modules/raven_feeds.py — fetch_caltrans_cameras, fetch_wsdot_cameras, fetch_youtube_thumbnails, fetch_csv_cameras, fetch_all_feeds
  - modules/raven_ingest.py — load_raven_csv, _CSV_COLUMN_ALIASES added
  - data/youtube_cameras.json — 15-entry curated US city traffic cam seed file

affects: [10-raven-map-view]

tech-stack:
  added: []
  patterns:
    - "Mock-first per fetcher — mock=True returns deterministic records with no network calls"
    - "_mock_seed(label) — Random seeded from MD5 hash of label, deterministic per source"
    - "fetch_all_feeds aggregates all four sources; sources=[] param enables selective loading"
    - "load_raven_csv accepts filepath string, Path, or file-like object (Streamlit uploader ready)"
    - "CSV alias map with first-match-wins dedup — handles multi-column → same target conflicts"
    - "coordinates column split — handles 'lat, lon' combined string format"
    - "fetch_csv_cameras with no filepath scans data/*.csv automatically"

key-files:
  created: [modules/raven_feeds.py, data/youtube_cameras.json]
  modified: [modules/raven_ingest.py]

key-decisions:
  - "CSV ingest added to Phase 9 scope (not deferred) — load_raven_csv built before Phase 10 UI wiring so both drop-file and st.file_uploader use the same function"
  - "fetch_csv_cameras(filepath=None) scans data/*.csv when no path given — zero-config for drop-file workflow"
  - "First-match-wins alias dedup — device_type wins over model for product column; extra columns silently dropped by RAVEN_SCHEMA_COLUMNS projection"
  - "CSV mock records center on Washington DC (38.9, -77.0) — distinct from Caltrans (Bay Area) and WSDOT (Seattle) for visual separation on Phase 10 map"
  - "55 combined mock records: 3 Caltrans districts × 8 + 8 WSDOT + 15 YouTube + 8 CSV"

patterns-established:
  - "load_raven_csv is the universal CSV → RAVEN schema adapter — accepts path or file-like"
  - "Phase 10 UI upload: df = load_raven_csv(st.file_uploader(...)) — no additional adapter needed"

duration: ~20min
started: 2026-05-02T00:00:00Z
completed: 2026-05-02T00:00:00Z
---

# Phase 9 Plan 01: Public Feed Integration — Summary

**Four RAVEN feed sources operational: Caltrans municipal, WSDOT municipal, YouTube thumbnails, and CSV with Base64 images. All normalize to the same 13-column RAVEN schema. Mock mode delivers 55 deterministic records across all sources with zero network calls.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~20 min |
| Completed | 2026-05-02 |
| Tasks | 3 auto + 1 checkpoint — all complete |
| Files created | 2 |
| Files modified | 1 (raven_ingest.py) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Caltrans Feed | Pass | 8 mock records, source="municipal", image_url non-null |
| AC-2: WSDOT Feed | Pass | 8 mock records, source="municipal" |
| AC-3: YouTube Thumbnails | Pass | 15 records from seed file, image_b64 set in mock |
| AC-4: Combined Feed | Pass | 55 records, sources: {municipal, youtube, csv} |
| AC-5: Pure Module | Pass | No streamlit in raven_feeds.py |
| AC-6: Schema Compliance | Pass | All 4 fetchers return exact RAVEN_SCHEMA_COLUMNS |
| AC-7: CSV Feed | Pass | 8 mock records, source="csv", image_b64 non-null |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `modules/raven_feeds.py` | Created | Caltrans + WSDOT + YouTube + CSV fetchers + combined feed loader |
| `modules/raven_ingest.py` | Modified | Added load_raven_csv + _CSV_COLUMN_ALIASES |
| `data/youtube_cameras.json` | Created | 15-entry US city traffic cam seed file with lat/lon |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| CSV ingest added to Phase 9 | load_raven_csv needed before Phase 10 app.py wiring; building it now avoids a mid-Phase-10 detour | Phase 10 UI upload is ~5 lines: `df = load_raven_csv(st.file_uploader(...))` |
| First-match-wins alias dedup | Multi-column → same target (device_type + model → product) caused duplicate columns and broken schema projection | Alias map iterates in order; first matching source column wins, rest silently dropped |
| coordinates column split | Existing sample_cameras_combined.csv uses "lat, lon" string — needed to support this format | load_raven_csv detects 'coordinates' column and splits it before alias mapping |
| fetch_csv_cameras scans data/*.csv by default | Zero-config drop-file workflow; operator drops CSV in data/ and it auto-loads | Phase 10 can call fetch_all_feeds() with no arguments and pick up any CSVs present |

## Deviations from Original Plan

- **AC-7 and Task 3 added** — CSV ingest with Base64 support was scoped in before APPLY per user direction. Plan amended before execution; no rework required.
- **55 combined records vs planned 31** — fetch_all_feeds runs all 3 Caltrans districts (24 records) by default, not just district 4. Combined total: 24 + 8 + 15 + 8 = 55.

## Next Phase Readiness

**Ready:**
- All four RAVEN sources callable with mock=True — Phase 10 map development needs no live APIs
- load_raven_csv accepts file-like objects — Phase 10 st.file_uploader wiring is trivial
- fetch_all_feeds() aggregates everything in one call with source-filter support
- data/youtube_cameras.json seed file in place — operator can replace REPLACE_WITH_LIVE_ID entries with real stream IDs

**Blockers:** None

---
*Phase: 09-public-feeds, Plan: 01*
*Completed: 2026-05-02*
