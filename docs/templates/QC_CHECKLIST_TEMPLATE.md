# QC Checklist Template (Per Feature/Branch)

Use this checklist before merging.

---

## Feature / Branch

- Feature name:
- Branch:
- Tester:
- Date:

## 1) Setup Validation

- [ ] `python --version` confirmed
- [ ] Virtual environment activated
- [ ] `pip install -r requirements.txt` completed
- [ ] App starts successfully

## 2) Functional Validation

- [ ] Expected feature behavior works
- [ ] No regressions observed in core flow
- [ ] UI text/instructions are clear for beginner users

## 3) Failure-Mode Validation

- [ ] Invalid input handled with clear message
- [ ] Missing required fields handled safely
- [ ] App remains stable after recoverable errors

## 4) Data Validation

- [ ] Output data schema matches expectation
- [ ] Export files open and contain expected fields
- [ ] Example/persona data runs successfully

## 5) Documentation Validation

- [ ] Setup steps are complete and in correct order
- [ ] Run commands are copy/paste ready
- [ ] Troubleshooting section includes known issues

## 6) Security / Ethics Validation

- [ ] No secrets hard-coded in source
- [ ] Ethical-use warning present where appropriate
- [ ] Logging avoids sensitive data exposure

## 7) Final Decision

- [ ] PASS — ready to merge
- [ ] FAIL — fix required

### Notes / Findings

- 
