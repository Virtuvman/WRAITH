# WRAITH Test Scenarios (Beginner-Friendly)

Use these scenarios to validate core behavior before demos or GitHub push.

---

## Scenario 1 — Happy Path CSV Load

**Objective:** confirm normal ingest + map render works.

Steps:
1. Run app: `streamlit run "app (2).py"`
2. Upload `sample_cameras.csv`
3. Open Globe, Flat Map, Data Table panels.

Expected result:
- Rows load successfully.
- KPI cards show totals.
- Points appear on globe/map.
- No critical errors displayed.

---

## Scenario 2 — Mixed Coordinate Format Support

**Objective:** verify coordinate format detection and normalization.

Steps:
1. Upload one valid decimal CSV.
2. Upload one CSV using combined `lat/lon` style values.
3. Confirm format badges are shown in UI.

Expected result:
- Both files load.
- Detection badges display appropriate format names.
- Coordinates plot correctly.

---

## Scenario 3 — Conflict Handling (Failure Path)

**Objective:** ensure bad coordinates are safely surfaced.

Steps:
1. Prepare a CSV with some invalid coordinates.
2. Upload file.
3. Open Conflicts panel.

Expected result:
- App does not crash.
- Conflict count/banner appears.
- Invalid rows can be exported for correction.

---

## Scenario 4 — Staleness Classification

**Objective:** verify Fresh/Stale/Expired logic.

Steps:
1. Use records with recent, mid-age, and old `last_seen` dates.
2. Check KPI counts and row status labels.
3. Filter by status in sidebar.

Expected result:
- Date bands classify correctly:
  - `< 3 months` → FRESH
  - `3–6 months` → STALE
  - `> 6 months` → EXPIRED

---

## Scenario 5 — BLUF and Export Validation

**Objective:** validate reporting outputs.

Steps:
1. Open “Alerts & Export” panel.
2. Generate BLUF text.
3. Download BLUF + CSV exports.

Expected result:
- BLUF includes totals and action language.
- Files download and open cleanly.
