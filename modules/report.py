"""
Intel report generator for WRAITH-WiGLE.

Produces self-contained HTML selector intelligence reports and CSV exports
from the current Selector view state. No API keys, no file I/O, no new
pip dependencies — Jinja2 is already installed via Streamlit.

No UI or streamlit dependencies — pure data module.
Callers are responsible for saving the returned strings to disk.
"""

from __future__ import annotations

import datetime
import logging

import pandas as pd
from jinja2 import Template

logger = logging.getLogger(__name__)

REPORT_SECTIONS = [
    "observations", "colocation", "velocity",
    "shodan", "osm", "telegram",
]

# ── HTML template ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WRAITH-WiGLE // {{ selector_field }}:{{ selector_value }}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0f172a;
    color: #e2e8f0;
    font-family: 'Courier New', Courier, monospace;
    font-size: 13px;
    padding: 24px;
    line-height: 1.6;
  }
  .report-header {
    border-bottom: 2px solid #38bdf8;
    padding-bottom: 16px;
    margin-bottom: 24px;
  }
  .report-title {
    font-size: 20px;
    color: #38bdf8;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .report-meta {
    color: #94a3b8;
    font-size: 12px;
  }
  .report-meta span {
    color: #e2e8f0;
    font-weight: bold;
  }
  .section {
    margin-bottom: 32px;
  }
  .section-title {
    font-size: 13px;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-left: 3px solid #38bdf8;
    padding-left: 10px;
    margin-bottom: 12px;
  }
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  .data-table th {
    background: #1e293b;
    color: #94a3b8;
    text-align: left;
    padding: 6px 10px;
    border-bottom: 1px solid #334155;
    font-weight: normal;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.05em;
  }
  .data-table td {
    padding: 5px 10px;
    border-bottom: 1px solid #1e293b;
    color: #e2e8f0;
    vertical-align: top;
  }
  .data-table tr:hover td {
    background: #1e293b;
  }
  .anomaly td {
    color: #ef4444;
  }
  .empty {
    color: #475569;
    font-style: italic;
    padding: 8px 0;
  }
  .summary-box {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 12px;
    color: #94a3b8;
    font-size: 12px;
  }
  .summary-box .value {
    color: #38bdf8;
    font-weight: bold;
    font-size: 16px;
    display: block;
    margin-bottom: 2px;
  }
  .anomaly-alert {
    color: #ef4444;
  }
  .anomaly-ok {
    color: #22c55e;
  }
  .report-footer {
    border-top: 1px solid #334155;
    padding-top: 16px;
    margin-top: 32px;
    color: #475569;
    font-size: 11px;
    text-align: center;
  }
  .kpi-row {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .kpi-box {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 10px 16px;
    min-width: 140px;
  }
  .kpi-label {
    color: #64748b;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .kpi-value {
    color: #38bdf8;
    font-size: 18px;
    font-weight: bold;
  }
</style>
</head>
<body>

<div class="report-header">
  <div class="report-title">WRAITH-WiGLE // Selector Intelligence Report</div>
  <div class="report-meta">
    Field: <span>{{ selector_field }}</span> &nbsp;|&nbsp;
    Selector: <span>{{ selector_value }}</span> &nbsp;|&nbsp;
    Generated: <span>{{ generated_at }}</span>
  </div>
</div>

<div class="kpi-row">
  <div class="kpi-box">
    <div class="kpi-label">Observations</div>
    <div class="kpi-value">{{ obs_count }}</div>
  </div>
  <div class="kpi-box">
    <div class="kpi-label">Co-located Networks</div>
    <div class="kpi-value">{{ coloc_count }}</div>
  </div>
  <div class="kpi-box">
    <div class="kpi-label">Movement Anomalies</div>
    <div class="kpi-value {% if anomaly_count > 0 %}anomaly-alert{% else %}anomaly-ok{% endif %}">{{ anomaly_count }}</div>
  </div>
  <div class="kpi-box">
    <div class="kpi-label">Shodan Devices</div>
    <div class="kpi-value">{{ shodan_count }}</div>
  </div>
  <div class="kpi-box">
    <div class="kpi-label">POIs Nearby</div>
    <div class="kpi-value">{{ osm_count }}</div>
  </div>
  <div class="kpi-box">
    <div class="kpi-label">Telegram Mentions</div>
    <div class="kpi-value">{{ tg_count }}</div>
  </div>
</div>

<div class="section">
  <div class="section-title">Observations</div>
  {{ obs_html }}
</div>

<div class="section">
  <div class="section-title">Co-located Networks</div>
  {{ coloc_html }}
</div>

<div class="section">
  <div class="section-title">Movement Analysis</div>
  <div class="summary-box">
    <span class="{% if anomaly_count > 0 %}anomaly-alert{% else %}anomaly-ok{% endif %}">
      {{ anomaly_summary }}
    </span>
  </div>
  {{ vel_html }}
</div>

<div class="section">
  <div class="section-title">Shodan — Nearby Exposed Devices</div>
  {{ shodan_html }}
</div>

<div class="section">
  <div class="section-title">OSM — Nearby Points of Interest</div>
  {{ osm_html }}
</div>

<div class="section">
  <div class="section-title">Telegram — Open Source Mentions</div>
  {{ tg_html }}
</div>

<div class="report-footer">
  WRAITH-WiGLE v0.2 &nbsp;|&nbsp; For authorized OSINT use only. &nbsp;|&nbsp;
  Passive collection — public sources only.
</div>

</body>
</html>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _df_to_html(df: pd.DataFrame | None, cols: list[str] | None = None, empty_msg: str = "No data available.") -> str:
    """Convert DataFrame to HTML table string, handling empty/None gracefully."""
    if df is None or df.empty:
        return f'<p class="empty">{empty_msg}</p>'
    try:
        display = df[cols] if cols and all(c in df.columns for c in cols) else df
        return display.to_html(index=False, border=0, classes="data-table", na_rep="—")
    except Exception as exc:
        logger.warning("_df_to_html error: %s", exc)
        return f'<p class="empty">Error rendering table: {exc}</p>'


def _anomaly_summary(vel_df: pd.DataFrame | None) -> str:
    """Return a plain-text anomaly summary string."""
    if vel_df is None or vel_df.empty or "is_anomaly" not in vel_df.columns:
        return "No velocity data."
    n = int(vel_df["is_anomaly"].sum())
    if n > 0:
        max_speed = vel_df["speed_kmh"].max() if "speed_kmh" in vel_df.columns else 0
        return f"{n} anomalous movement(s) detected. Max speed: {max_speed:.0f} km/h."
    return "No anomalous movements detected."


def _safe_len(df: pd.DataFrame | None) -> int:
    if df is None or df.empty:
        return 0
    return len(df)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_html_report(
    selector_field: str,
    selector_value: str,
    filtered_df: pd.DataFrame | None,
    coloc_df: pd.DataFrame | None = None,
    vel_df: pd.DataFrame | None = None,
    shodan_df: pd.DataFrame | None = None,
    osm_df: pd.DataFrame | None = None,
    tg_df: pd.DataFrame | None = None,
) -> str:
    """
    Generate a self-contained HTML selector intelligence report.

    Args:
        selector_field: The field queried (e.g. "ssid", "netid").
        selector_value: The selector value queried.
        filtered_df: WiGLE observations matching the selector.
        coloc_df: Co-located networks DataFrame (from find_collocated).
        vel_df: Velocity DataFrame (from compute_velocity).
        shodan_df: Nearby Shodan devices DataFrame.
        osm_df: Nearby OSM POIs DataFrame.
        tg_df: Telegram mentions DataFrame.

    Returns:
        UTF-8 HTML string. Self-contained — no external CSS/JS.
        Returns minimal error HTML on exception. Never raises.
    """
    try:
        obs_cols = ["lasttime", "trilat", "trilong", "ssid", "netid", "encryption", "near_camera"]
        coloc_cols = ["netid", "ssid", "type", "encryption", "coloc_count"]
        vel_cols = ["lasttime", "speed_kmh", "distance_km", "time_delta_h", "is_anomaly"]
        shodan_cols = ["ip", "ports", "org", "product", "country"]
        osm_cols = ["name", "amenity", "lat", "lon"]
        tg_cols = ["channel", "date", "text", "url"]

        anomaly_count = 0
        if vel_df is not None and not vel_df.empty and "is_anomaly" in vel_df.columns:
            anomaly_count = int(vel_df["is_anomaly"].sum())

        context = {
            "selector_field": selector_field,
            "selector_value": selector_value,
            "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "obs_count": _safe_len(filtered_df),
            "coloc_count": _safe_len(coloc_df),
            "anomaly_count": anomaly_count,
            "shodan_count": _safe_len(shodan_df),
            "osm_count": _safe_len(osm_df),
            "tg_count": _safe_len(tg_df),
            "obs_html": _df_to_html(filtered_df, obs_cols),
            "coloc_html": _df_to_html(coloc_df, coloc_cols),
            "vel_html": _df_to_html(vel_df, vel_cols),
            "anomaly_summary": _anomaly_summary(vel_df),
            "shodan_html": _df_to_html(shodan_df, shodan_cols),
            "osm_html": _df_to_html(osm_df, osm_cols),
            "tg_html": _df_to_html(tg_df, tg_cols),
        }

        template = Template(HTML_TEMPLATE)
        return template.render(**context)

    except Exception as exc:
        logger.warning("generate_html_report error: %s", exc)
        return (
            f"<!DOCTYPE html><html><body style='background:#0f172a;color:#ef4444;"
            f"font-family:monospace;padding:24px'>"
            f"<h2>Report generation error</h2><pre>{exc}</pre></body></html>"
        )


def generate_csv_export(filtered_df: pd.DataFrame | None) -> str:
    """
    Export filtered selector observations as a CSV string.

    Args:
        filtered_df: WiGLE observations DataFrame.

    Returns:
        UTF-8 CSV string. Returns header-only CSV if input is None/empty.
        Never raises.
    """
    try:
        if filtered_df is None or filtered_df.empty:
            # Return header row only
            cols = ["trilat", "trilong", "ssid", "netid", "encryption",
                    "lasttime", "bestrssi", "near_camera", "type", "channel"]
            return ",".join(cols) + "\n"
        return filtered_df.to_csv(index=False)
    except Exception as exc:
        logger.warning("generate_csv_export error: %s", exc)
        return f"error,{exc}\n"
