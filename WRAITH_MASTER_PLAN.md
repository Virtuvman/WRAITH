# WRAITH — Wide-area Reconnaissance & Asset Intelligence Tracking Hub
## MASTER PLAN v3.0 (Master Prompt Aligned)
### Status: ACTIVE | Owner: Virtuvman | Repo: https://github.com/Virtuvman

---

## 1) Mission + Operating Context

WRAITH is a local-first, CSV-driven OSINT/PAI monitoring dashboard for camera intelligence lifecycle tracking.

**Primary mission:**
- ingest exported records,
- normalize coordinates,
- classify record staleness,
- visualize activity on token-free maps,
- and support analyst decision-making with BLUF outputs.

**Guardrails:**
- Passive analysis only (no active scanning, no stream access).
- Local processing first.
- Clear ethical-use boundaries documented.

---

## 2) Master Prompt Implementation Contract (How we build)

This project now follows these default build rules:

1. **Beginner-first instructions**
   - No assumed engineering knowledge.
   - Every implementation branch includes step-by-step setup, run, test, and rollback notes.

2. **Plan-first execution**
   - Start with markdown plan + branch breakdown before major code changes.
   - Clarify ambiguous/high-impact decisions before execution.

3. **Default stack preference**
   - Python + Streamlit + VS Code.
   - Vercel only for non-Streamlit front-ends.
   - Cline/ROO-friendly markdown workflows.

4. **API clarity standard**
   - For each API integration: purpose, auth model, endpoints, rate limits, request/response examples, errors, and recovery strategy.

5. **QC-by-design**
   - Include sample personas + test docs.
   - Include validation checklists and acceptance criteria for each branch.

6. **Devil’s-advocate review**
   - Each branch contains a “Risks + Countermeasures” section.

7. **GitHub-ready handoff**
   - Keep docs and structure ready for push to `https://github.com/Virtuvman`.

---

## 3) Current Architecture Snapshot

Existing core files in use:
- `app.py` (primary Streamlit implementation)
- `modules/ingestion.py` (CSV loading + coordinate parsing orchestration)
- `modules/coord_normalizer.py` (coordinate normalization utilities)
- `sample_cameras.csv` (base demo dataset)

Recommended near-term normalization:
- app entrypoint now standardized to `app.py`,
- keep `modules/` as core analytics/transform layer,
- keep docs in `/docs` and templates in `/docs/templates`.

---

## 4) Branch-Based Roadmap (Detailed, beginner-ready)

### Branch A — `docs/master-prompt-foundation`
**Goal:** Persist the Master Prompt and operating contract in-repo.

Tasks:
1. Create `docs/MASTER_PROMPT.md`.
2. Define role assumptions, communication style, and execution defaults.
3. Add “when to ask clarifying questions” rubric.
4. Add handoff standards for GitHub commits/PRs.

Exit criteria:
- New contributors can understand project expectations without chat history.

---

### Branch B — `docs/implementation-templates`
**Goal:** Add reusable templates for fast, consistent build execution.

Tasks:
1. Add API integration template.
2. Add feature planning template.
3. Add QC checklist template.
4. Add branch execution checklist.

Exit criteria:
- Every future feature can be started from a template with no guesswork.

---

### Branch C — `test-assets/persona-and-qc-data`
**Goal:** Build repeatable test inputs for demos and validation.

Tasks:
1. Add persona data file(s) for analyst/operator workflows.
2. Add test scenarios for happy path + failure path.
3. Add expected outputs for quality control.

Exit criteria:
- Demos and validation can be reproduced in any environment.

---

### Branch D — `app/refactor-entrypoint-and-readme`
**Goal:** Improve onboarding and consistency.

Tasks:
1. Document run commands clearly.
2. Add beginner setup checklist.
3. Keep `app.py` as the canonical app entrypoint.
4. Confirm dependencies align with requirements and imports.

Exit criteria:
- A beginner can run app locally in <15 minutes using docs alone.

---

## 5) API Integration Standard (Mandatory)

For any new API use, include:
- API purpose and why selected,
- auth method (token/key/OAuth),
- endpoint table,
- rate-limit policy + retry strategy,
- request/response examples,
- common errors + handling,
- logging and fallback behavior.

---

## 6) Quality & Risk Model

### Quality checks per branch
- [ ] Installation steps tested on clean environment
- [ ] Core user workflow tested end-to-end
- [ ] Failure mode test captured (bad CSV, missing columns, invalid coords)
- [ ] Documentation updated
- [ ] Output export validated (CSV/BLUF)

### Devil’s-advocate checks
- Could this create legal/ethical ambiguity?
- Could data be misinterpreted due to stale timestamps?
- Are “unknown/invalid” coordinate rows safely surfaced?
- Is operator warned before acting on incomplete data?

---

## 7) Deployment Notes

Preferred path:
1. Local dev (`streamlit run app.py`)
2. Repo hardening + docs polish
3. Streamlit Cloud for POC demo
4. Optional containerization for team distribution

---

## 8) Changelog

| Version | Date       | Change |
|---------|------------|--------|
| 1.0 | 2026-03-14 | Initial WRAITH plan created |
| 2.0 | 2026-03-14 | CAMWATCH renamed to WRAITH |
| 3.0 | 2026-03-14 | Plan aligned to Master Prompt workflow (beginner-first + branch-based + QC templates) |

---

## 9) Next Actions (Actionable Order)

1. [x] Persist Master Prompt expectations in-repo
2. [x] Add implementation templates for features/APIs/QC
3. [x] Add persona and scenario test artifacts
4. [ ] Execute Branch D onboarding cleanup (`README.md`, optional `app.py` normalization)
5. [ ] Run full QA pass and push to GitHub
