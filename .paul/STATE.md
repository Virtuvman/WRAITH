# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-06)

**Core value:** Track selector movement and patterns across wireless observations, exposed devices, and live camera feeds — reveal ISR vulnerabilities, package findings into shareable intelligence reports
**Current focus:** v0.3 RAVEN — Phase 8 Plan 01 complete, ready for Plan 02 (raven_media.py)

## Current Position

Milestone: v0.3 RAVEN Camera Intelligence
Phase: 8 of 10 (RAVEN Ingest Engine) — In Progress (1 of 2 plans complete)
Plan: 08-01 complete
Status: Loop closed — ready for next PLAN
Last activity: 2026-05-02 — 08-01 UNIFY complete

Progress:
- v0.3 RAVEN Camera Intelligence: [░░░░░░░░░░] 10%
- Phase 8: [█████░░░░░] 50%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Loop complete — ready for next PLAN]
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
| CAMERA_PORTS as set | Phase 8-01 | O(1) lookup for port classification in df.apply() |

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
Stopped at: Plan 08-01 UNIFY complete
Next action: /paul:plan — Phase 8 Plan 02: raven_media.py (thumbnail + popup HTML)
Resume file: .paul/phases/08-raven-ingest/08-01-SUMMARY.md

---
*STATE.md — Updated after every significant action*
