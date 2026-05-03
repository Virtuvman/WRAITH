---
phase: 04-cross-source-enrichment
plan: 02
subsystem: ui
tags: [shodan, osm, streamlit, selector-view, enrichment, sidebar]

requires:
  - phase: 04-01
    provides: modules/shodan.py — shodan_search_near, SHODAN_RESULT_COLUMNS
  - phase: 04-01
    provides: modules/osm.py — overpass_pois, OSM_RESULT_COLUMNS
  - phase: 03-selector-tracking
    provides: render_selector_view() — filtered DataFrame, co-location table

provides:
  - render_sidebar(): Shodan Enrichment section with mock checkbox + conditional API key input
  - render_selector_view(): "Nearby Exposed Devices (Shodan)" expander with Query Shodan button
  - render_selector_view(): "Nearby Points of Interest (OSM)" expander with Query OSM button
  - init_session(): shodan_mock and shodan_api_key session state keys

affects: [06-entity-graph]

tech-stack:
  added: []
  patterns:
    - "Enrichment panels: button-triggered, not auto-query — respects Shodan rate limits"
    - "Centroid query: mean(trilat)/mean(trilong) of filtered observations as single query coordinate"
    - "Inline imports inside button handlers — keeps modules.shodan/osm out of top-level imports"
    - "section-label CSS unreliable for sidebar visibility — plain markdown bold used instead"

key-files:
  created: []
  modified: [app.py]

key-decisions:
  - "Button-triggered enrichment only — avoids auto-querying Shodan on every Streamlit rerender"
  - "Centroid-based query (not per-observation) — one API call per button click regardless of filtered size"
  - "Replaced section-label div with plain bold markdown for Shodan sidebar header — CSS class was rendering invisible"

patterns-established:
  - "Enrichment panels slot after co-location table, before raw observations — natural ISR workflow order"
  - "st.session_state.shodan_mock / shodan_api_key initialized in init_session() — consistent with wigle_* pattern"

duration: ~20min
started: 2026-04-05T00:00:00Z
completed: 2026-04-05T00:00:00Z
---

# Phase 4 Plan 02: Cross-Source Enrichment UI Wiring — Summary

**Shodan and OSM enrichment panels wired into the Selector view — button-triggered centroid queries with mock fallback and graceful empty-result handling.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~20 min |
| Completed | 2026-04-05 |
| Tasks | 3 of 3 complete (2 auto + 1 checkpoint) |
| Files modified | 1 (app.py) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Shodan Sidebar Controls | Pass | Mock checkbox + conditional API key input; session state keys initialized |
| AC-2: Nearby Exposed Devices Panel | Pass | Query Shodan button returns mock table; empty result shows info message |
| AC-3: Nearby POI Panel | Pass | Query OSM button calls overpass_pois; offline returns empty with info message |
| AC-4: No Crash on Empty or No Data | Pass | Both panels guarded by filtered.empty early return |
| AC-5: App Loads Clean | Pass | py_compile exit 0 |

## Accomplishments

- Both enrichment panels integrated into existing Selector view without touching globe, heatmap, or co-location logic
- Button-triggered pattern avoids rate-limit exposure during normal Streamlit rerenders
- Centroid approach keeps UI snappy — one API call per button click regardless of filtered DataFrame size

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `app.py` | Modified | init_session() keys; Shodan sidebar section; Shodan + OSM expanders in render_selector_view() |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Button-triggered only | Shodan free tier: 1 req/sec — auto-query on every rerender would exhaust rate limit instantly | Operator controls when enrichment runs |
| Centroid query | One Overpass/Shodan call per click regardless of filtered size | Fast, predictable; sufficient for operator orientation |
| Bold markdown for sidebar label | `section-label` CSS div was rendering invisible in sidebar context | Sidebar header now always visible |

## Deviations from Plan

**1. Sidebar label style changed**
- **Issue:** `<div class="section-label">Shodan Enrichment</div>` rendered invisible — the CSS class applies dark text that blends into sidebar background
- **Fix:** Replaced with `st.sidebar.markdown("**SHODAN ENRICHMENT**")` — plain bold, always visible
- **Impact:** Minor cosmetic deviation; functionality unchanged

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| section-label CSS invisible in sidebar | Replaced with plain bold markdown — identified during checkpoint visual verification |

## Next Phase Readiness

**Ready:**
- Selector view now delivers the full Phase 4 cross-source picture: WiGLE observations → co-location → Shodan exposure → OSM context
- `shodan_search_near` and `overpass_pois` callable from any future view (Phase 6 entity graph can reuse directly)
- `shodan_api_key` stored in session state — Phase 6 can read it without re-prompting

**Concerns:**
- Shodan sidebar section always renders (even without WiGLE enabled) — minor UX inconsistency; could be wrapped in `if wigle_enabled:` in a future pass
- Centroid query loses precision when filtered observations span multiple cities — acceptable for MVP but Phase 6 should consider per-cluster queries

**Blockers:**
- None

---
*Phase: 04-cross-source-enrichment, Plan: 02*
*Completed: 2026-04-05*
