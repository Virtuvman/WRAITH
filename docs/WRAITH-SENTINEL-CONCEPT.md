# WRAITH-Sentinel — Concept Brief

**Status:** Proposed — not yet in development
**Parent suite:** WRAITH (Wide-area Reconnaissance & Asset Intelligence Tracking Hub)
**Relationship:** Operational companion to WRAITH-WiGLE (OSINT monitoring)

---

## Concept

WRAITH-Sentinel is the real-time alerting and autonomous watch layer of the WRAITH suite. Where WRAITH-WiGLE is an *investigative* tool (operator asks, platform answers), WRAITH-Sentinel is a *sentinel* tool — it watches continuously and tells the operator when something changes.

Sentinel operates on the same data sources and selector primitives as WiGLE, but its job is not analysis — it is **persistent autonomous monitoring with alerting**.

---

## Core Capability

**One toggle that makes the ISR chain autonomous:**

- Auto-refresh WiGLE observations on configurable interval (1 min – 60 min)
- Monitor active selectors (SSID, BSSID, IP) for new observations
- Fire anomaly alerts when movement velocity exceeds threshold
- Push notifications: Streamlit toast, email, or TAK Cursor-on-Target (CoT) message
- Session replay: log all observations and alerts for post-event reconstruction

---

## Differentiator from WRAITH-WiGLE

| Dimension | WRAITH-WiGLE | WRAITH-Sentinel |
|-----------|-------------|-----------------|
| Mode | Investigative (query on demand) | Sentinel (autonomous watch) |
| Operator role | Active analyst | Passive monitor |
| Data refresh | Manual | Scheduled (APScheduler) |
| Alerting | None | Toast / email / TAK CoT |
| TAK integration | No | Yes (CivTAK / TAKServer) |
| Use case | OSINT research, pattern analysis | Operational watch, real-time ISR |
| Audience | Intelligence analyst | Operations officer / watch stander |

---

## Technology Fit

All core dependencies are already present in the WRAITH stack:

| Capability | Technology | Status |
|------------|-----------|--------|
| Scheduled refresh | APScheduler | Already installed in WRAITH |
| Email alerts | smtplib / ALERT_EMAIL_* env vars | Already in app.py |
| Data modules | modules/wigle.py, velocity.py | Already built in WiGLE v0.1 |
| TAK CoT output | pytak (free, open source) | New dependency — lightweight |
| Session logging | pandas + CSV | Already in WRAITH stack |

Estimated new code: ~200 lines (`modules/scheduler.py` + sidebar controls + alert hook).

---

## WRAITH Suite Position

```
WRAITH Suite
├── WRAITH-WiGLE        OSINT monitoring — investigative, analyst-facing
├── WRAITH-Sentinel     Operational watch — autonomous, ops-facing        ← this
├── (future) WRAITH-Map Geospatial fusion — multi-layer SA display
└── (future) WRAITH-Net Network/IP intelligence — Censys/Shodan/BGP layer
```

---

## Questions to Answer Before Building

1. Does Sentinel run as a standalone Streamlit app or as a tab/mode within WRAITH-WiGLE?
2. Is TAK/CivTAK integration in scope for v1, or email-only alerting first?
3. What selectors does Sentinel watch — operator-defined list, or imported from a WiGLE session?
4. Does Sentinel need multi-operator support (shared watch log visible to a team)?
5. What is the acceptable false-positive rate on anomaly alerts?

---

## Next Step

When ready to build: run `/seed` to incubate WRAITH-Sentinel as a new project,
or `/paul:init` inside a new `WRAITH-Sentinel/` directory to begin execution.

---

*Created: 2026-04-06*
*Author: WRAITH development session*
*Status: Concept — pending /seed or /paul:init*
