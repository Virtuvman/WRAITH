# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-05-02)

**Core value:** Track selector movement and patterns across wireless observations, exposed devices, and live camera feeds — reveal ISR vulnerabilities, package findings into shareable intelligence reports
**Current focus:** v0.3 RAVEN — Phase 10 complete. Milestone v0.3 RAVEN Camera Intelligence DONE.

## Current Position

Milestone: v0.3 RAVEN Camera Intelligence — COMPLETE
Phase: 10 of 10 (RAVEN Map View) — Complete
Plan: 10-02 complete
Status: All phases delivered. Ready for next milestone.
Last activity: 2026-05-03 — Phase 10 Plan 02 UNIFY complete

Progress:
- v0.3 RAVEN Camera Intelligence: [██████████] 100%
- Phase 10: [██████████] 100%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [10-02 complete — milestone closed]
```

## Accumulated Context

### Decisions

| Decision | Phase | Impact |
|----------|-------|--------|
| Extend WRAITH Python/Streamlit stack | Init | All phases inherit coord normalization, staleness, Folium pin |
| Passive OSINT only, free sources only | Init | Hard constraint on all phases |
| WRAITH suite direction | v0.2 | WiGLE = OSINT monitoring; Sentinel = future operational watch app |
| RAVEN: Folium popup (click) not tooltip (hover) for thumbnails | v0.3 planning | Base64 images too large for hover tooltips |
| RAVEN: YouTube thumbnail via img.youtube.com (no yt-dlp) | v0.3 planning | Zero new deps; thumbnail sufficient for PoC |
| RAVEN: unified schema across all sources | v0.3 planning | RAVEN_SCHEMA_COLUMNS defined in raven_ingest.py |
| RAVEN_SCHEMA_COLUMNS in raven_ingest.py | Phase 8-01 | Single source of truth — all downstream modules import from here |
| RAVEN media: Shodan JSON for metadata, own screenshots or samples | Phase 8-02 | make_thumbnail_b64 handles both base64 and file path sources |
| RAVEN video: public municipal feeds (MJPEG/snapshot URLs) | Phase 9 | No stored video files — municipal APIs provide live JPEG snapshot URLs |
| Pillow optional with fallback | Phase 8-02 | Thumbnails work without Pillow, just unresized |
| image_url passthrough — no HTTP fetch in raven_media | Phase 8-02 | Phase 9 fetches images; raven_media only embeds what it receives |
| Screenshot filename: {ip_underscores}_{port}.png | Phase 8-02 | Consistent convention for extract_screenshots and manual drops |
| CSV ingest added to Phase 9 | Phase 9-01 | load_raven_csv built before Phase 10 UI wiring — file-like object support means st.file_uploader drop-in |
| fetch_csv_cameras scans data/*.csv by default | Phase 9-01 | Zero-config drop-file workflow; operator drops CSV in data/ and it auto-loads |
| Inert shims for stale stub imports | Phase 10-01 | match_media/build_media_html replaced with passthrough shims; call sites untouched per user direction |
| RAVEN early-return in main() | Phase 10-01 | Non-CSV views must early-return before CSV pipeline block (~line 2467); pattern for future views |

### Deferred Issues

| Phase | Deferred | Resolution Path |
|-------|----------|-----------------|
| Phase 11–12 | IP Reputation (AbuseIPDB, GreyNoise, Censys) | Awaiting API key strategy |
| yt-dlp live frame capture | Adds ffmpeg system dep | Revisit post-RAVEN |

### Blockers/Concerns

| Blocker | Impact | Resolution Path |
|---------|--------|-----------------|
| Folium 0.17.0 pin | Cannot upgrade folium | All RAVEN map work must test against pinned version |
| YouTube video IDs in seed file | 12 of 15 entries use REPLACE_WITH_LIVE_ID placeholder | Operator must curate active stream IDs before live fetch |

## Session Continuity

Last session: 2026-05-03
Stopped at: Plan 10-02 complete — RAVEN source filter + file upload live
Next action: Run /paul:milestone to open v0.4 or /seed for next feature direction
Resume file: .paul/phases/10-raven-map-view/10-02-SUMMARY.md

---
*STATE.md — Updated after every significant action*
