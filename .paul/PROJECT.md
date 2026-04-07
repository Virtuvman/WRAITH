# WRAITH-WiGLE

## What This Is

A WRAITH-affiliated ISR analytics platform that ingests WiGLE wireless observation data and visualizes it in near-realtime across heatmaps, globe, and flat map views. Designed to track selectors (IP, SSID, BSSID, username, network affiliation) across time and space, surface co-location patterns, expose human and digital-ISR vulnerabilities, and generate shareable intelligence reports.

## Core Value

Users can track the movement and define patterns of selector information — IP address, username, network affiliation, and other identifying characteristics — to reveal ISR vulnerabilities and behavioral intelligence, then package findings into a shareable HTML report.

## Current State

| Attribute | Value |
|-----------|-------|
| Type | Application |
| Version | 0.2.0 |
| Status | MVP — Active |
| Last Updated | 2026-04-06 |

## Requirements

### Validated (Shipped)

- [x] Ingest WiGLE data (WiFi/cell/BT observations) by location or selector — v0.1
- [x] Visualize signal density and movement patterns on heatmap + globe — v0.1
- [x] Track a selector (IP, SSID, BSSID, username) across time and space, with temporal filtering — v0.1
- [x] Identify co-location patterns between selectors across multiple sources — v0.1
- [x] Flag vulnerability indicators (open/WEP networks, unusual signal behavior, entity graph links) — v0.1
- [x] Shodan IP cross-reference — nearby exposed devices panel — v0.1
- [x] OSM/Overpass POI enrichment — nearby points of interest panel — v0.1
- [x] Telegram public channel scraping — keyword search in Selector view — v0.1
- [x] Movement velocity analysis + anomaly detection (haversine, 500 km/h threshold) — v0.1
- [x] Entity co-occurrence ranking via coloc_count — v0.1
- [x] HTML intel report export — self-contained dark-theme ISR report from Selector view — v0.2
- [x] CSV observations export — raw filtered observations download — v0.2

### Active (In Progress)

None — awaiting next milestone definition.

### Planned (Deferred)

- [ ] IP Reputation layer — AbuseIPDB + GreyNoise + Censys cross-reference — pending API key strategy
- [ ] Reputation UI wiring — Phase 9 — pending Phase 8

### Out of Scope

- Active scanning of any kind — passive OSINT only
- Paid data sources — free/open tier only
- Non-Python runtimes
- PDF export — HTML only for v0.2

## Target Users

**Primary:** OSINT analyst / ISR operator
- Tracking selectors across wireless observations and digital footprints
- Identifying patterns of life and co-location
- Assessing friendly and hostile ISR vulnerabilities
- Packaging findings into shareable intelligence reports

## Context

**Technical Context:**
Extends the WRAITH stack (Python, Streamlit, Plotly, Folium, pandas). Runs as a standalone app or WRAITH-affiliated module. Shares coordinate normalization and staleness patterns from core WRAITH. Local-first deployment with optional hosted pilot pattern inherited from WRAITH.

**Suite Context:**
WRAITH-WiGLE is the OSINT monitoring arm of the emerging WRAITH suite. WRAITH-Sentinel (future) will handle real-time operational watch. The two apps are designed to complement, not overlap.

## Constraints

### Technical Constraints

- WiGLE free API tier — rate limits apply, queries must be batched and cached
- Passive OSINT only — no active scanning, no unauthorized access
- Python/Streamlit stack — no new runtimes introduced
- Folium pin: folium==0.17.0 + branca==0.7.2 (do not upgrade — HeatMap serialization regression risk)
- Overpass API — public endpoint, cache results locally to avoid abuse
- matplotlib not installed in WRAITH env — use Streamlit native column_config instead

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
| Mock-first on all modules | All features usable without live API keys from day one | 2026-04-04 | Active |
| v0.2 scoped to export only | Freeze complexity at MVP; reputation APIs deferred until key strategy defined | 2026-04-06 | Active |
| WRAITH suite direction | WiGLE = OSINT monitoring arm; Sentinel = future operational watch app | 2026-04-06 | Active |
| Inline CSS only in HTML report | Self-contained report works offline, air-gapped, any browser | 2026-04-06 | Active |

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Selector query → heatmap with temporal filter | Working end-to-end | Working | ✅ Shipped v0.1 |
| Co-location between selectors surfaced | Linked in Selector view | Working | ✅ Shipped v0.1 |
| Full ISR chain in single view | WiGLE → Shodan → OSM → TG → Velocity → Entity | Working | ✅ Shipped v0.1 |
| Shareable intel report | One-click HTML export from Selector view | Working | ✅ Shipped v0.2 |
| Open/WEP vulnerability flags | Auto-flagged in BLUF | Partial (near_camera flag) | In progress |
| Free-tier rate limit handling | No crash on 500-camera query | Cached | Partial |

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Language | Python 3.x | Consistent with WRAITH |
| UI | Streamlit | Local + optional hosted pilot |
| Globe/Map | Plotly + Folium | Inherit WRAITH layer patterns |
| Data | pandas | CSV + API response normalization |
| WiGLE API | requests + Basic auth | Free tier, API token from wigle.net/account |
| Shodan | requests + free tier | IP cross-reference, mock fallback |
| OSM/Overpass | requests, no auth | POI enrichment, POST query, session cache |
| Telegram | Public scrape via t.me/s/ | No auth, no new deps, regex extraction |
| Velocity | stdlib math (haversine) | No scipy/numpy dependency |
| Report | Jinja2 + pandas | Already installed via Streamlit |
| Config | python-dotenv | Keys in .env, never committed |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-06 after v0.2 Intel Export*
