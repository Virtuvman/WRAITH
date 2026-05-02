---
phase: 08-raven-ingest
plan: 02
subsystem: media
tags: [raven, thumbnail, pillow, base64, popup, html, screenshot, extractor, cli]

requires:
  - phase: 08-raven-ingest
    plan: 01
    provides: RAVEN_SCHEMA_COLUMNS, generate_mock_raven, filter_cameras

provides:
  - modules/raven_media.py — make_thumbnail_b64, build_popup_html, build_tooltip_text, extract_screenshots
  - scripts/extract_raven_screenshots.py — CLI: JSON export → PNG files on disk
  - requirements.txt — Pillow>=10.0.0 added

affects: [10-raven-map-view, 09-public-feeds]

tech-stack:
  added: [Pillow>=10.0.0 (optional — graceful fallback if not installed)]
  patterns:
    - "Optional Pillow import — try/except at module level, _PIL_AVAILABLE flag"
    - "Priority-order image sourcing — file path arg > row image_b64 > None"
    - "image_url passthrough — no HTTP fetch in media module; Phase 9 fetches, media embeds"
    - "html.escape on all popup metadata — XSS-safe output"

key-files:
  created: [modules/raven_media.py (replaced stub), scripts/extract_raven_screenshots.py]
  modified: [requirements.txt]

key-decisions:
  - "Pillow optional, not required — raven_media works without it, thumbnails just unresized"
  - "image_url passthrough in popup HTML — <img src=url> with onerror hide; no requests in this module"
  - "extract_screenshots uses ip+port as filename — matches raven_matcher.py file-path convention from prior stub"
  - "screenshot extractor added to 08-02 scope (not a separate plan) — small, directly related, completes offline prep pipeline"

patterns-established:
  - "Popup HTML always self-contained — no external CDN, no src URLs that could fail offline"
  - "extract_screenshots → data/screenshots/{ip_with_underscores}_{port}.png naming convention"

duration: ~15min
started: 2026-05-02T00:00:00Z
completed: 2026-05-02T00:00:00Z
---

# Phase 8 Plan 02: RAVEN Media + Screenshot Extractor — Summary

**Image pipeline complete: Shodan base64 and local file path → resized thumbnail → dark-theme Folium popup HTML; CLI extractor dumps all Shodan screenshots to disk in one command.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Completed | 2026-05-02 |
| Tasks | 2 auto + 1 checkpoint — all complete |
| Files created | 2 |
| Files modified | 1 (requirements.txt) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Base64 Source | Pass | make_thumbnail_b64 returns non-null b64 for mock row with image_b64 |
| AC-2: File Path Source | Pass | _load_file_bytes + _resize path exercised; graceful None on missing file |
| AC-3: Graceful Fallback | Pass | build_popup_html returns valid HTML with "No image" div when image_b64 is None |
| AC-4: Popup HTML Structure | Pass | base64 img tag + label + ip:port + org + source + tags + timestamp present |
| AC-5: Pure Module | Pass | No streamlit import in raven_media.py |
| AC-6: Screenshot Extractor | Pass | 3 files written to temp dir; extract_screenshots returns correct counts |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `modules/raven_media.py` | Created (replaced stub) | Full image pipeline + popup builder + extractor |
| `scripts/extract_raven_screenshots.py` | Created | CLI: Shodan/FOFA JSON → PNG files to disk |
| `requirements.txt` | Modified | Pillow>=10.0.0 added as optional dep |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Pillow optional with graceful fallback | Not guaranteed installed; thumbnails work without it | No hard dep added; Streamlit Cloud installs it fine |
| image_url passthrough — no HTTP fetch | Media module stays pure data; Phase 9 handles fetching | build_popup_html renders `<img src=url>` with onerror=hide for municipal feeds |
| Screenshot filename: ip_underscore_port.png | Matches file-path convention from original stub | Operator files dropped in data/screenshots/ with matching names auto-link to RAVEN pins |
| Added extractor to 08-02 (not separate plan) | Small scope, directly related, completes offline prep | Phase 9 and 10 can assume data/screenshots/ is populated before map renders |

## Deviations from Plan

None — plan executed as written. Screenshot extractor was added to scope before APPLY began (user-approved addition).

## Next Phase Readiness

**Ready:**
- Full RAVEN data pipeline established: JSON → parse → classify → thumbnail → popup HTML
- extract_screenshots() + CLI script enables offline prep before app launch
- build_popup_html() ready for Phase 10 Folium map integration
- image_url passthrough ready for Phase 9 municipal feed URLs

**Blockers:** None

---
*Phase: 08-raven-ingest, Plan: 02*
*Completed: 2026-05-02*
