---
phase: 07-ip-reputation
plan: 02
subsystem: ui
tags: [export, download, html, csv, streamlit, session-state, report]

requires:
  - phase: 07-ip-reputation
    plan: 01
    provides: modules/report.py — generate_html_report, generate_csv_export

provides:
  - app.py — "Export Intelligence Report" section in render_selector_view()
  - app.py — enrichment DataFrame capture to session state (Shodan, OSM, Telegram)
  - app.py — init_session() keys for _last_shodan_df, _last_osm_df, _last_tg_df

affects: []

tech-stack:
  added: []
  patterns:
    - "st.download_button — Streamlit native download, no server-side file I/O"
    - "Session state enrichment capture — store results on successful query for later export"
    - "Lazy import inside function — modules.report and modules.velocity imported at call site, not module top"

key-files:
  created: []
  modified: [app.py]

key-decisions:
  - "Capture enrichment to session state on non-empty result — ensures HTML report reflects whatever operator loaded this session"
  - "compute_velocity(filtered) called fresh at export time — not re-using Movement Analysis expander state"
  - "Lazy imports inside render_selector_view — consistent with existing Shodan/OSM/Telegram import style"

patterns-established:
  - "Export section always at bottom of Selector view — after all enrichment expanders and Raw observations"

duration: ~10min
started: 2026-04-06T00:00:00Z
completed: 2026-04-06T00:00:00Z
---

# Phase 7 Plan 02: Export Intelligence Report UI — Summary

**Two-button export section wired into Selector view: operators can download a self-contained dark-theme HTML intel report and a raw CSV in one click, with enrichment data automatically captured from the session.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~10 min |
| Completed | 2026-04-06 |
| Tasks | 1 of 1 complete (1 auto + 1 checkpoint) |
| Files modified | 1 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Export Section Visible | Pass | Section appears below Raw observations expander when filtered results exist |
| AC-2: HTML Download Works | Pass | wraith_intel_{selector}_{date}.html — full ISR chain, all sections |
| AC-3: CSV Download Works | Pass | wraith_obs_{selector}_{date}.csv — all columns from filtered DataFrame |
| AC-4: No Crash Without Enrichment | Pass | generate_html_report gracefully handles None for all optional DFs |
| AC-5: App Loads Clean | Pass | python -m py_compile app.py exits 0 |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `app.py` | Modified | Added export section, session state keys, enrichment capture |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Capture enrichment on non-empty result only | No point storing empty DFs; report gracefully handles None | Session state reflects actual loaded data |
| compute_velocity called fresh at export | Velocity not stored in session state; recompute is cheap and always current | Avoids stale velocity data from earlier in session |
| Lazy import of report/velocity modules | Matches existing pattern; avoids module-level import of optional deps | Consistent with Shodan/OSM/Telegram import style |

## Deviations from Plan

None — plan executed exactly as written.

## Next Phase Readiness

**Ready:**
- Phase 7 complete — both plans done
- v0.2 deliverable: HTML Intel Report export is fully operational
- modules/report.py + UI export section = complete ISR package

**Blockers:** None

---
*Phase: 07-ip-reputation, Plan: 02*
*Completed: 2026-04-06*
