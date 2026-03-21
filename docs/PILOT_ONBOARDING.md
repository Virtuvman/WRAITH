use ## WRAITH Peer Pilot Onboarding (Non-GitHub Users)

This guide is for trusted peers participating in the private WRAITH MVP trial.

---

### 1) Access

- Pilot URL: `<YOUR_DEPLOYMENT_URL>`
- Temporary passphrase: `WRAITH_TRIAL_2026!`
- Trial window: `<START_DATE>` to `<END_DATE>`

> Do not share URL or passphrase outside the pilot group.

---

### 2) 5-minute validation flow

1. Open WRAITH URL.
2. Upload `data/poc_global_500.csv` (or provided sample CSV).
3. Confirm KPIs render at top:
   - Total Cameras
   - Current / Review / Stale / Expired
   - Regions
   - Layers
4. Switch between:
   - Globe
   - Flat Map
   - Heatmap
5. Open **Alerts & Export**:
   - Review BLUF summary
   - Review Collection Schedule table (`poc_batch` grouped)
   - Test CSV/TXT exports

---

### 3) What feedback we need

- Was the workflow understandable without help?
- What slowed you down most?
- Any map/KPI/filters confusing or misleading?
- Did exports contain what you expected?
- What single improvement would provide most value?

Use the feedback template in `docs/PILOT_FEEDBACK_TEMPLATE.md`.

---

### 4) Data handling for pilot

- Use sanitized / PoC datasets only.
- Do not upload sensitive operational data.
- Do not distribute exported data outside pilot participants.
