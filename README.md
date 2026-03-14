# WRAITH

**W**ide-area **R**econnaissance & **A**sset **I**ntelligence **T**racking **H**ub

WRAITH is a local-first Streamlit application for ingesting camera OSINT datasets, normalizing coordinates, classifying staleness, and visualizing results on globe/map views for analyst workflows.

---

## What WRAITH does

- Loads one or more CSV files as independent map layers
- Normalizes coordinate formats (decimal, combined, MGRS, DMS, UTM)
- Classifies camera record freshness using `last_seen`
- Renders:
  - Globe (orthographic)
  - Flat map
  - Heatmap (with basemap controls)
- Exports combined CSV + BLUF summaries
- Surfaces coordinate conflicts for correction

---

## Repository layout

```text
.
├── app.py                           # Streamlit entrypoint
├── modules/
│   ├── ingestion.py                 # CSV ingestion + parsing flow
│   └── coord_normalizer.py          # Coordinate normalization
├── scripts/
│   └── generate_poc_global_dataset.py
├── data/                            # Sample and generated datasets
├── docs/                            # Plans, scenarios, templates, session notes
├── requirements.txt
├── env.example
└── .gitignore
```

---

## Quick start (Windows / VS Code)

### 1) Create and activate virtual environment

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 2) Install dependencies

```cmd
pip install -r requirements.txt
```

### 3) Run WRAITH

```cmd
streamlit run app.py
```

If port `8501` is busy:

```cmd
streamlit run app.py --server.port 8502
```

---

## Data workflow

### Option A — Use included sample data

- `sample_cameras.csv`
- `sample_cameras_decimal.csv`
- `sample_cameras_combined.csv`
- `data/poc_global_500.csv`

### Option B — Generate PoC global dataset

```cmd
python scripts\generate_poc_global_dataset.py
```

Outputs:
- `data/poc_global_500.csv`
- `poc_global_500.csv`
- optional `.xlsx` files if Excel engine is available

### Option C — External source ingest

External API-based ingestion is currently disabled by default.

For now, use CSV imports and local generation workflows only.

---

## Docs index

- `WRAITH_MASTER_PLAN.md` — high-level roadmap and standards
- `docs/MASTER_PROMPT.md` — implementation contract / operating style
- `docs/TEST_SCENARIOS.md` — repeatable validation scenarios
- `docs/SESSION_UPDATE_2026-03-14.md` — latest session summary
- `docs/templates/` — reusable templates for features, API integrations, QC

---

## Security and ethics

- Passive OSINT workflow only
- No active scanning, no unauthorized access
- Keep `.env` private (ignored by git)
- Rotate API keys if exposed

---

## Current status

- Heatmap detail controls added (basemap, clustering, minimap, sizing)
- Heatmap serialization crash fixed by removing explicit custom gradient
- Dataset generator now dependency-light (no hard pandas requirement)
