# Implementation Plan

[Overview]
Deliver a COA 2 proof-of-concept by introducing a mobile client and a shared API layer that reuses WRAITH’s existing Python business logic without breaking the current Streamlit app.

This implementation adds a mobile-ready architecture while preserving current analyst workflows in `app.py`. Today, WRAITH is a Streamlit monolith that combines UI rendering, file ingestion orchestration, staleness classification, and reporting/export logic in one app entrypoint, with reusable parsing/classification modules in `modules/`. For the mobile POC, the design goal is not to rewrite WRAITH functionality, but to separate it into stable backend services and independent clients.

The POC scope includes: (1) extraction of API endpoints for ingest, staleness analysis, conflicts, KPIs, and BLUF; (2) creation of a mobile client shell (React Native/Expo recommended) that consumes these endpoints; and (3) parity checks between Streamlit and mobile output using the same sample datasets. Per user direction, `WRAITH_QR.png` is treated as static branding in Phase 1 (no deep-link or scanner behavior yet), while architecture will include extension points for a follow-on NFC-tag workflow.

The existing Streamlit application remains operational and unchanged for pilot users, minimizing migration risk. Core transformation logic remains centralized in Python (`modules/ingestion.py`, `modules/coord_normalizer.py`, `modules/staleness.py`) and is invoked by both Streamlit and mobile-facing API routes.

[Types]
Introduce explicit API contracts so web/mobile clients receive deterministic schemas from shared backend services.

### Domain Types (Python / Pydantic)

1. `CoordinateDetectionInfo`
   - `format: Literal["decimal","combined","dms","mgrs","utm","unknown"]`
   - `lat_column: Optional[str]`
   - `lon_column: Optional[str]`
   - `column: Optional[str]`
   - Validation: `format` required; optional fields present only for applicable formats.

2. `IngestError`
   - `row_index: int` (>= 0)
   - `format_detected: str`
   - `reason: str`
   - `raw_values: dict[str, str]`

3. `CameraRecord`
   - Existing normalized WRAITH fields:
     - `ip: str`
     - `latitude: float` (range -90..90)
     - `longitude: float` (range -180..180)
     - `device_type: str`
     - `model: str`
     - `location_label: str`
     - `last_seen: str`
     - `port: str`
     - `org: str`
     - `country: str`
     - `region: str`
     - `poc_batch: str`
   - Derived fields:
     - `staleness_status: Literal["CURRENT","REVIEW","STALE","EXPIRED"]`
     - `color_hex: str`
     - `color_class: Literal["green","yellow","orange","red"]`
     - `age_days: int`
     - `age_months: float`

4. `IngestResponse`
   - `source_file: str`
   - `detection_info: CoordinateDetectionInfo`
   - `total_rows_ingested: int`
   - `total_rows_parsed: int`
   - `parse_success_pct: float`
   - `records: list[CameraRecord]`
   - `errors: list[IngestError]`

5. `KpiSummary`
   - `total: int`
   - `current: int`
   - `review: int`
   - `stale: int`
   - `expired: int`
   - `regions: int`
   - `layers: int`

6. `BlufResponse`
   - `generated_on: date`
   - `summary_text: str`
   - `expired_locations: list[str]`
   - `stale_locations: list[str]`

7. `MobileFeatureFlags`
   - `qr_enabled: bool` (Phase 1 default: `false`)
   - `nfc_enabled: bool` (Phase 1 default: `false`)
   - `offline_cache_enabled: bool` (Phase 1 optional)

[Files]
Implement backend/API and mobile POC scaffolding while preserving existing Streamlit files.

### New files to be created

- `backend_api/main.py`
  - FastAPI app entrypoint, route registration, health endpoint.
- `backend_api/schemas.py`
  - Pydantic request/response models (types above).
- `backend_api/services/ingest_service.py`
  - Wraps `modules.ingestion.load_csv()` and maps output to schemas.
- `backend_api/services/staleness_service.py`
  - Wraps `modules.staleness.apply_staleness()` and aggregation helpers.
- `backend_api/services/report_service.py`
  - BLUF and KPI builders for API consumption.
- `backend_api/routers/ingest.py`
  - Upload/ingest endpoint(s).
- `backend_api/routers/metrics.py`
  - KPI/summary endpoints.
- `backend_api/routers/reports.py`
  - BLUF and export-oriented endpoints.
- `backend_api/config.py`
  - Environment/config loading for API service.
- `mobile_app/` (React Native Expo app root)
  - `App.tsx`, navigation, screen modules, API client module.
- `mobile_app/src/screens/HomeScreen.tsx`
  - KPI summary + layer summary cards.
- `mobile_app/src/screens/UploadScreen.tsx`
  - File upload flow (Phase 1 may rely on preloaded/pilot datasets).
- `mobile_app/src/screens/MapScreen.tsx`
  - Initial map/markers rendering.
- `mobile_app/src/screens/ConflictsScreen.tsx`
  - Conflict list and row-level detail.
- `mobile_app/src/screens/ReportsScreen.tsx`
  - BLUF preview + export trigger.
- `mobile_app/src/assets/WRAITH_QR.png`
  - Static branding image surfaced in About/Welcome screen.
- `docs/MOBILE_POC_ARCHITECTURE.md`
  - Architecture diagram and endpoint map.
- `docs/NFC_FOLLOW_ON_PLAN.md`
  - Follow-on design for NFC tag interactions.

### Existing files to be modified

- `requirements.txt`
  - Add API dependencies (`fastapi`, `uvicorn`, `pydantic`, `python-multipart`).
- `README.md`
  - Add backend API run instructions and mobile POC setup.
