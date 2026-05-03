# WRAITH-WiGLE

**Wide-area Reconnaissance & Asset Intelligence Tracking Hub — WiGLE Module**

A local-first Streamlit ISR analytics platform that ingests WiGLE wireless observation data, tracks selectors (SSID, BSSID, IP, username, network affiliation) across time and space, cross-references enrichment sources, and generates shareable intelligence reports. Part of the WRAITH suite.

---

## Capabilities

### Core Intelligence Chain

| Layer | Source | What It Surfaces |
|-------|--------|-----------------|
| Observations | WiGLE API / CSV | WiFi, cell, Bluetooth signal records with coordinates and timestamps |
| Heatmap | WiGLE | Signal density overlay on Folium basemap with temporal slider |
| Globe | WiGLE | Orthographic globe with encryption-color coded pins |
| Selector Tracking | WiGLE | Field/value query — SSID, BSSID, encryption type, near-camera flag |
| Co-location | WiGLE | Networks observed within ~1 km of selector, ranked by co-occurrence count |
| Shodan | Shodan free tier | Exposed devices, open ports, organizations near observation centroid |
| OSM/Overpass | OpenStreetMap | Nearby amenities, military sites, government buildings within 500 m |
| Telegram | Public channels | Open-source mentions of selector keyword across configurable channel list |
| Velocity Analysis | Computed | Haversine movement speed between observations, anomaly flagging at 500 km/h |
| Entity Co-occurrence | Computed | Entity graph ranked by co-location frequency |
| Intel Report | Jinja2 | Self-contained dark-theme HTML ISR report + CSV export, one click |

### Key Features

- **Mock-first design** — every enrichment source has a mock fallback; full functionality without live API keys
- **Session-aware reporting** — HTML report captures whatever enrichment data was loaded during the session
- **Pure data modules** — no Streamlit imports in modules/; all modules are independently importable
- **Passive OSINT only** — no active scanning, no unauthorized access, free/open sources only

---

## Quick Start

### 1. Clone and create virtual environment

```bash
git clone https://github.com/Virtuvman/WRAITH-WiGLE.git
cd WRAITH-WiGLE
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp env.example .env
# Edit .env — add API keys (all optional; mock mode works without them)
```

### 4. Run

```bash
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## Module Overview

```
app.py                    # Streamlit entrypoint — all views and UI
modules/
  wigle.py                # WiGLE API client + mock data generator
  selector.py             # Selector query, temporal filter, co-location detection
  shodan.py               # Shodan free tier IP cross-reference
  osm.py                  # Overpass API POI enrichment with session cache
  telegram.py             # Public Telegram channel keyword scraping
  velocity.py             # Haversine velocity analysis + anomaly detection
  report.py               # Jinja2 HTML report generator + CSV export
  ingestion.py            # CSV ingestion + coordinate normalization
  coord_normalizer.py     # Multi-format coordinate normalization (decimal, MGRS, DMS, UTM)
  staleness.py            # 4-tier staleness classification (CURRENT/REVIEW/STALE/EXPIRED)
data/                     # Sample datasets (WiGLE mock, camera OSINT)
docs/                     # Planning documents, concept briefs
```

---

## Configuration

Copy `env.example` to `.env` and fill in as needed. All keys are optional — mock mode is enabled by default when keys are absent.

```env
# WiGLE API (free account at wigle.net/account)
WIGLE_API_NAME=your_api_name
WIGLE_API_TOKEN=your_api_token

# Shodan (free tier at shodan.io)
SHODAN_API_KEY=your_shodan_key

# Pilot access gate (for hosted deployments)
PILOT_ACCESS_ENABLED=false
PILOT_ACCESS_PASSWORD=

# Admin metrics panel
ADMIN_METRICS_PASSPHRASE=
```

### WiGLE API Setup

1. Create a free account at [wigle.net](https://wigle.net)
2. Accept the API terms at `wigle.net/account`
3. Copy your API Name and API Token into `.env`
4. In the sidebar: enable WiGLE → enter coordinates → Fetch

Without a WiGLE key, the app operates in mock mode — all views, selectors, and enrichment work with generated data.

---

## Views

### WiGLE Heatmap
Signal density overlay with temporal filter (date range slider). Toggle WiGLE layer independently from camera layers.

### Selector View
Main ISR workflow. Enter a selector value (e.g. `xfinitywifi`, a BSSID, or an IP fragment) and the app:
1. Filters WiGLE observations matching the selector
2. Detects co-located networks within ~1 km
3. Queries Shodan for exposed devices near the observation centroid
4. Queries Overpass for nearby points of interest
5. Searches Telegram public channels for keyword mentions
6. Computes movement velocity and flags anomalies
7. Renders entity co-occurrence ranked table
8. Provides one-click HTML + CSV export at the bottom

### Globe / Flat Map / Heatmap
Standard WRAITH camera OSINT views — multi-layer CSV upload, staleness classification, coordinate normalization.

---

## Intel Report Export

The **Export Intelligence Report** section appears at the bottom of the Selector view when filtered observations exist.

- **Download HTML Report** — self-contained dark-theme HTML with:
  - KPI summary row (observation count, co-located networks, anomalies, Shodan devices, POIs, Telegram mentions)
  - Full observations table
  - Co-location table
  - Movement analysis with anomaly summary
  - Shodan devices (if queried this session)
  - OSM POIs (if queried this session)
  - Telegram mentions (if searched this session)
  - Filename: `wraith_intel_{selector}_{date}.html`

- **Download CSV** — raw filtered observations
  - Filename: `wraith_obs_{selector}_{date}.csv`

The HTML report is fully self-contained — no external CSS, no CDN. Opens in any browser, works offline.

---

## Dependency Notes

```
folium==0.17.0    # pinned — HeatMap serialization regression in later versions
branca==0.7.2     # pinned — paired with folium
```

Do not upgrade the folium/branca pair without testing HeatMap layer serialization.

Jinja2 is already installed as a Streamlit dependency — no separate install needed.

---

## Security & Ethics

- **Passive OSINT only** — no active scanning, no unauthorized network access
- **Free/open sources only** — WiGLE (non-commercial), Shodan (free tier), OSM (ODbL), Telegram (public channels)
- **`.env` is gitignored** — never commit API keys
- **Local-first by default** — no data leaves your machine unless you configure a hosted deployment
- Data handling must respect WiGLE non-commercial terms and OpenStreetMap ODbL license

---

## WRAITH Suite

| App | Focus | Status |
|-----|-------|--------|
| WRAITH-WiGLE | OSINT monitoring — wireless selector tracking, ISR pattern analysis | Active (v0.2) |
| WRAITH-Sentinel | Real-time operational watch — alerts, TAK integration, APScheduler | Concept ([docs/WRAITH-SENTINEL-CONCEPT.md](docs/WRAITH-SENTINEL-CONCEPT.md)) |

---

## Roadmap

### Shipped

- v0.1 WiGLE Core — ingestion, heatmap, selector tracking, Shodan, OSM, Telegram, velocity, entity graph
- v0.2 Intel Export — HTML ISR report + CSV export from Selector view

### Deferred (pending API key strategy)

- v0.3 IP Reputation — AbuseIPDB + GreyNoise + Censys cross-reference layer

---

## Version

`v0.2.0` — April 2026

---

*WRAITH-WiGLE is part of the WRAITH suite by [Virtuvman](https://github.com/Virtuvman)*
