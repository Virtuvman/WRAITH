# Roadmap: WRAITH-WiGLE

## Current Milestone

**v0.3 — RAVEN Camera Intelligence** (v0.3.0)
Status: In Progress
Phases: 0 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 8 | RAVEN Ingest Engine | TBD | Planning | - |
| 9 | Public Feed Integration | TBD | Not started | - |
| 10 | RAVEN Map View | TBD | Not started | - |

### Phase 8: RAVEN Ingest Engine

Focus: Parse Shodan/FOFA raw JSON files containing base64 screenshot fields. Extract device metadata (IP, lat/lon, port, product, org, tags, timestamp) and base64 image data into a unified RAVEN schema. Camera-type classifier filters for Hikvision, Dahua, Axis, RTSP-tagged, and traffic-cam devices. Mock data generator with realistic camera device records including embedded base64 thumbnails.
Plans: TBD (defined during /paul:plan)

### Phase 9: Public Feed Integration

Focus: Ingest live camera snapshots from open municipal traffic camera APIs (NYC DOT, Caltrans, WSDOT, Chicago) and YouTube public thumbnails via curated camera list. All sources normalize to the same RAVEN schema — lat/lon, label, image_b64, source, tags, timestamp. No new Python dependencies beyond requests (already installed).
Plans: TBD (defined during /paul:plan)

### Phase 10: RAVEN Map View

Focus: New RAVEN view in app.py — Folium map with one pin per camera device, color-coded by source (Shodan/FOFA/municipal/YouTube). Click-to-open popup shows thumbnail image + device metadata. Sidebar filter by source, product type, and tags. KPI row: total devices, cameras with screenshots, municipal feeds loaded, countries represented.
Plans: TBD (defined during /paul:plan)

---

## Deferred (awaiting API strategy)

| Phase | Name | Dependency |
|-------|------|------------|
| 11 | IP Reputation Layer (AbuseIPDB + GreyNoise + Censys) | API keys required |
| 12 | Reputation UI Wiring | Phase 11 prerequisite |

---

## Completed Milestones

<details>
<summary>v0.2 Intel Export — 2026-04-06 (1 phase) ✅</summary>

| Phase | Name | Plans | Completed |
|-------|------|-------|-----------|
| 7 | Selector Intel Report Export | 2 | 2026-04-06 |

</details>

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
*Last updated: 2026-05-02 — v0.3 RAVEN Camera Intelligence defined*
