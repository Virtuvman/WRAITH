# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-03-14

### Added
- Initial `README.md` with setup, workflow, and operations guidance.
- `.gitattributes` for line-ending normalization.
- Validation artifact: `docs/VALIDATION_REPORT_2026-03-14.md`.

### Changed
- Standardized app entrypoint to `app.py` (renamed from `app (2).py`).
- Pinned mapping dependencies to reduce heatmap compatibility issues:
  - `folium==0.17.0`
  - `branca==0.7.2`
- Improved date parsing in `app.py` staleness engine to support multiple date formats and Excel serial dates.
- Updated docs (`README.md`, `WRAITH_MASTER_PLAN.md`, `docs/TEST_SCENARIOS.md`, templates) to reflect `app.py` entrypoint.

### Removed
- Removed active Shodan dependency from `requirements.txt`.
- Removed Shodan API key requirement from `env.example`.
- Removed legacy `shodan_ingest (1).py` script from the active codebase.

### Security
- Kept `.env` out of source control via `.gitignore`.
- Updated messaging to provider-agnostic passive OSINT guidance.
