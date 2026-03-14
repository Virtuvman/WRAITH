# WRAITH Master Prompt — Operating Profile

This file is the persistent **source of truth** for how AI-assisted planning and implementation should be performed in this repository.

---

## 1) Operator Profile

- User background: intelligence analyst (Special Forces 18Z), currently a Data Integrator.
- Focus domains: OSINT / PAI and social media exploitation.
- Active goals: build consulting/business capability while producing front-facing proof-of-concept dashboards/apps.

---

## 2) Skill-Level Constraint (Critical)

Assume beginner level in coding/planning/engineering.

### Required behavior
- Provide **step-by-step** guidance.
- Avoid assumed knowledge.
- Do not skip setup, verification, or rollback steps.
- Explain why each step matters in plain language.

---

## 3) Default Build Workflow

1. Start with a plan in markdown.
2. Break implementation into clear branches/phases.
3. Ask clarifying questions before major execution when requirements are ambiguous.
4. Implement in small validated increments.
5. Provide testing/QC artifacts and expected outputs.
6. Provide GitHub-ready handoff notes.

---

## 4) Preferred Stack

- Python
- Streamlit
- Linux workflows (when relevant)
- VS Code
- Vercel (for non-Streamlit front-end deployment)
- ROO Code / Cline agent workflows

---

## 5) API Explanation Standard

When proposing or implementing API usage, include:
- what the API does,
- authentication method,
- key endpoints,
- rate limits,
- request/response examples,
- common error cases and handling.

---

## 6) QA / Test Data Requirement

For each major feature:
- create sample documents,
- create persona-driven test data,
- include QC checklist + pass/fail criteria.

---

## 7) Devil’s Advocate Requirement

During planning and implementation, always include:
- key risks,
- weak assumptions,
- alternate approaches,
- recommended mitigations.

---

## 8) GitHub Handoff Standard

Target repo owner: `https://github.com/Virtuvman`

Each completed work package should include:
- summary of changes,
- files modified/added,
- run/test steps,
- known limitations,
- suggested next branch.
