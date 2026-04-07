# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-06)

**Core value:** Track selector movement and patterns (IP, SSID, BSSID, username, network affiliation) to reveal ISR vulnerabilities and package findings into shareable intelligence reports
**Current focus:** Awaiting next milestone — v0.2 complete

## Current Position

Milestone: Awaiting next milestone
Phase: None active
Plan: None
Status: Milestone v0.2 Intel Export complete — ready for next
Last activity: 2026-04-06 — Milestone v0.2 completed

Progress:
- v0.2 Intel Export: [██████████] 100% ✓

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ○        ○        ○     [Milestone complete — ready for next]
```

## Accumulated Context

### Decisions

| Decision | Phase | Impact |
|----------|-------|--------|
| Extend WRAITH Python/Streamlit stack | Init | All phases inherit coord normalization, staleness, Folium pin |
| WiGLE as Phase 1 data source | Init | Free API, geospatial-native, establishes selector tracking foundation |
| MVP sources: WiGLE + Shodan + Telegram + OSM + velocity + entity graph | Init | Shapes phases 1-6 roadmap |
| Passive OSINT only, free sources only | Init | Hard constraint on all phases |
| v0.2 scoped to HTML export only | v0.2 planning | Freeze complexity — no reputation APIs until key strategy defined |
| WRAITH suite direction | v0.2 | WiGLE = OSINT monitoring; Sentinel = future operational watch app |

### Deferred Issues

| Phase | Deferred | Resolution Path |
|-------|----------|-----------------|
| Phase 8–9 | IP Reputation (AbuseIPDB, GreyNoise, Censys) | Awaiting API key strategy — run /paul:milestone when ready |

### Blockers/Concerns

| Blocker | Impact | Resolution Path |
|---------|--------|-----------------|
| WiGLE free-tier rate limits | Limits cameras queried per session | Implement request caching + batching |
| WiGLE API terms acceptance | Blocks live queries until accepted on wigle.net/account | User action required |

## Session Continuity

Last session: 2026-04-06
Stopped at: Milestone v0.2 complete
Next action: /paul:milestone to define v0.3, OR push to GitHub, OR /seed for WRAITH-Sentinel
Resume file: .paul/MILESTONES.md

---
*STATE.md — Updated after every significant action*
