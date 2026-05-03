---
phase: 04-cross-source-enrichment
plan: 01
subsystem: enrichment
tags: [shodan, osm, overpass, requests, pandas, mock-data]

requires:
  - phase: 03-selector-tracking
    provides: modules/selector.py — selector DataFrame schema, SELECTOR_FIELDS, coloc pattern

provides:
  - modules/shodan.py — shodan_host_lookup, shodan_search_near, generate_mock_shodan, enrich_with_shodan, SHODAN_RESULT_COLUMNS
  - modules/osm.py — overpass_pois, clear_osm_cache, OSM_RESULT_COLUMNS, DEFAULT_POI_TAGS, session cache

affects: [04-02-ui-wiring, 06-entity-graph]

tech-stack:
  added: []
  patterns:
    - "Shodan geo query: GET /shodan/search?query=geo:{lat},{lon},{radius_km} — normalize matches list to SHODAN_RESULT_COLUMNS"
    - "Overpass QL: POST to overpass-api.de/api/interpreter, data={data: query}, out center"
    - "Tag parsing: simple tags → node['tag'](...), key=value tags → node['key'='value'](...)"
    - "OSM cache key: (round(lat,3), round(lon,3), int(radius_m)) — prevents duplicate Overpass requests"
    - "enrich_with_shodan: deduplicates coords before API calls to minimize rate-limit exposure"

key-files:
  created: [modules/shodan.py, modules/osm.py]
  modified: []

key-decisions:
  - "Mock-first for both modules — all functionality usable without live API keys"
  - "enrich_with_shodan deduplicates coordinates — avoids repeated Shodan calls for co-located WiGLE observations"
  - "Overpass HTTP timeout = Overpass server timeout + 5s — avoids hanging if server is slow to respond"
  - "OSM cache stored at module level — persists across Streamlit reruns within a session"

patterns-established:
  - "Both modules: pure data, no streamlit — consistent with wigle.py and selector.py pattern"
  - "All functions return empty DataFrame / error dict on failure — never raise"
  - "Mock flag on every public function — enables UI development without API keys"

duration: ~15min
started: 2026-04-05T00:00:00Z
completed: 2026-04-05T00:00:00Z
---

# Phase 4 Plan 01: Cross-Source Enrichment (Data Modules) — Summary

**Shodan IP enrichment and Overpass POI query shipped as pure data modules with mock fallback, session cache, and graceful error handling.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Completed | 2026-04-05 |
| Tasks | 3 of 3 complete (2 auto + 1 checkpoint) |
| Files created | 2 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Shodan Module Imports Clean | Pass | py_compile exit 0 |
| AC-2: Shodan Host Lookup | Pass | mock returns correct dict; missing key returns error dict, never raises |
| AC-3: Shodan Geo Search | Pass | mock=True returns 10-row DataFrame with SHODAN_RESULT_COLUMNS; empty api_key returns empty DataFrame |
| AC-4: OSM POI Query | Pass | overpass_pois returns DataFrame with OSM_RESULT_COLUMNS; bogus coords return empty DataFrame |
| AC-5: OSM Session Cache | Pass | cache_key populated after first call; verified via _osm_cache inspection |

## Accomplishments

- `modules/shodan.py` created — host lookup, geo search, mock generator, enrich_with_shodan with coord deduplication
- `modules/osm.py` created — Overpass QL builder, session cache, key=value tag parsing, timeout separation
- Both modules confirm the pure-data pattern established in Phase 1: no streamlit, graceful degradation, mock flags throughout

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `modules/shodan.py` | Created | Shodan IP/geo enrichment; SHODAN_RESULT_COLUMNS; mock data generator |
| `modules/osm.py` | Created | Overpass POI query; OSM_RESULT_COLUMNS; module-level session cache |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Coord deduplication in enrich_with_shodan | WiGLE observations cluster near cameras — many rows share near-identical coordinates; dedup reduces API calls | Lowers rate-limit exposure; faster on large DataFrames |
| Overpass HTTP timeout = server timeout + 5s | Overpass may be slow to send first byte even within its own timeout; extra buffer avoids premature client-side hang | Robust on slow public servers |
| OSM cache at module level | Persists across Streamlit reruns in same process; avoids repeated Overpass calls during UI interaction | Consistent with wigle.py _session_cache pattern |
| Mock flag on every public function | Enables all UI development and testing without live credentials | Phase 4-02 UI wiring can be built and tested without Shodan key |

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- `shodan_search_near(mock=True)` and `overpass_pois()` are callable from Plan 04-02 immediately
- `enrich_with_shodan` can annotate a wigle_networks DataFrame for display in the Selector view
- `SHODAN_RESULT_COLUMNS` and `OSM_RESULT_COLUMNS` define the display schema for 04-02 tables

**Concerns:**
- Shodan free tier limits: 1 req/sec, 100 results/query, no streaming — `enrich_with_shodan` on a large wigle_networks (>50 unique coords) will be slow without caching. Plan 04-02 should add a Shodan session cache similar to the WiGLE cache in modules/wigle.py.
- Overpass can be intermittently slow during high-load periods — 10s timeout is adequate for operator use but may feel slow on first query.

**Blockers:**
- None

---
*Phase: 04-cross-source-enrichment, Plan: 01*
*Completed: 2026-04-05*