- `env.example`
  - Add API and mobile-compatible environment keys (base URL, JWT placeholders, feature flags).
- `app.py`
  - Optional minimal refactor to call shared service helpers rather than inline-only logic, while preserving current UI behavior.
- `modules/ingestion.py`
  - Optional small adjustments for service-level invocation consistency; preserve function signatures where possible.
- `modules/staleness.py`
  - Preserve logic; expose helper-level functions if needed for API summary endpoints.

### Files to be deleted or moved

- No deletions in POC phase.
- Copy/mirror `WRAITH_QR.png` into mobile assets for packaging consistency.

### Configuration file updates

- Add `.env` keys for:
  - `API_HOST`, `API_PORT`
  - `MOBILE_FEATURE_QR_ENABLED=false`
  - `MOBILE_FEATURE_NFC_ENABLED=false`
  - `MOBILE_API_BASE_URL`

[Functions]
Add API-oriented functions and minimally adapt existing functions for reuse.

### New functions

- `create_app() -> FastAPI` in `backend_api/main.py`
  - Purpose: initialize app and attach routers.
- `ingest_csv_file(file: UploadFile) -> IngestResponse` in `backend_api/services/ingest_service.py`
  - Purpose: parse CSV and return normalized + staleness-enriched payload.
- `build_kpi_summary(records: list[CameraRecord]) -> KpiSummary` in `backend_api/services/staleness_service.py`
  - Purpose: generate KPI aggregate for clients.
- `build_bluf(records: list[CameraRecord], source_files: list[str]) -> BlufResponse` in `backend_api/services/report_service.py`
  - Purpose: API-safe BLUF output.
- `map_ingest_errors(errors: list[dict]) -> list[IngestError]` in `backend_api/services/ingest_service.py`
  - Purpose: strict schema mapping and validation.

### Modified functions

- `load_csv(uploaded_file)` in `modules/ingestion.py`
  - Required changes: keep return shape stable, ensure API-safe typing compatibility.
- `apply_staleness(df)` in `modules/staleness.py`
  - Required changes: none to logic; optionally expose strict type hints for downstream service use.
- `generate_bluf(files_dict, active_names, status_filter)` in `app.py`
  - Required changes: optionally extract internals into shared helper to avoid duplication.

### Removed functions

- No removals planned in POC phase.
- Migration strategy: deprecate only after parity validation and explicit user sign-off.

[Classes]
Introduce schema/model classes for backend contracts and client DTOs, with no destructive changes to current app structure.

### New classes

- Pydantic model classes in `backend_api/schemas.py`:
  - `CoordinateDetectionInfoModel`
  - `IngestErrorModel`
  - `CameraRecordModel`
  - `IngestResponseModel`
  - `KpiSummaryModel`
  - `BlufResponseModel`
  - `FeatureFlagsModel`

- Mobile data model interfaces/types (TypeScript) in `mobile_app/src/types/api.ts`:
  - `CameraRecord`
  - `KpiSummary`
  - `IngestResponse`
  - `BlufResponse`

### Modified classes

- None in existing Python modules (current architecture is function-oriented).

### Removed classes

- None.

[Dependencies]
Add backend API and mobile toolchain dependencies while preserving current Streamlit runtime.

### Python/backend additions

- `fastapi` (API framework)
- `uvicorn[standard]` (ASGI server)
- `pydantic` (schema validation)
- `python-multipart` (file uploads)

### Mobile additions (React Native/Expo)

- `expo`
- `react-native`
- `@react-navigation/native` (+ stack/tab dependencies)
- `axios` (API client)
- map dependency (e.g., `react-native-maps`)

### Version/integration notes

- Keep existing Streamlit and pandas versions pinned as-is for MVP stability.
- Introduce API dependencies in a backward-compatible way so `streamlit run app.py` remains unaffected.

[Testing]
Use parity-driven testing to confirm API/mobile behavior matches current Streamlit outputs and preserves analyst workflow correctness.

### Test requirements

- New backend tests:
  - `tests/test_ingest_api.py`
  - `tests/test_staleness_api.py`
  - `tests/test_reports_api.py`
- Validation with datasets:
  - `sample_cameras.csv`
  - `sample_cameras_decimal.csv`
  - `sample_cameras_combined.csv`
  - `data/poc_global_500*.csv`

### Existing test/doc modifications

- Update `docs/TEST_SCENARIOS.md` to include:
  - API ingest parity scenario
  - Mobile KPI parity scenario
  - QR branding-only verification scenario (Phase 1)
  - NFC follow-on placeholder scenario (disabled feature flag)

### Validation strategy

1. Compare Streamlit KPI totals vs API totals on same dataset.
2. Compare conflict counts and rows between Streamlit and API responses.
3. Compare BLUF text totals and key action language.
4. Verify mobile screens render API outputs without schema drift.
5. Verify `WRAITH_QR.png` displays as static branding in mobile app.

[Implementation Order]
Sequence changes from lowest-risk backend extraction to mobile parity validation and documentation hardening.

1. Scaffold API project (`backend_api/`) and add typed schemas.
2. Implement ingest + staleness service wrappers using existing `modules/*` logic.
3. Add KPI and BLUF/report API endpoints.
4. Add API tests and parity checks against Streamlit outputs.
5. Scaffold mobile app and implement API client + navigation shell.
6. Implement mobile screens (Home, Upload, Map, Conflicts, Reports).
7. Add `WRAITH_QR.png` as static branding asset in mobile UI.
8. Add feature flags for future QR/NFC functionality (disabled in POC).
9. Update docs (`README.md`, architecture doc, NFC follow-on plan).
10. Execute end-to-end pilot validation and produce release checklist.
