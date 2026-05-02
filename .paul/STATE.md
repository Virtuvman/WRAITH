# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-05-02)

**Core value:** Track selector movement and patterns across wireless observations, exposed devices, and live camera feeds — reveal ISR vulnerabilities, package findings into shareable intelligence reports
**Current focus:** v0.3 RAVEN — Phase 8 complete, ready for Phase 9 (Public Feed Integration)

## Current Position

Milestone: v0.3 RAVEN Camera Intelligence
Phase: 9 of 10 (Public Feed Integration) — Not started
Plan: Not started
Status: Phase 8 complete — ready to plan Phase 9
Last activity: 2026-05-02 — Phase 8 UNIFY complete (both plans)

Progress:
- v0.3 RAVEN Camera Intelligence: [███░░░░░░░] 33%
- Phase 9: [░░░░░░░░░░] 0%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Phase 8 complete — ready for Phase 9 PLAN]
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

### Deferred Issues

| Phase | Deferred | Resolution Path |
|-------|----------|-----------------|
| Phase 11–12 | IP Reputation (AbuseIPDB, GreyNoise, Censys) | Awaiting API key strategy |
| yt-dlp live frame capture | Adds ffmpeg system dep | Revisit post-RAVEN |

### Blockers/Concerns

| Blocker | Impact | Resolution Path |
|---------|--------|-----------------|
| Folium 0.17.0 pin | Cannot upgrade folium | All RAVEN map work must test against pinned version |

## Session Continuity

Last session: 2026-05-02
Stopped at: Phase 8 complete — both plans done
Next action: /paul:plan — Phase 9: Public Feed Integration
Resume file: .paul/phases/08-raven-ingest/08-02-SUMMARY.md

---
*STATE.md — Updated after every significant action*
