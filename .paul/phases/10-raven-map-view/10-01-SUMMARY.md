---
phase: 10-raven-map-view
plan: 01
subsystem: ui
tags: [raven, folium, map, popup, thumbnail, streamlit, navigation, session-state]

requires:
  - phase: 08-raven-ingest
    provides: RAVEN_SCHEMA_COLUMNS, generate_mock_raven, build_popup_html, tag_camera_type
  - phase: 09-public-feeds
    provides: fetch_all_feeds, load_raven_csv, load_raven_file

provides:
  - app.py — render_raven_view(), _load_raven_data(), RAVEN nav option, RAVEN session state
  - RAVEN map view functional end-to-end with mock data (65 pins, color-coded, click popups)

affects: [10-02-raven-filters-upload]

tech-stack:
  added: []
  patterns:
    - "RAVEN early-return in main() — bypasses CSV pipeline entirely before no-data/KPI blocks"
    - "Inert shims replace stale stub imports — call sites unchanged, module replaced"
    - "_RAVEN_SOURCE_COLORS dict — source → hex color, DEFAULT fallback for unknown sources"
    - "view == RAVEN early-return — prevents CSV onboarding UI from rendering over RAVEN view"

key-files:
  created: []
  modified: [app.py]

key-decisions:
  - "Inert shims for match_media/build_media_html — replaced ImportError-causing imports with passthrough/empty-string functions; call sites at lines ~941 and ~1419 left untouched per user direction"
  - "Early-return bypass for RAVEN in main() — RAVEN view must not run through the CSV pipeline (no-data state, KPI cards, alert banners); inserting before that block keeps RAVEN independent of CSV data state"
  - "RAVEN placed between Selector and Data Table in nav — groups analytical views together"

patterns-established:
  - "New non-CSV views should early-return in main() before the CSV pipeline block (line ~2467)"
  - "Source color lookup: _RAVEN_SOURCE_COLORS.get(src, _RAVEN_DEFAULT_COLOR)"

duration: ~25min
started: 2026-05-03T00:00:00Z
completed: 2026-05-03T00:00:00Z
---

# Phase 10 Plan 01: RAVEN Map View Foundation — Summary

**RAVEN Camera Intelligence map view is live: 65 mock pins color-coded by source on a dark Folium map with click-to-open popup thumbnails, KPI row, and source legend — accessible via the sidebar nav without touching the CSV data pipeline.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~25 min |
| Completed | 2026-05-03 |
| Tasks | 2 auto + 1 checkpoint — all complete |
| Files modified | 1 (app.py) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: App Starts Without ImportError | Pass | Stale imports shimmed; app starts cleanly |
| AC-2: RAVEN Navigation | Pass | "RAVEN" in sidebar View radio between Selector and Data Table |
| AC-3: RAVEN KPI Row | Pass | 4-column row: total pins, with screenshot, sources, countries |
| AC-4: Folium Map with Color-Coded Pins | Pass | Dark map, CircleMarkers color by source, tooltips on hover |
| AC-5: Popup Thumbnail | Pass | build_popup_html() dark-theme popup on click |
| AC-6: Empty State | Pass | Info message + Load RAVEN Data button shown before data loaded |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `app.py` | Modified | Shims, RAVEN imports, session state, nav, render functions, early-return bypass |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Inert shims instead of call-site surgery | User direction: render stale feature inert, don't spend time on staleness code | `match_media` and `build_media_html` call sites at ~941, ~1419 untouched; shims are passthrough/empty |
| Early-return before CSV pipeline | RAVEN is source-independent; running through KPI/no-data/alert blocks caused RAVEN content to render buried below CSV UI | All future non-CSV views should follow same pattern |

## Deviations from Plan

### Auto-fixed Issues

**1. RAVEN buried under CSV pipeline UI**
- **Found during:** Checkpoint visual verify
- **Issue:** `main()` renders CSV no-data message, `render_kpis()`, and alert banners unconditionally before view routing — RAVEN rendered below all of it
- **Fix:** Added `if view == "RAVEN": render_raven_view(); return` before the `if not files_dict:` block
- **Files:** `app.py`
- **Verification:** User confirmed map + KPI row visible after fix (approved checkpoint)

**2. `ast.parse` UTF-8 encoding**
- **Found during:** Task 1 verification
- **Issue:** `open('app.py').read()` used system default encoding (cp1252) which couldn't decode UTF-8 characters in app.py
- **Fix:** Added `encoding='utf-8'` to all verify commands
- **Impact:** No code change required; verify pattern updated

## Next Phase Readiness

**Ready:**
- RAVEN map view functional with mock data — 65 pins across all 4 sources
- `render_raven_view()` is self-contained — Plan 10-02 adds filters without restructuring
- Early-return bypass pattern documented for non-CSV views

**Plan 10-02 scope:**
- Sidebar source filter toggles (checkboxes per source)
- `st.file_uploader` for CSV and Shodan JSON
- Product type / tag filters

**Blockers:** None

---
*Phase: 10-raven-map-view, Plan: 01*
*Completed: 2026-05-03*
