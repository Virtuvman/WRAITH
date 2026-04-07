# Roadmap: WRAITH-WiGLE

## Current Milestone

**v0.2 — Intel Export** (v0.2.0)
Status: Complete
Phases: 1 of 1 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 7 | Selector Intel Report Export | 2 | Complete | 2026-04-06 |

### Phase 7: Selector Intel Report Export

Focus: One-click HTML report generated from the current Selector view state — captures selector query, observations table, co-location, velocity summary, entity co-occurrence, and anomaly flags into a self-contained shareable document. Plus CSV export of raw observations. No API keys. No new external dependencies.
Plans: 2 (07-01: report engine, 07-02: UI export buttons)

---

## Deferred (awaiting API strategy)

The following phases are defined but frozen until API keys are in hand and operationally validated:

| Phase | Name | Dependency |
|-------|------|------------|
| 8 | IP Reputation Layer (AbuseIPDB + GreyNoise + Censys) | API keys required |
| 9 | Reputation UI Wiring | Phase 8 prerequisite |

---

## Completed Milestones

<details>
<summary>v0.1 WiGLE Core — 2026-04-06 (6 phases) ✅ MVP</summary>

| Phase | Name | Plans | Completed |
|-------|------|-------|-----------|
| 1 | WiGLE Ingestion & API Client | 1 | 2026-04-04 |
| 2 | Heatmap + Globe Visualization | 1 | 2026-04-05 |
| 3 | Selector Tracking & Temporal Filter | 1 | 2026-04-05 |
| 4 | Cross-Source Enrichment (Shodan + OSM) | 2 | 2026-04-05 |
| 5 | Telegram + Social Layer | 2 | 2026-04-06 |
| 6 | Movement Velocity + Entity Graph | 2 | 2026-04-06 |

</details>

---
*Roadmap created: 2026-04-04*
*Last updated: 2026-04-06 — v0.2 scoped to Intel Export only; reputation phases deferred*
