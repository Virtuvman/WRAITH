# Implementation Task Handoff

Refer to @implementation_plan.md for a complete breakdown of the task requirements and steps. You should periodically read this file again.

## Objective
Implement the COA 2 mobile POC by introducing a shared Python API backend and a separate mobile app client while keeping current Streamlit behavior operational.

## Constraints and Decisions
1. Preserve current `app.py` Streamlit user experience for existing pilot users.
2. Reuse existing business logic in:
   - `modules/ingestion.py`
   - `modules/coord_normalizer.py`
   - `modules/staleness.py`
3. Treat `WRAITH_QR.png` as static branding only for Phase 1.
4. Include extension points for NFC follow-on work behind feature flags.
5. Validate parity between Streamlit outputs and API/mobile outputs.

## Plan Document Navigation Commands
Use these commands to inspect targeted sections:

```cmd
:: Read Overview section
powershell -NoProfile -Command "Get-Content implementation_plan.md | Select-String -Pattern '^\[Overview\]','^\[Types\]' -Context 0,200 | ForEach-Object { $_.Line }"

:: Read Types section
powershell -NoProfile -Command "Get-Content implementation_plan.md | Select-String -Pattern '^\[Types\]','^\[Files\]' -Context 0,300 | ForEach-Object { $_.Line }"

:: Read Files section
powershell -NoProfile -Command "Get-Content implementation_plan.md | Select-String -Pattern '^\[Files\]','^\[Functions\]' -Context 0,300 | ForEach-Object { $_.Line }"

:: Read Functions section
powershell -NoProfile -Command "Get-Content implementation_plan.md | Select-String -Pattern '^\[Functions\]','^\[Classes\]' -Context 0,300 | ForEach-Object { $_.Line }"

:: Read Classes section
powershell -NoProfile -Command "Get-Content implementation_plan.md | Select-String -Pattern '^\[Classes\]','^\[Dependencies\]' -Context 0,300 | ForEach-Object { $_.Line }"

:: Read Dependencies section
powershell -NoProfile -Command "Get-Content implementation_plan.md | Select-String -Pattern '^\[Dependencies\]','^\[Testing\]' -Context 0,300 | ForEach-Object { $_.Line }"

:: Read Testing section
powershell -NoProfile -Command "Get-Content implementation_plan.md | Select-String -Pattern '^\[Testing\]','^\[Implementation Order\]' -Context 0,300 | ForEach-Object { $_.Line }"

:: Read Implementation Order section
powershell -NoProfile -Command "Get-Content implementation_plan.md | Select-String -Pattern '^\[Implementation Order\]' -Context 0,300 | ForEach-Object { $_.Line }"
```

## Implementation Notes
1. Create `backend_api/` first and verify service wrappers around existing modules.
2. Add schema validation before wiring routes.
3. Add API tests before mobile integration.
4. Scaffold `mobile_app/` and consume API only (no duplicated business logic).
5. Add QR asset (`WRAITH_QR.png`) to mobile assets and display on About/Welcome screen.
6. Keep QR/NFC functionality disabled in Phase 1 via feature flags.

## task_progress Items:
- [ ] Step 1: Scaffold `backend_api/` with typed schemas and shared service wrappers
- [ ] Step 2: Implement ingest, metrics, and BLUF API routes with tests
- [ ] Step 3: Validate parity between Streamlit and API outputs on sample datasets
- [ ] Step 4: Scaffold `mobile_app/` and implement core screens + API client
- [ ] Step 5: Add `WRAITH_QR.png` static branding and disable QR/NFC feature flags
- [ ] Step 6: Update docs and run end-to-end pilot validation checklist
