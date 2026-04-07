# WRAITH-WiGLE

## What This Is

A WRAITH-affiliated ISR analytics platform that ingests WiGLE wireless observation data and visualizes it in near-realtime across heatmaps, globe, and flat map views. Designed to track selectors (IP, SSID, BSSID, username, network affiliation) across time and space, surface co-location patterns, and expose human and digital-ISR vulnerabilities for both hostile and friendly entities. MVP data sources: WiGLE, Shodan, Telegram public channels, OpenStreetMap/Overpass, with movement velocity and entity graph analytics.

## Core Value

Users can track the movement and define patterns of selector information — IP address, username, network affiliation, and other identifying characteristics — to reveal ISR vulnerabilities and behavioral intelligence.

## Current State

| Attribute | Value |
|-----------|-------|
| Type | Application |
| Version | 0.0.0 |
| Status | Initializing |
| Last Updated | 2026-04-04 |

## Requirements

### Core Features

- Ingest WiGLE data (WiFi/cell/BT observations) by location or selector
- Visualize signal density and movement patterns on heatmap + globe
- Track a selector (IP, SSID, BSSID, username) across time and space, with temporal filtering
- Identify co-location patterns between selectors across multiple sources
- Flag vulnerability indicators (open/WEP networks, unusual signal behavior, entity graph links)

### Validated (Shipped)

- WiGLE ingestion module + API client (Phase 1)
- Heatmap layer with temporal slider (Phase 2)
- Selector query + co-location detection + temporal filter (Phase 3)
- Shodan IP cross-reference — nearby exposed devices panel (Phase 4)
- OSM/Overpass POI enrichment — nearby points of interest panel (Phase 4)

### Active (In Progress)
None.

### Validated (Shipped) — continued

- Telegram public channel scraping — keyword search in Selector view (Phase 5)
- Movement velocity analysis + anomaly detection (Phase 6)
- Entity co-occurrence ranking via coloc_count (Phase 6)
- HTML intel report export — self-contained dark-theme ISR report from Selector view (Phase 7)
- CSV observations export — raw filtered observations download (Phase 7)

### Planned (Next)

None — v0.2 Intel Export milestone complete. Deferred phases (8–9, IP Reputation) pending API key strategy.

### Out of Scope

- Active scanning of any kind — passive OSINT only
- Paid data sources — free/open tier only
- Non-Python runtimes

## Target Users

**Primary:** OSINT analyst / ISR operator
- Tracking selectors across wireless observations and digital footprints
- Identifying patterns of life and co-location
- Assessing friendly and hostile ISR vulnerabilities

## Context

**Technical Context:**
Extends the WRAITH stack (Python, Streamlit, Plotly, Folium, pandas). Runs as a standalone app or WRAITH-affiliated module. Shares coordinate normalization and staleness patterns from core WRAITH. Local-first deployment with optional hosted pilot pattern inherited from WRAITH.

## Constraints

### Technical Constraints

- WiGLE free API tier — rate limits apply, queries must be batched and cached
- Passive OSINT only — no active scanning, no unauthorized access
- Python/Streamlit stack — no new runtimes introduced
- Folium pin: folium==0.17.0 + branca==0.7.2 (do not upgrade — HeatMap serialization regression risk)
- Overpass API — public endpoint, cache results locally to avoid abuse

### Business Constraints

- Local-first deployment; optional hosted pilot
- API keys/credentials never committed to git
- Free/open data sources only — flag any suggestion requiring payment
- Solo developer — no review cycle, move fast

### Compliance Constraints

- Passive observation only — no active probing or unauthorized access
- Data handling must respect ODbL (OpenStreetMap), WiGLE non-commercial terms

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| Extend WRAITH stack (Python/Streamlit/Folium) | Avoids new runtime, reuses coord normalization and staleness patterns | 2026-04-04 | Active |
| WiGLE as first data source | Free API, geospatial-native, direct lat/lon output, strong selector tracking potential | 2026-04-04 | Active |
| OSM/Overpass for POI enrichment | No auth, no cost, adds behavioral context to coordinates | 2026-04-04 | Active |
| MVP sources: WiGLE + Shodan + Telegram + OSM + velocity + entity graph | Covers device, network, social, and spatial layers with no paid dependencies | 2026-04-04 | Active |

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Selector query → heatmap with temporal filter | Working end-to-end | - | Not started |
| Co-location between selectors surfaced visually | Two selectors linked on map | - | Not started |
| Open/WEP vulnerability flags | Auto-flagged in BLUF | - | Not started |
| Free-tier rate limit handling | No crash on 500-camera query | - | Not started |

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Language | Python 3.x | Consistent with WRAITH |
| UI | Streamlit | Local + optional hosted pilot |
| Globe/Map | Plotly + Folium | Inherit WRAITH layer patterns |
| Data | pandas | CSV + API response normalization |
| WiGLE API | requests + Basic auth | Free tier, API token from wigle.net/account |
| Shodan | requests + free tier | IP cross-reference |
| OSM/Overpass | requests, no auth | POI enrichment, POST query |
| Telegram | Bot API or public scrape | Public channels only |
| Config | python-dotenv | Keys in .env, never committed |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-04*
