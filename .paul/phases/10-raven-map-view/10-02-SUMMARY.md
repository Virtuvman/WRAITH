---
phase: 10-raven-map-view
plan: 02
subsystem: ui
tags: [raven, filter, upload, session-state, streamlit, shodan, csv]

requires:
  - phase: 10-raven-map-view
    plan: 01
    provides: render_raven_view(), RAVEN map view foundation

provides:
  - modules/raven_ingest.py — load_raven_file accepts filepath string OR file-like (BytesIO/StringIO/UploadedFile)
  - app.py — source filter multiselect, file uploader expander, raven_uploaded_df + raven_uploaded_names session state

affects: []

tech-stack:
  added: []
  patterns:
    - "File-like detection: hasattr(filepath, 'read') — works for BytesIO, StringIO, Streamlit UploadedFile"
    - "display_df = concat(raven_df, raven_uploaded_df) — merges loaded feeds with user uploads"
    - "filtered_df = display_df filtered by selected_sources multiselect"
    - "Upload persistence: raven_uploaded_names set prevents re-processing already-loaded files on rerun"

key-files:
  created: []
  modified: [modules/raven_ingest.py, app.py]

key-decisions:
  - "load_raven_file signature changed from (filepath: str) to (filepath) — accepts both path and file-like"
  - "Clear uploads button conditional on raven_uploaded_df non-empty — appears inside expander after first upload"
  - "filtered_df replaces raven_df for all KPI and map rendering — single source of truth post-filter"

duration: ~20min
started: 2026-05-03T00:00:00Z
completed: 2026-05-03T00:00:00Z
---

# Phase 10 Plan 02: RAVEN Filters + File Upload — Summary

**Source filter and file upload are live: operators can isolate any source with a multiselect, upload CSV or Shodan/FOFA JSON directly in the UI, and uploaded records persist across reruns.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~20 min |
| Completed | 2026-05-03 |
| Tasks | 2 auto + 1 checkpoint — all complete |
| Files modified | 2 (modules/raven_ingest.py, app.py) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Source Filter | Pass | Multiselect hides/shows pins and updates KPI live |
| AC-2: Filter Preserves All Sources by Default | Pass | default=all_sources on multiselect |
| AC-3: CSV File Upload | Pass | load_raven_csv accepts file-like; records merged into map |
| AC-4: JSON File Upload | Pass | load_raven_file accepts BytesIO/UploadedFile |
| AC-5: Upload Persists Across Reruns | Pass | raven_uploaded_names set prevents re-processing; raven_uploaded_df persists in session state |
| AC-6: load_raven_file Accepts File-Like | Pass | BytesIO smoke test passed |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `modules/raven_ingest.py` | Modified | load_raven_file extended to accept file-like objects |
| `app.py` | Modified | load_raven_csv import, session state keys, file uploader expander, source filter, filtered_df |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| `hasattr(filepath, "read")` detection | Works for BytesIO, StringIO, and Streamlit UploadedFile without isinstance coupling | load_raven_file is now drop-in compatible with st.file_uploader |
| Clear uploads button conditional on non-empty uploads | Avoids cluttering the expander when nothing is uploaded | Button only appears after first successful upload |

## Phase 10 Complete

Both plans executed. Phase 10 RAVEN Map View is fully delivered:
- Plan 01: Foundation — dark Folium map, 65 mock pins, KPI row, color-coded popups
- Plan 02: Filters + Upload — source filter, CSV/JSON upload, upload persistence

---
*Phase: 10-raven-map-view, Plan: 02*
*Completed: 2026-05-03*
