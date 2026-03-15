# WRAITH

**W**ide-area **R**econnaissance & **A**sset **I**ntelligence **T**racking **H**ub

WRAITH is a local-first Streamlit application for ingesting camera OSINT datasets, normalizing coordinates, classifying staleness, and visualizing results on globe/map views for analyst workflows.

---

## What WRAITH does

- Loads one or more CSV files as independent map layers
- Normalizes coordinate formats (decimal, combined, MGRS, DMS, UTM)
- Classifies camera record freshness using `last_seen`
  - `CURRENT` (<90 days)
  - `REVIEW` (90–180 days)
  - `STALE` (180–360 days)
  - `EXPIRED` (>360 days)
- Renders:
  - Globe (orthographic)
  - Flat map
  - Heatmap (with basemap controls)
- Exports combined CSV + BLUF summaries
- Surfaces coordinate conflicts for correction
- Tracks collection refresh timelines by `poc_batch`

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
- `data/poc_global_500_v2.csv`
- `data/poc_global_500_v3.csv`
- `data/poc_global_500_v4.csv`
- `data/poc_global_500_v5.csv`

### Option B — Generate PoC global dataset

```cmd
python scripts\generate_poc_global_dataset.py
```

Outputs:
- `data/poc_global_500.csv`
- `poc_global_500.csv`
- `data/poc_global_500_v2.csv`
- `data/poc_global_500_v3.csv`
- `data/poc_global_500_v4.csv`
- `data/poc_global_500_v5.csv`
- optional `.xlsx` files if Excel engine is available

### Option C — External source ingest

External API-based ingestion is currently disabled by default.

For now, use CSV imports and local generation workflows only.

---

## MVP behavior notes (v0.2 baseline)

- **Regions KPI** counts unique geographic values from the `region` column.
- **Layers KPI** counts active uploaded files/layers.
- **Collection Schedule** appears in **Alerts & Export**, grouped by `poc_batch` with:
  - oldest `last_seen`
  - age in days
  - countdown to 90 / 180 / 360 day thresholds
- BLUF language and top alerts align to the 4-tier staleness model.

---

## MVP quality check commands

```cmd
python -m py_compile app.py modules\staleness.py modules\ingestion.py scripts\generate_poc_global_dataset.py
python scripts\generate_poc_global_dataset.py
streamlit run app.py
```

---

## GitHub push workflow (recommended)

```cmd
git pull --rebase origin main
git add app.py modules/staleness.py modules/ingestion.py README.md CHANGELOG.md env.example wraith_logo.svg "WRAITH Logo.png"
git commit -m "MVP: 4-tier staleness, region/layer KPIs, collection schedule"
git push origin main
```

Optional safer release flow:

```cmd
git checkout -b release/mvp-0.2.0
git push -u origin release/mvp-0.2.0
```

Then open a PR to `main`.

---

## Share and publish to select colleagues

1. Keep repository **Private**.
2. Add colleagues via **Settings → Collaborators**.
3. Create a GitHub release tag (example: `v0.2.0-mvp`) with notes + screenshots.
4. Share an onboarding snippet:
   - clone URL
   - setup commands
   - expected sample run (`data/poc_global_500.csv`)
5. Collect first-user feedback and log in `CHANGELOG.md` / `docs/SESSION_UPDATE_*`.

---

## Docs index

- `WRAITH_MASTER_PLAN.md` — high-level roadmap and standards
- `docs/MASTER_PROMPT.md` — implementation contract / operating style
- `docs/TEST_SCENARIOS.md` — repeatable validation scenarios
- `docs/SESSION_UPDATE_2026-03-14.md` — latest session summary
- `docs/PILOT_ONBOARDING.md` — trial onboarding for non-GitHub peers
- `docs/PILOT_FEEDBACK_TEMPLATE.md` — structured pilot feedback intake template
- `docs/templates/` — reusable templates for features, API integrations, QC

---

## Security and ethics

- Passive OSINT workflow only
- No active scanning, no unauthorized access
- Keep `.env` private (ignored by git)
- Rotate API keys if exposed

### Admin Metrics Access

- WRAITH includes an admin-only **Metrics** panel for usage and ingest statistics.
- Configure passphrase in `.env`:

```env
ADMIN_METRICS_PASSPHRASE=WRAITH_TRIAL_2026!
```

- In the sidebar, unlock via **Admin Access → Metrics passphrase**.
- When unlocked, a `Metrics` panel appears in View navigation.

### Pilot Front-Door App Protection (Recommended for hosted trials)

WRAITH includes an optional full-app password gate for pilot deployments.

- Streamlit Cloud → **App Settings → Secrets**:

```toml
PILOT_ACCESS_PASSWORD = "WRAITH_TRIAL_2026!"
PILOT_ACCESS_ENABLED = true
PILOT_LOCKOUT_SECONDS = 15
```

- Behavior:
  - Users must pass front-door password before any app UI loads.
  - After 3 failed attempts, a short cooldown lockout applies.
  - `Lock Session` button in sidebar clears access for current session.

You can disable the gate for local/offline debugging with:

```env
PILOT_ACCESS_ENABLED=false
```

### Logo / Branding

- Place logo assets in project root:
  - `wraith_logo.svg` (inline header logo)
  - `wraith_logo.png` (preferred favicon/tab icon)
- App behavior:
  - `page_icon` uses `wraith_logo.png` first, then `wraith_logo.svg`, then `👻` fallback.
  - Header logo renders inline from `wraith_logo.svg` when present.
- If favicon does not update immediately, hard-refresh the browser cache.

### Optional Splash Background

You can enable a full-page splash/dashboard background image in Streamlit.

1. Add image file (example):
   - `assets/wraith_splash.png`
2. In `.env`:

```env
ENABLE_SPLASH=true
SPLASH_BACKGROUND_PATH=assets/wraith_splash.png
SPLASH_OVERLAY_ALPHA=0.58
```

Notes:
- `SPLASH_OVERLAY_ALPHA` controls readability overlay (0.0–0.9).
- If the image path is missing/invalid, WRAITH falls back safely to normal background.
- Recommended: optimize splash image size (compressed PNG/WebP) for faster load.

---

## Current status

- Heatmap detail controls added (basemap, clustering, minimap, sizing)
- Heatmap serialization crash fixed by removing explicit custom gradient
- Dataset generator now dependency-light (no hard pandas requirement)
