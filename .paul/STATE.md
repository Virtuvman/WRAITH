# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-06)

**Core value:** Track selector movement and patterns (IP, SSID, BSSID, username, network affiliation) to reveal ISR vulnerabilities
**Current focus:** v0.2 Intel Export complete — awaiting next milestone definition

## Current Position

Milestone: v0.2 Intel Export — **COMPLETE**
Phase: 7 of 7 (Selector Intel Report Export) — Complete (2 of 2 plans complete)
Plan: 07-02 complete
Status: Phase 7 unified — v0.2 milestone complete
Last activity: 2026-04-06 — Completed Plan 07-02 UNIFY

Progress:
- v0.2 Intel Export: [██████████] 100%
- Phase 7: [██████████] 100%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Phase 7 complete — v0.2 milestone complete]
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
| WiGLE free-tier rate limits | Limits cameras queried per session | Implement request caching + batching in Phase 1 |
| WiGLE API terms acceptance | Blocks live queries until accepted on wigle.net/account | User action required before Phase 1 testing |

## Session Continuity

Last session: 2026-04-06
Stopped at: v0.2 milestone complete — all phases done
Next action: /paul:complete-milestone to formally close v0.2, OR /paul:milestone to define v0.3 scope
Resume file: .paul/ROADMAP.md

---
*STATE.md — Updated after every significant action*
