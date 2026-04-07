# Milestones

Completed milestone log for WRAITH-WiGLE.

| Milestone | Completed | Duration | Stats |
|-----------|-----------|----------|-------|
| v0.1 WiGLE Core | 2026-04-06 | 2 days | 6 phases, 9 plans, 8 files |
| v0.2 Intel Export | 2026-04-06 | 1 day | 1 phase, 2 plans, 2 files |

---

## ✅ v0.2 Intel Export

**Completed:** 2026-04-06
**Duration:** 1 day (2026-04-06)
**Version:** 0.2.0

### Stats

| Metric | Value |
|--------|-------|
| Phases | 1 |
| Plans | 2 |
| Files created | 1 (modules/report.py) |
| Files modified | 1 (app.py) |

### Key Accomplishments

- **Jinja2 HTML report engine** — Self-contained dark-theme ISR report with inline CSS, KPI row, 6 data sections (observations, co-location, velocity, Shodan, OSM, Telegram), graceful None/empty handling throughout
- **CSV observations export** — One-click filtered observations download, header-only fallback on empty data
- **Session-state enrichment capture** — Shodan/OSM/Telegram results stored to session state on successful query; HTML report automatically includes whatever data the operator loaded during the session
- **Export Intelligence Report UI** — Two-button side-by-side export section at bottom of Selector view; filenames include selector value + date stamp
- **Zero new dependencies** — Jinja2 already installed via Streamlit; no new pip installs required

### Key Decisions

| Decision | Rationale | Phase |
|----------|-----------|-------|
| v0.2 scoped to export only | Freeze complexity until API key strategy defined | 7 |
| Inline CSS only — no CDN | Self-contained report works offline, air-gapped environments | 7 |
| Return string, no file I/O in modules | UI layer controls filename and download; module stays pure | 7 |
| Session-state enrichment capture | Streamlit reruns on every interaction — must persist enrichment between button clicks | 7 |
| Lazy import of report/velocity in UI | Consistent with existing Shodan/OSM/Telegram import style in render_selector_view() | 7 |

---

## v0.1 WiGLE Core

**Completed:** 2026-04-06
**Duration:** 2 days (2026-04-04 — 2026-04-06)
**Version:** 0.1.0

### Stats

| Metric | Value |
|--------|-------|
| Phases | 6 |
| Plans | 9 |
| Files created | 6 (modules/wigle.py, selector.py, shodan.py, osm.py, telegram.py, velocity.py) |
| Files modified | 2 (app.py, env.example) |

### Key Accomplishments

- **WiGLE ingestion pipeline** — HTTP Basic auth API client with mock fallback, session cache, coordinate normalization, and CSV-compatible schema
- **Globe + Heatmap WiGLE overlay** — WiFi/cell/BT signal visualization with encryption-color coding on both Plotly globe and Folium heatmap
- **Selector tracking + temporal filter** — Field/value query (SSID, BSSID, encryption, type, near_camera) with date range slider and co-location detection
- **Shodan cross-reference** — Nearby exposed device search with mock data generator and enrich_with_shodan for batch annotation
- **OSM/Overpass POI enrichment** — Amenity/military/office POI query with session cache and key=value tag parsing
- **Telegram public channel scraping** — Keyword search across DEFAULT_CHANNELS via t.me/s/ web preview, no auth, no new deps
- **Movement velocity + anomaly detection** — Haversine great-circle distance, per-selector velocity computation, 500 km/h anomaly threshold
- **Entity co-occurrence ranking** — coloc_count as edge weight; MVP entity graph without networkx
- **Full Selector ISR chain** — Single view delivers: WiGLE → Co-location → Shodan → OSM → Telegram → Movement → Entity

### Key Decisions

| Decision | Rationale | Phase |
|----------|-----------|-------|
| Mock-first on all modules | All features usable without live API keys | 1–5 |
| Pure data modules (no streamlit) | Clean separation; modules reusable outside UI | 1 |
| Regex over HTMLParser for Telegram | Simpler; t.me/s/ HTML is stable enough | 5 |
| ANOMALY_THRESHOLD_KMH=500 | Below commercial aircraft; catches implausible fixed-device travel | 6 |
| ProgressColumn over background_gradient | matplotlib not installed in WRAITH env | 6 |
| coloc_count as MVP entity graph | No networkx dependency; sufficient for v0.1 operator use | 6 |
| section-label CSS unreliable in sidebar | Replaced with plain bold markdown for Shodan header | 4 |

---
