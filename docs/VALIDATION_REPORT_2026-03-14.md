# WRAITH Validation Report — 2026-03-14

## Scope

Validation run for the requested Step 1–3 execution block:

1. Dependency stabilization (`folium`/`branca` pinning)
2. Entrypoint standardization (`app.py`)
3. Scenario-oriented verification pass

---

## Environment

- OS: Windows 11
- Python: local Python 3.13 interpreter
- Repository: `https://github.com/Virtuvman/WRAITH`

---

## Changes validated

### A) Dependency pinning (Step 1)

`requirements.txt` updated to pin a compatible Folium/Branca pair:

- `folium==0.17.0`
- `branca==0.7.2`

Rationale: reduce recurrence of HeatMap serialization regressions encountered earlier.

### B) Entrypoint normalization (Step 2)

- Renamed app file from `app (2).py` to `app.py`
- Updated docs/references to use `streamlit run app.py`

Files updated for entrypoint consistency:

- `README.md`
- `WRAITH_MASTER_PLAN.md`
- `docs/TEST_SCENARIOS.md`
- `docs/templates/FEATURE_PLAN_TEMPLATE.md`

### C) Automated checks executed (Step 3)

| Check | Command | Status |
|------|---------|--------|
| App syntax check | `python -m py_compile app.py` | ✅ Pass |
| Ingestion module syntax | `python -m py_compile modules\\ingestion.py` | ✅ Pass |
| Dataset generator run | `python scripts\\generate_poc_global_dataset.py` | ✅ Pass |

---

## Scenario matrix (from `docs/TEST_SCENARIOS.md`)

| Scenario | Status | Notes |
|---------|--------|-------|
| Scenario 1 — Happy Path CSV Load | ⚠️ Manual Pending | Requires interactive Streamlit UI validation |
| Scenario 2 — Mixed Coordinate Format Support | ⚠️ Manual Pending | Requires multi-file upload in running app |
| Scenario 3 — Conflict Handling | ⚠️ Manual Pending | Needs crafted invalid-coordinate CSV in UI |
| Scenario 4 — Staleness Classification | ⚠️ Manual Pending | Verify filters and labels visually |
| Scenario 5 — BLUF and Export Validation | ⚠️ Manual Pending | Confirm export outputs from Alerts panel |

---

## Recommended manual completion checklist

1. Run `streamlit run app.py`
2. Execute Scenarios 1–5 from `docs/TEST_SCENARIOS.md`
3. Record pass/fail outcomes and edge notes in this report (append-only)
