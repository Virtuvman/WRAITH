"""
WRAITH — Streamlit Front-End
================================
File: app.py
Author: Virtuvman | GitHub: https://github.com/Virtuvman
Version: 3.0

KEY FEATURES:
  - Multi-CSV upload: load multiple region files simultaneously
  - Each file identified by filename, stored as a named dataset
  - Each file is a toggleable layer (show/hide per region)
  - Files can be individually removed without clearing all data
  - Globe + Flat Map: per-file color, staleness encoded by ring width
  - Heatmap: per-file FeatureGroups, toggle in map legend
  - KPIs: combined totals + per-file breakdown table
  - BLUF: combined summary + per-file section
  - Conflicts panel: per-file coordinate conflict reporting + export
  - Auto-rotate globe is a sidebar toggle (off by default)

RUN:
  streamlit run app.py

REQUIRES:
  pip install streamlit pandas plotly folium streamlit-folium python-dotenv mgrs
"""

import os
import base64
from pathlib import Path
import datetime
import time
import hmac
import smtplib
import logging
import io
import zipfile
from email.mime.text import MIMEText

# pandas may trigger Pylance's `reportMissingModuleSource` in some environments
# even when installed correctly (wheel/binary distribution). Runtime import is valid.
import pandas as pd  # pyright: ignore[reportMissingModuleSource]
import plotly.graph_objects as go  # pyright: ignore[reportMissingImports]
import streamlit as st  # pyright: ignore[reportMissingImports]
# python-dotenv may appear unresolved in some editor/interpreter setups.
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

try:
    # Folium imports are optional and may show unresolved in some editors
    # when the active interpreter doesn't match the runtime environment.
    import folium  # pyright: ignore[reportMissingImports]
    from folium.plugins import HeatMap, MarkerCluster, MiniMap, Fullscreen  # pyright: ignore[reportMissingImports]
    from streamlit_folium import st_folium  # pyright: ignore[reportMissingImports]
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# NOTE: When `app.py` is opened from a different VS Code workspace root,
# Pylance may not include this project directory on its analysis path.
# Runtime import is valid when running from this folder (e.g. `streamlit run app.py`).
from modules.ingestion import load_csv  # pyright: ignore[reportMissingImports]
from modules.coord_normalizer import describe_detection  # pyright: ignore[reportMissingImports]
from modules.staleness import (  # pyright: ignore[reportMissingImports]
    STALENESS_ORDER,
    STALENESS_RING,
    STATUS_COLORS,
    apply_staleness,
    parse_last_seen_date,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _safe_secret(name: str, default: str = "") -> str:
    """Safely read a Streamlit secret without crashing when secrets.toml is absent."""
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        # Local runs often omit .streamlit/secrets.toml; gracefully fall back.
        return str(default)


def get_ui_profile() -> str:
    """Return one of: phone, tablet, desktop (default)."""
    try:
        raw = str(st.query_params.get("ui", "desktop")).strip().lower()
    except Exception:
        raw = "desktop"
    return raw if raw in {"phone", "tablet", "desktop"} else "desktop"


def is_phone_ui() -> bool:
    return get_ui_profile() == "phone"


def is_tablet_ui() -> bool:
    return get_ui_profile() == "tablet"

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

FILE_COLORS = [
    "#38bdf8",  # sky blue
    "#f472b6",  # pink
    "#a78bfa",  # violet
    "#34d399",  # emerald
    "#fb923c",  # orange
    "#facc15",  # yellow
    "#60a5fa",  # blue
    "#f87171",  # salmon
    "#4ade80",  # green-light
    "#c084fc",  # purple-light
]

HEATMAP_TILES = {
    "Dark (CartoDB)": {"tiles": "CartoDB dark_matter", "attr": "CartoDB"},
    "Light (CartoDB)": {"tiles": "CartoDB positron", "attr": "CartoDB"},
    "Street (OpenStreetMap)": {"tiles": "OpenStreetMap", "attr": "OpenStreetMap"},
    # Use explicit non-auth terrain tiles to avoid hosted 401 errors.
    "Terrain": {
        "tiles": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        "attr": "Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap",
    },
    "Satellite": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Tiles © Esri",
    },
}

# Optional branding assets (if present in project root)
LOGO_SVG_PATH = Path("wraith_logo.svg")
LOGO_PNG_PATH = Path("wraith_logo.png")

PAGE_ICON = "👻"
if LOGO_PNG_PATH.exists():
    PAGE_ICON = str(LOGO_PNG_PATH)
elif LOGO_SVG_PATH.exists():
    # SVG may work depending on Streamlit/browser behavior.
    PAGE_ICON = str(LOGO_SVG_PATH)

# Splash background defaults ON with automatic logo fallback for hosted pilots.
SPLASH_ENABLED = _env_bool("ENABLE_SPLASH", True)

_splash_env_path = os.getenv("SPLASH_BACKGROUND_PATH", "").strip()
if _splash_env_path:
    SPLASH_BACKGROUND_PATH = Path(_splash_env_path)
else:
    _splash_candidates = [
        Path("assets/wraith_splash.png"),
        Path("WRAITH Logo.png"),
        Path("wraith_logo.png"),
        Path("wraith_logo.svg"),
    ]
    SPLASH_BACKGROUND_PATH = next((p for p in _splash_candidates if p.exists()), _splash_candidates[0])

try:
    SPLASH_OVERLAY_ALPHA = float(os.getenv("SPLASH_OVERLAY_ALPHA", "0.35"))
except ValueError:
    SPLASH_OVERLAY_ALPHA = 0.35
SPLASH_OVERLAY_ALPHA = min(0.9, max(0.0, SPLASH_OVERLAY_ALPHA))
AUTO_PRELOAD_TEST_FIXTURES = _env_bool("AUTO_PRELOAD_TEST_FIXTURES", True)
REQUIRE_BUNDLED_FIXTURES = _env_bool("REQUIRE_BUNDLED_FIXTURES", True)

REQUIRED_BUNDLED_FIXTURE_FILENAMES = [
    "WRAITH Test Data.csv",
    "WRAITH Test Data_1.csv",
    "WRAITH Test Data_2.csv",
    "WRAITH Test Data_3.csv",
    "WRAITH Test Data_4.csv",
    "WRAITH Test Data_5.csv",
    "WRAITH Test Data_6.csv",
]


def discover_fixture_files() -> list[Path]:
    """Discover bundled test fixture CSV files for optional preload/download UX."""
    files = []

    # Resolve against app.py directory first (robust when streamlit is launched
    # from a different working directory/workspace root).
    app_dir = Path(__file__).resolve().parent
    files.extend(sorted(app_dir.glob("WRAITH Test Data*.csv")))
    app_fixture_dir = app_dir / "data" / "fixtures"
    if app_fixture_dir.exists():
        files.extend(sorted(app_fixture_dir.glob("*.csv")))

    # Backward-compatible fallback: also check current process working directory.
    cwd = Path(".").resolve()
    if cwd != app_dir:
        files.extend(sorted(cwd.glob("WRAITH Test Data*.csv")))
        cwd_fixture_dir = cwd / "data" / "fixtures"
        if cwd_fixture_dir.exists():
            files.extend(sorted(cwd_fixture_dir.glob("*.csv")))

    # De-duplicate by filename while preserving first-seen order.
    dedup: dict[str, Path] = {}
    for p in files:
        dedup.setdefault(p.name, p)
    return list(dedup.values())


def missing_required_fixtures(fixtures: list[Path] | None = None) -> list[str]:
    """Return required fixture filenames that are currently missing."""
    fixture_list = fixtures if fixtures is not None else discover_fixture_files()
    present_names = {p.name for p in fixture_list}
    return [name for name in REQUIRED_BUNDLED_FIXTURE_FILENAMES if name not in present_names]


def _splash_data_uri(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None

    mime_by_ext = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    mime = mime_by_ext.get(path.suffix.lower(), "application/octet-stream")

    try:
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return None


def apply_splash_background() -> None:
    """Apply optional full-page splash background image with readability overlay."""
    if not SPLASH_ENABLED:
        return

    splash_uri = _splash_data_uri(SPLASH_BACKGROUND_PATH)
    if not splash_uri:
        if not st.session_state.get("splash_warning_shown", False):
            st.warning(
                f"Splash is enabled but image was not found: `{SPLASH_BACKGROUND_PATH}`. "
                "Using standard background."
            )
            st.session_state.splash_warning_shown = True
        return

    st.markdown(
        f"""
<style>
.stApp {{
    background:
      linear-gradient(rgba(7, 12, 24, {SPLASH_OVERLAY_ALPHA}), rgba(7, 12, 24, {SPLASH_OVERLAY_ALPHA})),
      url('{splash_uri}');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}
[data-testid="stHeader"] {{
    background: rgba(0, 0, 0, 0);
}}
</style>
""",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="WRAITH",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif; }

.cw-header {
    display:flex; align-items:center; gap:14px;
    padding:0.4rem 0 1.2rem;
    border-bottom:1px solid rgba(255,255,255,0.08);
    margin-bottom:1.2rem;
    flex-wrap:wrap;
}
.cw-header h1 {
    font-family:'Share Tech Mono',monospace; font-size:1.5rem;
    font-weight:400; letter-spacing:0.12em; color:#e2e8f0; margin:0;
}
.cw-header .cw-sub {
    font-size:0.72rem; color:#64748b;
    letter-spacing:0.08em; text-transform:uppercase;
    line-height:1.35;
    max-width:900px;
}
.brand-logo-wrap {
    width:min(100%, 360px);
    margin:0 0 0.6rem 0;
}
.brand-subline {
    font-size:0.72rem;
    color:#64748b;
    letter-spacing:0.08em;
    text-transform:uppercase;
    line-height:1.35;
    margin-bottom:1rem;
}
@media (max-width: 760px) {
  .cw-header h1 { font-size:1.25rem; letter-spacing:0.08em; }
  .cw-header .cw-sub, .brand-subline { font-size:0.66rem; }
}

/* Global overflow and touch-target safety */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  overflow-x: hidden;
}
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] [role="button"] {
  min-height: 2.35rem;
}

/* Phone profile */
@media (max-width: 768px) {
  .kpi-card { min-width: 44%; padding: 0.65rem 0.7rem; }
  .kpi-card .kpi-num { font-size: 1.35rem; }
  .kpi-card .kpi-lbl { font-size: 0.56rem; }
  .alert-banner { font-size: 0.76rem; padding: 0.55rem 0.75rem; }
}

/* Tablet profile */
@media (min-width: 769px) and (max-width: 1100px) {
  .kpi-card { min-width: 30%; }
}

.kpi-row { display:flex; gap:10px; margin-bottom:1rem; flex-wrap:wrap; }
.kpi-card {
    flex:1; min-width:88px;
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:10px; padding:0.8rem 0.9rem; text-align:center;
}
.kpi-card .kpi-num {
    font-family:'Share Tech Mono',monospace;
    font-size:1.8rem; line-height:1.1;
}
.kpi-card .kpi-lbl {
    font-size:0.62rem; letter-spacing:0.1em;
    text-transform:uppercase; color:#64748b; margin-top:3px;
}
.kpi-card.total  .kpi-num { color:#94a3b8; }
.kpi-card.green  .kpi-num { color:#22c55e; }
.kpi-card.yellow .kpi-num { color:#eab308; }
.kpi-card.orange .kpi-num { color:#f97316; }
.kpi-card.red    .kpi-num { color:#ef4444; }

.file-table { width:100%; border-collapse:collapse; font-size:0.78rem; margin-top:0.4rem; }
.table-scroll { width:100%; overflow-x:auto; -webkit-overflow-scrolling:touch; }
.file-table th {
    text-align:left; padding:5px 10px; font-size:0.65rem;
    text-transform:uppercase; letter-spacing:0.07em;
    color:#475569; border-bottom:1px solid rgba(255,255,255,0.07);
}
.file-table td { padding:5px 10px; border-bottom:1px solid rgba(255,255,255,0.04); vertical-align:middle; }
.file-table tr:last-child td { border-bottom:none; }
.ft-dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px; vertical-align:middle; }

.alert-banner {
    padding:0.65rem 1rem; border-radius:8px; font-size:0.82rem;
    margin-bottom:0.7rem; display:flex; align-items:flex-start; gap:10px; line-height:1.5;
}
.alert-red    { background:rgba(239,68,68,0.1);  border-left:3px solid #ef4444; color:#fca5a5; }
.alert-yellow { background:rgba(234,179,8,0.1);  border-left:3px solid #eab308; color:#fde047; }
.alert-green  { background:rgba(34,197,94,0.08); border-left:3px solid #22c55e; color:#86efac; }
.alert-info   { background:rgba(99,102,241,0.1); border-left:3px solid #6366f1; color:#a5b4fc; }
.alert-warn   { background:rgba(249,115,22,0.1); border-left:3px solid #f97316; color:#fdba74; }

.section-label {
    font-family:'Share Tech Mono',monospace; font-size:0.68rem;
    letter-spacing:0.15em; text-transform:uppercase; color:#475569;
    margin-bottom:0.5rem;
    border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;
}
.detect-tag {
    font-family:'Share Tech Mono',monospace; font-size:0.68rem; color:#6366f1;
    background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.25);
    border-radius:5px; padding:2px 7px; display:inline-block; margin-right:5px;
}

.conflict-card {
    background:rgba(249,115,22,0.07);
    border:1px solid rgba(249,115,22,0.3);
    border-radius:10px; padding:1rem 1.2rem; margin-bottom:0.75rem;
}
.conflict-card .cc-header {
    font-family:'Share Tech Mono',monospace; font-size:0.8rem;
    color:#f97316; letter-spacing:0.08em; margin-bottom:0.5rem;
}
.conflict-card .cc-row {
    font-size:0.76rem; color:#94a3b8; padding:3px 0;
    border-bottom:1px solid rgba(255,255,255,0.04);
}
.conflict-card .cc-row:last-child { border-bottom:none; }
.conflict-card .cc-reason { color:#fdba74; }
.conflict-card .cc-footer {
    margin-top:0.6rem; font-size:0.72rem; color:#64748b; font-style:italic;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE SCHEMA
#
# st.session_state.files = {
#   "bolivia.csv": {
#     "df":             pd.DataFrame,   # clean, staleness columns added
#     "df_raw":         pd.DataFrame,   # original as-loaded rows
#     "errors":         list of dict,   # coordinate parse failures
#     "detection_info": dict,           # what coord format was found
#     "color":          str,            # assigned layer color hex
#     "loaded_at":      str,            # ISO date string
#   }, ...
# }
# ─────────────────────────────────────────────────────────────────────────────

def init_session():
    if "files" not in st.session_state:
        st.session_state.files = {}
    if "email_sent" not in st.session_state:
        st.session_state.email_sent = False
    if "admin_metrics_ok" not in st.session_state:
        st.session_state.admin_metrics_ok = False
    if "sample_data_autoload" not in st.session_state:
        st.session_state.sample_data_autoload = AUTO_PRELOAD_TEST_FIXTURES


def require_pilot_access() -> None:
    """Front-door password gate for hosted pilot access."""
    # Enable gate if explicitly toggled OR if any supported password key is present.
    # This prevents accidental exposure when password is configured but toggle is omitted.
    access_enabled_flag = _env_bool("PILOT_ACCESS_ENABLED", False)
    expected_primary = _safe_secret("PILOT_ACCESS_PASSWORD", os.getenv("PILOT_ACCESS_PASSWORD", "")).strip()
    expected_legacy = _safe_secret("ACCESS_PASSWORD", os.getenv("ACCESS_PASSWORD", "")).strip()
    expected = expected_primary or expected_legacy
    access_enabled = access_enabled_flag or bool(expected)
    if not access_enabled:
        return

    if not expected:
        # Fail CLOSED: never bypass when the access gate is enabled.
        st.title("WRAITH Pilot Access")
        st.error(
            "Pilot access is enabled, but `PILOT_ACCESS_PASSWORD` is not configured. "
            "Access is blocked until a password is set in Streamlit Secrets or environment variables."
        )
        st.caption("Required setting: `PILOT_ACCESS_PASSWORD`")
        st.stop()

    if "pilot_authed" not in st.session_state:
        st.session_state.pilot_authed = False
    if "pilot_failed_attempts" not in st.session_state:
        st.session_state.pilot_failed_attempts = 0
    if "pilot_lock_until" not in st.session_state:
        st.session_state.pilot_lock_until = 0.0

    if st.session_state.pilot_authed:
        return

    now_ts = time.time()
    lock_until = float(st.session_state.pilot_lock_until)
    if now_ts < lock_until:
        wait_seconds = max(1, int(lock_until - now_ts))
        st.title("WRAITH Pilot Access")
        st.warning(f"Too many failed attempts. Try again in {wait_seconds}s.")
        st.stop()

    st.title("WRAITH Pilot Access")
    st.caption("Enter pilot password to access WRAITH.")
    candidate = st.text_input("Pilot password", type="password", key="pilot_password_input")

    if st.button("Enter", use_container_width=True):
        # Constant-time comparison to reduce timing side-channel leakage.
        if hmac.compare_digest(candidate, expected):
            st.session_state.pilot_authed = True
            st.session_state.pilot_failed_attempts = 0
            st.session_state.pilot_lock_until = 0.0
            st.rerun()
        else:
            st.session_state.pilot_failed_attempts += 1
            attempts = int(st.session_state.pilot_failed_attempts)
            if attempts >= 3:
                cooldown_seconds = int(os.getenv("PILOT_LOCKOUT_SECONDS", "15"))
                st.session_state.pilot_lock_until = time.time() + max(5, cooldown_seconds)
                st.session_state.pilot_failed_attempts = 0
                st.error("Invalid password. Temporary lockout enabled.")
            else:
                st.error(f"Invalid password ({attempts}/3).")

    st.stop()


def next_color():
    """Return the next unused layer color based on how many files are loaded."""
    return FILE_COLORS[len(st.session_state.files) % len(FILE_COLORS)]


def compute_staleness(df):
    """Compatibility wrapper; delegated to modules.staleness."""
    return apply_staleness(df)


# ─────────────────────────────────────────────────────────────────────────────
# GLOBE VIEW
# Per-file traces, staleness encoded as ring color/width on each dot.
# Legend groups by file; each status is a sub-entry within that group.
# ─────────────────────────────────────────────────────────────────────────────

def render_globe(files_dict, active_names, status_filter, auto_rotate=False):
    phone_ui = is_phone_ui()
    tablet_ui = is_tablet_ui()

    frames = []
    for name in active_names:
        if name not in files_dict:
            continue
        df = files_dict[name]["df"].copy()
        df = df[df["staleness_status"].isin(status_filter)]
        if df.empty:
            continue
        df["_source"] = name
        df["_fcolor"] = files_dict[name]["color"]
        frames.append(df)

    if not frames:
        st.info("No data matches current filters.")
        return

    df_all = pd.concat(frames, ignore_index=True)
    center_lat = df_all["latitude"].mean()
    center_lon = df_all["longitude"].mean()

    df_all["hover"] = df_all.apply(lambda r: (
        f"<b>{r.get('location_label','')}</b><br>"
        f"<i style='color:#94a3b8'>{r['_source']}</i><br>"
        f"IP: {r.get('ip','N/A')}<br>"
        f"Model: {r.get('model','Unknown')}<br>"
        f"Last Seen: {r.get('last_seen','')}<br>"
        f"<b>{r['staleness_status']}</b> ({r['age_months']} mo)<br>"
        f"Country: {r.get('country','')}"
    ), axis=1)

    fig = go.Figure()

    for fname in active_names:
        if fname not in files_dict:
            continue
        fcolor     = files_dict[fname]["color"]
        short      = fname.replace(".csv", "")[:22]
        sub_file   = df_all[df_all["_source"] == fname]

        first_trace = True
        for status in STALENESS_ORDER:
            sub = sub_file[sub_file["staleness_status"] == status]
            if sub.empty:
                continue
            ring = STALENESS_RING[status]
            fig.add_trace(go.Scattergeo(
                lat=sub["latitude"],
                lon=sub["longitude"],
                mode="markers",
                name=f"{status}",
                legendgroup=fname,
                legendgrouptitle_text=short if first_trace else None,
                marker=dict(
                    size=8,
                    color=fcolor,
                    opacity=ring["opacity"],
                    line=dict(width=ring["width"], color=ring["color"]),
                ),
                hovertemplate=sub["hover"] + "<extra></extra>",
                selected=dict(marker=dict(size=14, opacity=1.0)),
                unselected=dict(marker=dict(opacity=0.3)),
            ))
            first_trace = False

    fig.update_geos(
        projection_type="orthographic",
        projection_rotation=dict(lon=center_lon, lat=center_lat, roll=0),
        showland=True,       landcolor="#1e293b",
        showocean=True,      oceancolor="#0f172a",
        showlakes=True,      lakecolor="#0f172a",
        showcountries=True,  countrycolor="#334155",
        showcoastlines=True, coastlinecolor="#334155",
        showframe=False,     bgcolor="rgba(0,0,0,0)",
    )
    globe_height = 430 if phone_ui else (500 if tablet_ui else 560)

    fig.update_layout(
        height=globe_height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            # Keep legend away from Plotly modebar controls (top-right).
            orientation="h" if phone_ui else "v",
            x=0.5 if phone_ui else 1.01,
            y=0.02 if phone_ui else 0.82,
            xanchor="center" if phone_ui else "left",
            font=dict(size=10, color="#94a3b8"),
            bgcolor="rgba(15,23,42,0.75)",
            bordercolor="rgba(255,255,255,0.1)", borderwidth=1,
            groupclick="toggleitem",
        ),
        dragmode="orbit",
    )

    if phone_ui:
        auto_rotate = False

    if auto_rotate:
        rot_frames = [
            go.Frame(layout=dict(geo=dict(
                projection_rotation=dict(
                    lon=(center_lon + step) % 360,
                    lat=center_lat, roll=0,
                )
            ))) for step in range(0, 360, 3)
        ]
        fig.frames = rot_frames
        fig.update_layout(updatemenus=[dict(
            type="buttons", showactive=False,
            y=0.02, x=0.01, xanchor="left", yanchor="bottom",
            buttons=[dict(
                label="▶ Rotate", method="animate",
                args=[None, dict(
                    frame=dict(duration=40, redraw=True),
                    fromcurrent=True,
                    transition=dict(duration=0),
                )],
            )],
        )])

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True, "scrollZoom": True,
        "modeBarButtonsToRemove": ["select2d", "lasso2d"],
        "toImageButtonOptions": {"format": "png", "filename": "wraith_globe"},
    })

    # File color legend below the chart
    _render_file_legend(files_dict, active_names)


# ─────────────────────────────────────────────────────────────────────────────
# FLAT MAP VIEW
# Natural-earth projection, auto-fits to data extent, same layer model.
# ─────────────────────────────────────────────────────────────────────────────

def render_flat_map(files_dict, active_names, status_filter):
    phone_ui = is_phone_ui()
    tablet_ui = is_tablet_ui()

    frames = []
    for name in active_names:
        if name not in files_dict:
            continue
        df = files_dict[name]["df"].copy()
        df = df[df["staleness_status"].isin(status_filter)]
        if df.empty:
            continue
        df["_source"] = name
        df["_fcolor"] = files_dict[name]["color"]
        frames.append(df)

    if not frames:
        st.info("No data matches current filters.")
        return

    df_all = pd.concat(frames, ignore_index=True)

    df_all["hover"] = df_all.apply(lambda r: (
        f"<b>{r.get('location_label','')}</b><br>"
        f"<i style='color:#94a3b8'>{r['_source']}</i><br>"
        f"IP: {r.get('ip','N/A')}<br>"
        f"Model: {r.get('model','Unknown')}<br>"
        f"Last Seen: {r.get('last_seen','')}<br>"
        f"<b>{r['staleness_status']}</b> ({r['age_months']} mo)"
    ), axis=1)

    fig = go.Figure()

    for fname in active_names:
        if fname not in files_dict:
            continue
        fcolor   = files_dict[fname]["color"]
        short    = fname.replace(".csv", "")[:22]
        sub_file = df_all[df_all["_source"] == fname]

        first_trace = True
        for status in STALENESS_ORDER:
            sub = sub_file[sub_file["staleness_status"] == status]
            if sub.empty:
                continue
            ring = STALENESS_RING[status]
            fig.add_trace(go.Scattergeo(
                lat=sub["latitude"],
                lon=sub["longitude"],
                mode="markers",
                name=f"{status}",
                legendgroup=fname,
                legendgrouptitle_text=short if first_trace else None,
                marker=dict(
                    size=7, color=fcolor,
                    opacity=ring["opacity"],
                    line=dict(width=ring["width"], color=ring["color"]),
                ),
                hovertemplate=sub["hover"] + "<extra></extra>",
                selected=dict(marker=dict(size=13, opacity=1.0)),
                unselected=dict(marker=dict(opacity=0.3)),
            ))
            first_trace = False

    all_lats = df_all["latitude"]
    all_lons = df_all["longitude"]

    fig.update_geos(
        projection_type="natural earth",
        showland=True,       landcolor="#1e293b",
        showocean=True,      oceancolor="#0f172a",
        showlakes=True,      lakecolor="#0f172a",
        showcountries=True,  countrycolor="#334155",
        showcoastlines=True, coastlinecolor="#475569",
        showframe=False,     bgcolor="rgba(0,0,0,0)",
        lataxis_range=[max(-90,  all_lats.min()-8), min(90,   all_lats.max()+8)],
        lonaxis_range=[max(-180, all_lons.min()-12), min(180, all_lons.max()+12)],
    )
    flat_height = 420 if phone_ui else (500 if tablet_ui else 540)

    fig.update_layout(
        height=flat_height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            # Keep legend away from Plotly modebar controls (top-right).
            orientation="h" if phone_ui else "v",
            x=0.5 if phone_ui else 1.01,
            y=0.02 if phone_ui else 0.82,
            xanchor="center" if phone_ui else "left",
            font=dict(size=10, color="#94a3b8"),
            bgcolor="rgba(15,23,42,0.75)",
            bordercolor="rgba(255,255,255,0.1)", borderwidth=1,
            groupclick="toggleitem",
        ),
        clickmode="event+select",
    )

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True, "scrollZoom": True,
        "toImageButtonOptions": {"format": "png", "filename": "wraith_flatmap"},
    })

    _render_file_legend(files_dict, active_names)


# ─────────────────────────────────────────────────────────────────────────────
# HEATMAP VIEW
# Per-file Folium FeatureGroups — operator toggles each in the map layer control.
# Fill = file color, ring = staleness color, density HeatMap underneath.
# ─────────────────────────────────────────────────────────────────────────────

def render_heatmap(
    files_dict,
    active_names,
    status_filter,
    tile_style="Dark (CartoDB)",
    use_cluster=True,
    marker_radius=6,
    heat_radius=20,
    show_minimap=True,
):
    phone_ui = is_phone_ui()
    tablet_ui = is_tablet_ui()

    if not FOLIUM_AVAILABLE:
        st.warning("Run: `pip install folium streamlit-folium`")
        return

    all_frames = []
    for name in active_names:
        if name not in files_dict:
            continue
        df = files_dict[name]["df"].copy()
        df = df[df["staleness_status"].isin(status_filter)]
        df["_source"] = name
        all_frames.append(df)

    if not all_frames:
        st.info("No data matches current filters.")
        return

    df_all = pd.concat(all_frames, ignore_index=True)
    center = [df_all["latitude"].mean(), df_all["longitude"].mean()]

    tile_cfg = HEATMAP_TILES.get(tile_style, HEATMAP_TILES["Dark (CartoDB)"])

    m = folium.Map(
        location=center, zoom_start=4,
        tiles=tile_cfg["tiles"], attr=tile_cfg["attr"],
        control_scale=True,
        prefer_canvas=True,
    )

    # Allow quick switching between detailed base maps.
    for label, cfg in HEATMAP_TILES.items():
        if label == tile_style:
            continue
        folium.TileLayer(
            tiles=cfg["tiles"],
            attr=cfg["attr"],
            name=f"🗺 {label}",
            overlay=False,
            control=True,
        ).add_to(m)

    Fullscreen(position="topleft", force_separate_button=True).add_to(m)
    if show_minimap:
        MiniMap(toggle_display=True, position="bottomleft").add_to(m)

    weight_map = {"CURRENT": 1, "REVIEW": 2, "STALE": 3, "EXPIRED": 4}

    # Per-file FeatureGroup — each toggleable in the map's layer control
    for name in active_names:
        if name not in files_dict:
            continue
        df     = files_dict[name]["df"].copy()
        df     = df[df["staleness_status"].isin(status_filter)]
        fcolor = files_dict[name]["color"]
        short  = name.replace(".csv", "")

        if df.empty:
            continue

        fg = folium.FeatureGroup(name=f"◉ {short}", show=True)
        marker_target = MarkerCluster(name=f"{short} cluster", disableClusteringAtZoom=8).add_to(fg) if use_cluster else fg

        for _, row in df.iterrows():
            ring = STALENESS_RING[row["staleness_status"]]
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=marker_radius,
                color=ring["color"],        # ring = staleness
                fill=True,
                fill_color=fcolor,          # fill = file/region color
                fill_opacity=0.82,
                weight=ring["width"],
                popup=folium.Popup(
                    f"<div style='font-family:monospace;font-size:12px;min-width:235px;line-height:1.45'>"
                    f"<b>{row.get('location_label','Unknown')}</b><br>"
                    f"<span style='color:#94a3b8'>Region:</span> {short}<br>"
                    f"<span style='color:#94a3b8'>Country:</span> {row.get('country','N/A')}<br>"
                    f"IP: {row.get('ip','N/A')}<br>"
                    f"Device: {row.get('device_type','Unknown')}<br>"
                    f"Model: {row.get('model','Unknown')}<br>"
                    f"Port: {row.get('port','')}<br>"
                    f"Org: {row.get('org','N/A')}<br>"
                    f"Coords: {row.get('latitude','')}, {row.get('longitude','')}<br>"
                    f"Last Seen: {row.get('last_seen','')}<br>"
                    f"<b style='color:{ring['color']}'>"
                    f"{row['staleness_status']}</b> ({row['age_months']} mo)"
                    f"</div>",
                    max_width=250,
                ),
                tooltip=folium.Tooltip(
                    f"{short} · {row.get('location_label', row.get('ip',''))} "
                    f"— {row['staleness_status']} · {row.get('country','')}",
                    sticky=False,
                ),
            ).add_to(marker_target)

        fg.add_to(m)

    # Density heatmap underneath all markers
    heat_data = [
        [r["latitude"], r["longitude"], weight_map.get(r["staleness_status"], 1)]
        for _, r in df_all.iterrows()
    ]
    hfg = folium.FeatureGroup(name="🌡 Density layer", show=True)
    HeatMap(
        heat_data,
        radius=heat_radius,
        blur=max(12, int(heat_radius * 0.9)),
        # NOTE: Avoid explicit gradient due a folium/branca serialization bug in
        # some versions where gradient keys become floats and break camelize().
        min_opacity=0.2,
        max_zoom=9,
    ).add_to(hfg)
    hfg.add_to(m)

    folium.LayerControl(collapsed=phone_ui, position="topright").add_to(m)

    heat_height = 460 if phone_ui else (520 if tablet_ui else 560)
    st_folium(m, use_container_width=True, height=heat_height, returned_objects=[])

    # Legend row below map
    _render_file_legend(files_dict, active_names, show_ring_key=True)


# ─────────────────────────────────────────────────────────────────────────────
# FILE COLOR LEGEND
# ─────────────────────────────────────────────────────────────────────────────

def _render_file_legend(files_dict, active_names, show_ring_key=False):
    phone_ui = is_phone_ui()
    swatches = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'font-size:{"0.68rem" if phone_ui else "0.75rem"};color:#94a3b8;'
        f'margin:2px 8px 2px 0">'
        f'<span style="width:10px;height:10px;border-radius:50%;'
        f'background:{files_dict[n]["color"]};display:inline-block;flex-shrink:0"></span>'
        f'{n.replace(".csv","")}</span>'
        for n in active_names if n in files_dict
    )
    ring_key = ""
    if show_ring_key:
        ring_key = (
            ' &nbsp;·&nbsp; <span style="font-size:0.71rem;color:#64748b">'
            'Ring = staleness: '
            '<span style="color:#22c55e">●</span> Current &nbsp;'
            '<span style="color:#eab308">●</span> Review &nbsp;'
            '<span style="color:#f97316">●</span> Stale &nbsp;'
            '<span style="color:#ef4444">●</span> Expired</span>'
        )
    st.markdown(
        f'<div style="margin-top:0.5rem;padding:0.3rem 0;display:flex;flex-wrap:wrap;align-items:center">{swatches}{ring_key}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS — combined totals + per-file breakdown
# ─────────────────────────────────────────────────────────────────────────────

def render_kpis(files_dict, active_names, status_filter):
    phone_ui = is_phone_ui()
    total = current = review = stale = expired = 0
    file_rows = []
    region_values: set[str] = set()

    for name in active_names:
        if name not in files_dict:
            continue
        df = files_dict[name]["df"]
        df = df[df["staleness_status"].isin(status_filter)]
        c  = int((df["staleness_status"] == "CURRENT").sum())
        r  = int((df["staleness_status"] == "REVIEW").sum())
        s  = int((df["staleness_status"] == "STALE").sum())
        e  = int((df["staleness_status"] == "EXPIRED").sum())
        t  = len(df)
        total   += t
        current += c
        review  += r
        stale   += s
        expired += e
        if "region" in df.columns:
            region_values.update({str(v).strip() for v in df["region"].dropna().astype(str) if str(v).strip()})
        file_rows.append((name, files_dict[name]["color"], t, c, r, s, e))

    region_count = len(region_values)
    layer_count = len(active_names)

    st.markdown(
        f'<div class="kpi-row">'
        f'<div class="kpi-card total"><div class="kpi-num">{total}</div>'
        f'<div class="kpi-lbl">{"Total" if phone_ui else "Total Cameras"}</div></div>'
        f'<div class="kpi-card green"><div class="kpi-num">{current}</div>'
        f'<div class="kpi-lbl">{"Current" if phone_ui else "Current &lt;90d"}</div></div>'
        f'<div class="kpi-card yellow"><div class="kpi-num">{review}</div>'
        f'<div class="kpi-lbl">{"Review" if phone_ui else "Review 90–180d"}</div></div>'
        f'<div class="kpi-card orange"><div class="kpi-num">{stale}</div>'
        f'<div class="kpi-lbl">{"Stale" if phone_ui else "Stale 180–360d"}</div></div>'
        f'<div class="kpi-card red"><div class="kpi-num">{expired}</div>'
        f'<div class="kpi-lbl">{"Expired" if phone_ui else "Expired &gt;360d"}</div></div>'
        f'<div class="kpi-card total"><div class="kpi-num">{region_count}</div>'
        f'<div class="kpi-lbl">Regions</div></div>'
        f'<div class="kpi-card total"><div class="kpi-num">{layer_count}</div>'
        f'<div class="kpi-lbl">Layers</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Per-file table — only shown when more than one file loaded
    if len(file_rows) > 1:
        with st.expander("Per-region breakdown", expanded=True):
            rows_html = "".join(
                f'<tr>'
                f'<td><span class="ft-dot" style="background:{color}"></span>'
                f'{name.replace(".csv","")}</td>'
                f'<td style="text-align:center">{t}</td>'
                f'<td style="text-align:center;color:#22c55e">{c}</td>'
                f'<td style="text-align:center;color:#eab308">{r}</td>'
                f'<td style="text-align:center;color:#f97316">{s}</td>'
                f'<td style="text-align:center;color:#ef4444">{e}</td>'
                f'</tr>'
                for name, color, t, c, r, s, e in file_rows
            )
            st.markdown(
                f'<div class="table-scroll"><table class="file-table"><thead><tr>'
                f'<th>Region / File</th><th>Total</th>'
                f'<th>Current</th><th>Review</th><th>Stale</th><th>Expired</th>'
                f'</tr></thead><tbody>{rows_html}</tbody></table></div>',
                unsafe_allow_html=True,
            )

    return total, current, review, stale, expired, region_count, layer_count


def _build_metrics_context(files_dict, filtered_dict, active_names, status_filter):
    ingest_rows = 0
    parsed_rows = 0
    conflict_rows = 0
    per_file_rows = []

    for name, fd in files_dict.items():
        df_raw = fd.get("df_raw")
        df_clean = fd.get("df")
        errors = fd.get("errors", [])
        detection_info = fd.get("detection_info", {})

        raw_count = len(df_raw) if df_raw is not None else len(df_clean)
        parsed_count = len(df_clean) if df_clean is not None else 0
        err_count = len(errors)

        ingest_rows += raw_count
        parsed_rows += parsed_count
        conflict_rows += err_count

        active_df = filtered_dict.get(name, {}).get("df")
        if active_df is None:
            active_count = 0
            c = r = s = e = 0
        else:
            active_df = active_df[active_df["staleness_status"].isin(status_filter)]
            active_count = len(active_df)
            c = int((active_df["staleness_status"] == "CURRENT").sum())
            r = int((active_df["staleness_status"] == "REVIEW").sum())
            s = int((active_df["staleness_status"] == "STALE").sum())
            e = int((active_df["staleness_status"] == "EXPIRED").sum())

        per_file_rows.append(
            {
                "source_file": name,
                "loaded_at": fd.get("loaded_at", ""),
                "coord_format": describe_detection(detection_info),
                "rows_ingested": raw_count,
                "rows_parsed": parsed_count,
                "conflicts": err_count,
                "parse_success_pct": round((parsed_count / raw_count) * 100, 1) if raw_count else 0.0,
                "active_rows": active_count,
                "current": c,
                "review": r,
                "stale": s,
                "expired": e,
            }
        )

    parse_success_pct = round((parsed_rows / ingest_rows) * 100, 1) if ingest_rows else 0.0

    active_frames = []
    for name in active_names:
        if name not in filtered_dict:
            continue
        df = filtered_dict[name]["df"].copy()
        if df.empty:
            continue
        df = df[df["staleness_status"].isin(status_filter)]
        if df.empty:
            continue
        df["source_file"] = name
        active_frames.append(df)

    df_active = pd.concat(active_frames, ignore_index=True) if active_frames else pd.DataFrame()

    return {
        "ingest_rows": ingest_rows,
        "parsed_rows": parsed_rows,
        "conflict_rows": conflict_rows,
        "parse_success_pct": parse_success_pct,
        "loaded_files": len(files_dict),
        "active_files": len([n for n in active_names if n in filtered_dict]),
        "per_file_df": pd.DataFrame(per_file_rows),
        "df_active": df_active,
    }


def render_metrics_panel(files_dict, filtered_dict, active_names, status_filter):
    phone_ui = is_phone_ui()
    tablet_ui = is_tablet_ui()

    st.markdown('<div class="section-label">Admin Metrics — Usage & Ingest Statistics</div>', unsafe_allow_html=True)

    ctx = _build_metrics_context(files_dict, filtered_dict, active_names, status_filter)
    df_active = ctx["df_active"]
    per_file_df = ctx["per_file_df"]

    if phone_ui:
        p1, p2 = st.columns(2)
        p1.metric("Loaded files", ctx["loaded_files"])
        p2.metric("Active files", ctx["active_files"])
        p3, p4 = st.columns(2)
        p3.metric("Rows ingested", f"{ctx['ingest_rows']:,}")
        p4.metric("Rows parsed", f"{ctx['parsed_rows']:,}")
        p5, p6 = st.columns(2)
        p5.metric("Parse success", f"{ctx['parse_success_pct']}%")
        p6.metric("Conflict rows", f"{ctx['conflict_rows']:,}")
        if not df_active.empty:
            p7, p8 = st.columns(2)
            p7.metric("Active rows", f"{len(df_active):,}")
            p8.metric("Expired %", f"{round((df_active['staleness_status'].eq('EXPIRED').mean()*100),1)}%")
    else:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Loaded files", ctx["loaded_files"])
        c2.metric("Active files", ctx["active_files"])
        c3.metric("Rows ingested", f"{ctx['ingest_rows']:,}")
        c4.metric("Rows parsed", f"{ctx['parsed_rows']:,}")
        c5.metric("Parse success", f"{ctx['parse_success_pct']}%")

        c6, c7, c8 = st.columns(3)
        c6.metric("Conflict rows", f"{ctx['conflict_rows']:,}")
        if not df_active.empty:
            c7.metric("Active rows", f"{len(df_active):,}")
            c8.metric("Expired %", f"{round((df_active['staleness_status'].eq('EXPIRED').mean()*100),1)}%")
        else:
            c7.metric("Active rows", "0")
            c8.metric("Expired %", "0.0%")

    st.markdown("---")

    if df_active.empty:
        st.info("No active rows match current filters for metrics charts.")
    else:
        # Status distribution
        status_counts = (
            df_active["staleness_status"]
            .value_counts()
            .reindex(STALENESS_ORDER, fill_value=0)
            .reset_index()
        )
        status_counts.columns = ["status", "count"]

        donut = go.Figure(
            data=[
                go.Pie(
                    labels=status_counts["status"],
                    values=status_counts["count"],
                    hole=0.5,
                    marker=dict(colors=[STATUS_COLORS[s] for s in STALENESS_ORDER]),
                )
            ]
        )
        donut.update_layout(height=360, margin=dict(l=0, r=0, t=20, b=0), title="Status distribution")

        # Monthly trend
        trend = df_active.copy()
        trend["_dt"] = trend["last_seen"].apply(parse_last_seen_date)
        trend = trend[trend["_dt"].notna()].copy()
        trend["month"] = trend["_dt"].apply(lambda d: d.strftime("%Y-%m"))

        if not trend.empty:
            grp = trend.groupby(["month", "staleness_status"]).size().reset_index(name="count")
            trend_fig = go.Figure()
            for status in STALENESS_ORDER:
                color = STATUS_COLORS[status]
                sub = grp[grp["staleness_status"] == status]
                trend_fig.add_trace(go.Bar(x=sub["month"], y=sub["count"], name=status, marker_color=color))
            trend_fig.update_layout(
                barmode="stack",
                height=360,
                margin=dict(l=0, r=0, t=20, b=0),
                title="Monthly last_seen trend",
                xaxis_title="Month",
                yaxis_title="Records",
            )
        else:
            trend_fig = None

        left, right = st.columns(1) if phone_ui else st.columns(2)
        with left:
            st.plotly_chart(donut, use_container_width=True)
        if not phone_ui:
            with right:
                if trend_fig is not None:
                    st.plotly_chart(trend_fig, use_container_width=True)
                else:
                    st.info("No parseable `last_seen` dates for monthly trend.")
        elif trend_fig is not None:
            st.plotly_chart(trend_fig, use_container_width=True)

        # Top entities + age distribution
        c_top1, c_top2 = st.columns(1) if phone_ui else st.columns(2)

        top_countries = df_active["country"].fillna("UNKNOWN").value_counts().head(10)
        fig_country = go.Figure(
            data=[go.Bar(x=top_countries.values, y=top_countries.index, orientation="h", marker_color="#60a5fa")]
        )
        fig_country.update_layout(height=360, margin=dict(l=0, r=0, t=20, b=0), title="Top countries")

        top_orgs = df_active["org"].fillna("UNKNOWN").value_counts().head(10)
        fig_org = go.Figure(
            data=[go.Bar(x=top_orgs.values, y=top_orgs.index, orientation="h", marker_color="#a78bfa")]
        )
        fig_org.update_layout(height=360, margin=dict(l=0, r=0, t=20, b=0), title="Top organizations")

        with c_top1:
            st.plotly_chart(fig_country, use_container_width=True)
        if not phone_ui:
            with c_top2:
                st.plotly_chart(fig_org, use_container_width=True)
        else:
            st.plotly_chart(fig_org, use_container_width=True)

        c_top3, c_top4 = st.columns(1) if phone_ui else st.columns(2)

        top_ports = df_active["port"].astype(str).fillna("UNKNOWN").value_counts().head(10)
        fig_port = go.Figure(
            data=[go.Bar(x=top_ports.index, y=top_ports.values, marker_color="#34d399")]
        )
        fig_port.update_layout(height=320, margin=dict(l=0, r=0, t=20, b=0), title="Top ports")

        top_models = df_active["model"].fillna("UNKNOWN").value_counts().head(10)
        fig_model = go.Figure(
            data=[go.Bar(x=top_models.values, y=top_models.index, orientation="h", marker_color="#f472b6")]
        )
        fig_model.update_layout(height=320, margin=dict(l=0, r=0, t=20, b=0), title="Top models")

        with c_top3:
            st.plotly_chart(fig_port, use_container_width=True)
        if not phone_ui:
            with c_top4:
                st.plotly_chart(fig_model, use_container_width=True)
        else:
            st.plotly_chart(fig_model, use_container_width=True)

        fig_age = go.Figure(
            data=[go.Histogram(x=df_active["age_months"], nbinsx=20, marker_color="#facc15")]
        )
        fig_age.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), title="Age distribution (months)")
        st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="section-label">Per-file ingest quality</div>', unsafe_allow_html=True)
    st.dataframe(per_file_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-label">Metrics exports</div>', unsafe_allow_html=True)
    summary_df = pd.DataFrame([
        {
            "generated_on": datetime.date.today().isoformat(),
            "loaded_files": ctx["loaded_files"],
            "active_files": ctx["active_files"],
            "rows_ingested": ctx["ingest_rows"],
            "rows_parsed": ctx["parsed_rows"],
            "conflict_rows": ctx["conflict_rows"],
            "parse_success_pct": ctx["parse_success_pct"],
        }
    ])

    e1, e2, e3 = st.columns(1) if phone_ui else st.columns(3)
    with e1:
        st.download_button(
            "⬇ Metrics summary CSV",
            data=summary_df.to_csv(index=False).encode("utf-8"),
            file_name=f"wraith_metrics_summary_{datetime.date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with e2:
        st.download_button(
            "⬇ Per-file ingest CSV",
            data=per_file_df.to_csv(index=False).encode("utf-8"),
            file_name=f"wraith_metrics_per_file_{datetime.date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with e3:
        if df_active.empty:
            st.button("No active metrics rows", disabled=True, use_container_width=True)
        else:
            st.download_button(
                "⬇ Active metrics rows CSV",
                data=df_active.to_csv(index=False).encode("utf-8"),
                file_name=f"wraith_metrics_active_rows_{datetime.date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
# CONFLICTS PANEL — per-file coordinate conflict reporting
# ─────────────────────────────────────────────────────────────────────────────

def render_conflicts(files_dict):
    phone_ui = is_phone_ui()
    any_errors = any(len(fd["errors"]) > 0 for fd in files_dict.values())

    if not any_errors:
        st.markdown(
            '<div class="alert-banner alert-green">'
            '✓ All rows across all loaded files parsed successfully — '
            'no coordinate conflicts detected.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    for name, fdata in files_dict.items():
        errors = fdata["errors"]
        df_raw = fdata["df_raw"]
        if not errors:
            continue

        st.markdown(f'<div class="section-label">{name}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="alert-banner alert-warn">'
            f'⚡ <b>{len(errors)} conflict(s)</b> in {name}</div>',
            unsafe_allow_html=True,
        )

        rows_html = "".join(
            f'<div class="cc-row">'
            f'<b>Row {err["row_index"]}</b> · '
            f'Format attempted: <code>{err["format_detected"]}</code> · '
            f'<span class="cc-reason">{err["reason"]}</span>'
            + (
                ""
                if phone_ui
                else f'<br><span style="color:#64748b;font-size:0.71rem">'
                     f'Raw: {" | ".join(f"{k}:{v}" for k,v in err["raw_values"].items()) or "N/A"}'
                     f'</span>'
            )
            + '</div>'
            for err in errors
        )

        st.markdown(
            f'<div class="conflict-card">'
            f'<div class="cc-header">⚠ {len(errors)} coordinate conflict(s) — {name}</div>'
            f'{rows_html}'
            f'<div class="cc-footer">'
            f'Correct coordinates in the source CSV and re-upload to resolve.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # Show full raw rows
        if df_raw is not None:
            with st.expander(f"View raw CSV rows for {name}"):
                bad_idx = [e["row_index"] for e in errors if e["row_index"] < len(df_raw)]
                if bad_idx:
                    st.dataframe(
                        df_raw.iloc[bad_idx].reset_index(drop=False)
                              .rename(columns={"index": "original_row"}),
                        use_container_width=True, hide_index=True,
                    )

        # Build and offer export
        export_rows = []
        for err in errors:
            row = {
                "source_file":        name,
                "original_row_index": err["row_index"],
                "format_detected":    err["format_detected"],
                "parse_error":        err["reason"],
            }
            row.update(err["raw_values"])
            if df_raw is not None and err["row_index"] < len(df_raw):
                for k, v in df_raw.iloc[err["row_index"]].to_dict().items():
                    if k not in row:
                        row[f"raw_{k}"] = v
            export_rows.append(row)

        st.download_button(
            f"⬇ Export conflict rows for {name}",
            data=pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8"),
            file_name=f"wraith_conflicts_{name}_{datetime.date.today().isoformat()}.csv",
            mime="text/csv",
            key=f"dl_conflict_{name}",
        )
        st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# BLUF GENERATOR — combined + per-file
# ─────────────────────────────────────────────────────────────────────────────

def generate_bluf(files_dict, active_names, status_filter):
    today = datetime.date.today().isoformat()

    all_frames = [
        files_dict[n]["df"] for n in active_names if n in files_dict
    ]
    if not all_frames:
        return "No data loaded."

    df_all   = pd.concat(all_frames, ignore_index=True)
    df_all   = df_all[df_all["staleness_status"].isin(status_filter)]
    total    = len(df_all)
    current  = int((df_all["staleness_status"] == "CURRENT").sum())
    review   = int((df_all["staleness_status"] == "REVIEW").sum())
    stale    = int((df_all["staleness_status"] == "STALE").sum())
    expired  = int((df_all["staleness_status"] == "EXPIRED").sum())
    exp_locs = df_all[df_all["staleness_status"] == "EXPIRED"]["location_label"].unique().tolist()
    stl_locs = df_all[df_all["staleness_status"] == "STALE"]["location_label"].unique().tolist()

    region_values = []
    if "region" in df_all.columns:
        region_values = sorted({str(v).strip() for v in df_all["region"].dropna().astype(str) if str(v).strip()})
    region_names = ", ".join(region_values) if region_values else "N/A"

    lines = [
        "=" * 64,
        "WRAITH — CAMERA INTELLIGENCE STALENESS REPORT",
        f"Generated : {today}",
        f"Regions   : {len(region_values)} — {region_names}",
        "=" * 64, "",
        "BOTTOM LINE UP FRONT:",
        f"  {total} total cameras across all active regions.",
        f"  {expired} EXPIRED (>360d) — immediate source-data refresh required.",
        f"  {stale} STALE (180–360d) — re-pull required.",
        f"  {review} REVIEW (90–180d) — schedule re-pull.",
        f"  {current} CURRENT (<90d) — monitor only.", "",
    ]

    if expired > 0:
        lines += ["ACTION REQUIRED — EXPIRED LOCATIONS:"]
        lines += [f"  - {l}" for l in exp_locs[:30]]
        lines += [""]

    if stale > 0:
        lines += ["REVIEW SOON — STALE LOCATIONS:"]
        lines += [f"  - {l}" for l in stl_locs[:30]]
        lines += [""]

    lines += ["─" * 64, "PER-REGION BREAKDOWN:", ""]

    for name in active_names:
        if name not in files_dict:
            continue
        df   = files_dict[name]["df"]
        df   = df[df["staleness_status"].isin(status_filter)]
        errs = len(files_dict[name]["errors"])
        lines += [
            f"  [{name.replace('.csv','').upper()}]",
            f"    Total:   {len(df)}",
            f"    Current: {int((df['staleness_status']=='CURRENT').sum())}",
            f"    Review:  {int((df['staleness_status']=='REVIEW').sum())}",
            f"    Stale:   {int((df['staleness_status']=='STALE').sum())}",
            f"    Expired: {int((df['staleness_status']=='EXPIRED').sum())}",
        ]
        if errs:
            lines += [f"    Coord conflicts: {errs} rows — see Conflicts panel"]
        lines += [""]

    lines += [
        "─" * 64,
        "NEXT REVIEW DATES:",
        f"  90-day  : {(datetime.date.today()+datetime.timedelta(days=90)).isoformat()}",
        f"  180-day : {(datetime.date.today()+datetime.timedelta(days=180)).isoformat()}",
        f"  360-day : {(datetime.date.today()+datetime.timedelta(days=360)).isoformat()}",
        "",
        "=" * 64,
        "ETHICAL USE: Data sourced from approved passive OSINT exports only.",
        "No camera streams accessed. Operator review required before action.",
        "=" * 64,
    ]
    return "\n".join(lines)


def render_collection_schedule(files_dict, active_names, status_filter):
    """COA 1 panel: show per-poc_batch refresh schedule against 90/180/360 thresholds."""
    phone_ui = is_phone_ui()
    frames = []
    for name in active_names:
        if name not in files_dict:
            continue
        df = files_dict[name]["df"].copy()
        df = df[df["staleness_status"].isin(status_filter)]
        if df.empty:
            continue
        df["source_file"] = name
        frames.append(df)

    if not frames:
        st.info("No active rows available for collection schedule.")
        return

    df_all = pd.concat(frames, ignore_index=True)
    if "poc_batch" not in df_all.columns:
        st.info("Collection schedule unavailable: `poc_batch` column is missing.")
        return

    df_all["poc_batch"] = df_all["poc_batch"].astype(str).str.strip()
    df_all = df_all[df_all["poc_batch"] != ""]
    if df_all.empty:
        st.info("Collection schedule unavailable: no populated `poc_batch` values in active data.")
        return

    today = datetime.date.today()
    df_all["_last_seen_dt"] = df_all["last_seen"].apply(parse_last_seen_date)

    rows = []
    for batch, sub in df_all.groupby("poc_batch", dropna=True):
        sub_valid = sub[sub["_last_seen_dt"].notna()].copy()

        if sub_valid.empty:
            oldest_date = None
            age_days = None
        else:
            oldest_date = sub_valid["_last_seen_dt"].min()
            age_days = int((today - oldest_date).days)

        regions = []
        if "region" in sub.columns:
            regions = sorted({str(v).strip() for v in sub["region"].dropna().astype(str) if str(v).strip()})

        rows.append(
            {
                "poc_batch": batch,
                "rows": int(len(sub)),
                "regions": ", ".join(regions) if regions else "N/A",
                "oldest_last_seen": oldest_date.isoformat() if oldest_date else "N/A",
                "oldest_age_days": age_days if age_days is not None else "N/A",
                "to_90d": (max(0, 90 - age_days) if age_days is not None else "N/A"),
                "to_180d": (max(0, 180 - age_days) if age_days is not None else "N/A"),
                "to_360d": (max(0, 360 - age_days) if age_days is not None else "N/A"),
                "current": int((sub["staleness_status"] == "CURRENT").sum()),
                "review": int((sub["staleness_status"] == "REVIEW").sum()),
                "stale": int((sub["staleness_status"] == "STALE").sum()),
                "expired": int((sub["staleness_status"] == "EXPIRED").sum()),
            }
        )

    sched_df = pd.DataFrame(rows).sort_values(by=["expired", "stale", "review", "rows"], ascending=False)
    if phone_ui:
        compact_cols = [
            c for c in [
                "poc_batch", "rows", "oldest_age_days", "to_90d", "to_180d", "to_360d", "expired"
            ] if c in sched_df.columns
        ]
        st.dataframe(sched_df[compact_cols], use_container_width=True, hide_index=True)
    else:
        st.dataframe(sched_df, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇ Collection Schedule CSV",
        data=sched_df.to_csv(index=False).encode("utf-8"),
        file_name=f"wraith_collection_schedule_{today.isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────────────────────────────────

def send_email_alert(subject, body):
    sender    = os.getenv("ALERT_EMAIL_FROM")
    password  = os.getenv("ALERT_EMAIL_PASSWORD")
    recipient = os.getenv("ALERT_EMAIL_TO")
    if not all([sender, password, recipient]):
        return False, "Email credentials not configured in .env"
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = recipient
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())
        return True, "Email sent."
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar(files_dict):
    phone_ui = is_phone_ui()
    tablet_ui = is_tablet_ui()

    st.sidebar.markdown(
        '<p style="font-family:\'Share Tech Mono\',monospace;font-size:0.75rem;'
        'letter-spacing:0.12em;color:#475569;text-transform:uppercase;">'
        'WRAITH // Controls</p>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("pilot_authed", False):
        if st.sidebar.button("Lock Session", use_container_width=True):
            st.session_state.pilot_authed = False
            st.session_state.admin_metrics_ok = False
            st.session_state.files = {}
            st.rerun()

        # Auth diagnostics (safe): show gate/source state without exposing secrets.
        with st.sidebar.expander("Auth Diagnostics", expanded=False):
            has_pilot_password = bool(_safe_secret("PILOT_ACCESS_PASSWORD", os.getenv("PILOT_ACCESS_PASSWORD", "")).strip())
            has_legacy_password = bool(_safe_secret("ACCESS_PASSWORD", os.getenv("ACCESS_PASSWORD", "")).strip())
            source_key = "PILOT_ACCESS_PASSWORD" if has_pilot_password else ("ACCESS_PASSWORD" if has_legacy_password else "none")
            st.caption(f"Pilot gate enabled: {'yes' if (_env_bool('PILOT_ACCESS_ENABLED', False) or has_pilot_password or has_legacy_password) else 'no'}")
            st.caption(f"Password source key: {source_key}")
            st.caption(f"Lockout seconds: {max(5, int(os.getenv('PILOT_LOCKOUT_SECONDS', '15')))}")
        st.sidebar.markdown("---")

    # ── Upload ────────────────────────────────────────────────────────────────
    uploaded_files = st.sidebar.file_uploader(
        "Upload region CSV(s)",
        type=["csv"],
        accept_multiple_files=True,
        help=(
            "Upload one or more CSVs simultaneously. "
            "Each file becomes an independent toggleable layer. "
            "Accepts decimal, MGRS, DMS, UTM, or combined lat/lon formats."
        ),
    )

    # ── Bundled Test Data on/off toggle ──────────────────────────────────────
    _bundled_on = st.sidebar.toggle(
        "Bundled Test Data",
        value=False,
        key="bundled_test_toggle",
        help="Load all bundled WRAITH sample CSVs as layers. Toggle off to remove them.",
    )
    bundled_paths = [str(p) for p in discover_fixture_files()] if _bundled_on else []

    st.sidebar.markdown("---")

    # ── Primary navigation (View) ─────────────────────────────────────────────
    st.sidebar.markdown('<div class="section-label">View</div>', unsafe_allow_html=True)
    view_options = ["Globe", "Flat Map", "Heatmap", "Data Table", "Conflicts", "Alerts & Export"]
    if st.session_state.admin_metrics_ok:
        view_options.append("Metrics")
    view = st.sidebar.radio(
        "Panel",
        options=view_options,
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")

    # ── Filters ───────────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="section-label">Filters</div>', unsafe_allow_html=True)

    status_filter = st.sidebar.multiselect(
        "Staleness",
        options=STALENESS_ORDER,
        default=STALENESS_ORDER,
    )

    country_filter = []
    if files_dict:
        all_countries = sorted(set(
            c for fd in files_dict.values()
            for c in fd["df"]["country"].dropna().unique()
        ))
        if all_countries:
            country_filter = st.sidebar.multiselect(
                "Country", options=all_countries, default=all_countries,
            )

    st.sidebar.markdown("---")

    # ── Layer controls — one row per loaded file ──────────────────────────────
    active_names = []
    _to_remove = []
    if files_dict:
        with st.sidebar.expander("Layers", expanded=not phone_ui):
            for name, fdata in files_dict.items():
                conflict_note = f" · ⚡ {len(fdata['errors'])} conflicts" if fdata["errors"] else ""
                label = f"{name.replace('.csv', '')}  ({len(fdata['df'])} cameras{conflict_note})"
                loaded = st.toggle(
                    label,
                    value=True,
                    key=f"layer_{name}",
                    help="Toggle off to remove this file.",
                )
                if loaded:
                    active_names.append(name)
                else:
                    _to_remove.append(name)

    if _to_remove:
        for _n in _to_remove:
            st.session_state.files.pop(_n, None)
        st.rerun()

    st.sidebar.markdown("---")

    # ── Advanced controls (collapsed on phone) ───────────────────────────────
    advanced_expanded = not phone_ui and not tablet_ui
    with st.sidebar.expander("Advanced Controls", expanded=advanced_expanded):
        # Map options
        st.markdown('<div class="section-label">Map Options</div>', unsafe_allow_html=True)

        # Email alerts
        st.markdown('<div class="section-label">Email Alerts</div>', unsafe_allow_html=True)
        email_enabled = st.toggle(
            "Enable email alerts", value=False,
            help="Set ALERT_EMAIL_FROM / _PASSWORD / _TO in .env",
        )
        if email_enabled:
            if st.button("Send test email"):
                ok, msg = send_email_alert("WRAITH — Test Alert", "Test alert from WRAITH.")
                st.success("Sent.") if ok else st.error(msg)

        st.markdown("---")

        # Admin access (metrics)
        st.markdown('<div class="section-label">Admin Access</div>', unsafe_allow_html=True)
        admin_phrase = os.getenv("ADMIN_METRICS_PASSPHRASE", "wraith")
        admin_input = st.text_input("Metrics passphrase", type="password", key="admin_metrics_phrase_input")
        a1, a2 = st.columns(2)
        with a1:
            if st.button("Unlock", use_container_width=True):
                if admin_input and admin_input == admin_phrase:
                    st.session_state.admin_metrics_ok = True
                    st.success("Admin metrics unlocked")
                else:
                    st.session_state.admin_metrics_ok = False
                    st.error("Invalid passphrase")
        with a2:
            if st.button("Lock", use_container_width=True):
                st.session_state.admin_metrics_ok = False

    auto_rotate = False
    heat_tile_style = "Dark (CartoDB)"
    heat_use_cluster = True
    heat_marker_radius = 6
    heat_radius = 20
    heat_show_minimap = not phone_ui

    if view == "Globe":
        auto_rotate = st.toggle("Auto-rotate", value=False)
    elif view == "Heatmap":
        heat_tile_style = st.selectbox(
            "Basemap",
            options=list(HEATMAP_TILES.keys()),
            index=0,
            help="Switch to a more detailed base map (street, terrain, satellite, etc.).",
        )
        heat_use_cluster = st.toggle(
            "Cluster markers",
            value=not phone_ui,
            help="Group nearby cameras at low zoom for denser regions.",
        )
        heat_show_minimap = st.toggle(
            "Show minimap",
            value=not phone_ui,
            help="Display a small overview map for quicker navigation.",
        )
        heat_marker_radius = st.slider(
            "Marker size",
            min_value=4,
            max_value=10,
            value=5 if phone_ui else 6,
        )
        heat_radius = st.slider(
            "Heat radius",
            min_value=10,
            max_value=35,
            value=16 if phone_ui else 20,
        )

    return (
        uploaded_files, bundled_paths, view, auto_rotate,
        status_filter, country_filter, email_enabled, active_names,
        heat_tile_style, heat_use_cluster, heat_marker_radius, heat_radius, heat_show_minimap,
        st.session_state.admin_metrics_ok,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    init_session()
    apply_splash_background()
    require_pilot_access()
    ui_profile = get_ui_profile()

    # ── Header ────────────────────────────────────────────────────────────────
    if True:
        st.markdown(
            '<div class="cw-header">'
            '<h1>◈ WRAITH</h1>'
            '<span class="cw-sub">Wide-area Reconnaissance & Asset Intelligence Tracking Hub</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="brand-subline">Wide-area Reconnaissance & Asset Intelligence Tracking Hub</div>',
            unsafe_allow_html=True,
        )

    st.caption(f"UI profile: {ui_profile} (set with ?ui=phone | ?ui=tablet | ?ui=desktop)")

    files_dict = st.session_state.files

    # ── Sidebar ───────────────────────────────────────────────────────────────
    (uploaded_files, bundled_paths, view, auto_rotate,
     status_filter, country_filter, email_enabled, active_names,
     heat_tile_style, heat_use_cluster, heat_marker_radius, heat_radius, heat_show_minimap,
     admin_metrics_ok) = render_sidebar(files_dict)

    # ── Bundled toggle: unload files removed when toggled off ─────────────────
    _bundled_names = {Path(p).name for p in bundled_paths}
    _prev_bundled = st.session_state.get("_bundled_active_names", set())
    _removed = _prev_bundled - _bundled_names
    if _removed:
        for _bn in _removed:
            st.session_state.files.pop(_bn, None)
        st.session_state["_bundled_active_names"] = set()
        st.rerun()
    st.session_state["_bundled_active_names"] = _bundled_names

    # Build a unified list of incoming files from uploader + bundled toggle.
    incoming_files = list(uploaded_files) if uploaded_files else []
    for _bp in bundled_paths:
        if Path(_bp).name not in st.session_state.files:
            incoming_files.append(_bp)

    # ── Ingest newly uploaded files ───────────────────────────────────────────
    if incoming_files:
        for incoming in incoming_files:
            is_local_path = isinstance(incoming, str)

            if is_local_path:
                fname = Path(incoming).name
            else:
                uf = incoming
                fname = uf.name

            if fname in files_dict:
                continue  # already loaded — skip duplicate

            try:
                color = next_color()  # assign before adding to dict

                if is_local_path:
                    with open(incoming, "rb") as f:
                        df_clean, detection_info, errors = load_csv(f)
                    df_raw = pd.read_csv(incoming, dtype=str)
                else:
                    df_clean, detection_info, errors = load_csv(uf)
                    uf.seek(0)
                    df_raw = pd.read_csv(uf, dtype=str)

                df_clean = compute_staleness(df_clean)

                st.session_state.files[fname] = {
                    "df":             df_clean,
                    "df_raw":         df_raw,
                    "errors":         errors,
                    "detection_info": detection_info,
                    "color":          color,
                    "loaded_at":      datetime.date.today().isoformat(),
                }
                st.session_state.email_sent = False

            except ValueError as e:
                st.error(f"Error loading {fname}: {e}")

        # Refresh references after possible additions
        files_dict = st.session_state.files
        active_names = [n for n in files_dict if n in active_names or True]
        active_names = list(files_dict.keys())  # default all visible on first load

    # ── No data state ─────────────────────────────────────────────────────────
    if not files_dict:
        st.markdown(
            '<div class="alert-banner alert-info">'
            '⬆ Upload one or more region CSVs using the sidebar. '
            'Each file loads as an independent toggleable layer. '
            'Accepts decimal degrees, MGRS, DMS, UTM, or combined lat/lon.'
            '</div>',
            unsafe_allow_html=True,
        )
        with st.expander("Supported coordinate formats — Training Guide"):
            st.caption("Toggle each format on to reveal a detailed training example.")
            _FORMAT_TRAINING = {
                "Decimal Degrees": {
                    "columns": "`lat`, `lon`, `latitude`, `longitude`",
                    "example": "`38.8951` / `-77.0364`",
                    "notes": "Most common format. Provide separate lat and lon columns with signed decimal values. Negative lon = West, negative lat = South.",
                    "csv": (
                        "ip,latitude,longitude,device_type,model,location_label,"
                        "last_seen,port,org,country\n"
                        "192.168.10.1,38.8951,-77.0364,IP Camera,Hikvision DS-2CD2085G1,"
                        "Pentagon Area,2026-01-15,554,Comcast,US\n"
                        "10.0.0.5,40.7128,-74.0060,PTZ Camera,Axis P5655-E,"
                        "Times Square,2025-09-10,80,Verizon,US"
                    ),
                },
                "MGRS": {
                    "columns": "`mgrs`, `grid`, `grid_ref`",
                    "example": "`18SUJ2338308450`",
                    "notes": "Military Grid Reference System. Single column. Zone + band + 100km square + easting + northing (even digit count).",
                    "csv": (
                        "ip,mgrs,device_type,model,location_label,"
                        "last_seen,port,org,country\n"
                        "10.0.0.5,18SUJ2338308450,PTZ Camera,Axis P5655-E,"
                        "Capitol Hill,2026-01-20,80,Verizon,US\n"
                        "172.16.0.3,18SUJ2284608900,Dome Camera,Dahua SD49425XB,"
                        "Pentagon,2025-09-10,8080,AT&T,US"
                    ),
                },
                "DMS (Degrees Minutes Seconds)": {
                    "columns": "`dms_lat`, `dms_lon`",
                    "example": "`38°53'42\"N` / `77°01'58\"W`",
                    "notes": "Requires two separate columns. Hemisphere suffix (N/S/E/W) is mandatory. Quote fields in CSV if they contain special characters.",
                    "csv": (
                        "ip,dms_lat,dms_lon,device_type,model,location_label,"
                        "last_seen,port,org,country\n"
                        "172.16.0.3,\"38°53'42\"\"N\",\"77°01'58\"\"W\",Dome Camera,"
                        "Dahua SD49425XB,Pentagon,2025-09-10,8080,AT&T,US"
                    ),
                },
                "UTM (Universal Transverse Mercator)": {
                    "columns": "`utm`, `utm_coord`",
                    "example": "`18N 323830 4308450`",
                    "notes": "Single column. Format: zone + hemisphere letter + space + easting + space + northing.",
                    "csv": (
                        "ip,utm_coord,device_type,model,location_label,"
                        "last_seen,port,org,country\n"
                        "10.10.1.7,18N 323830 4308450,IP Camera,Bosch FLEXIDOME,"
                        "Times Square,2025-07-04,554,Spectrum,US"
                    ),
                },
                "Combined Lat/Lon": {
                    "columns": "`coordinates`, `lat/lon`, `lat_lon`, `coord`, `coords`",
                    "example": '`"38.8951, -77.0364"`',
                    "notes": "Single column containing lat and lon as a comma-separated string. Must be quoted in CSV because it contains a comma.",
                    "csv": (
                        "ip,coordinates,device_type,model,location_label,"
                        "last_seen,port,org,country\n"
                        '100.65.2.20,"38.9072, -77.0369",IP Camera,Axis Q6135-LE,'
                        "Capitol Hill,2026-01-20,554,Comcast,US\n"
                        '100.65.2.21,"29.7604, -95.3698",PTZ Camera,Sony SNC-EP580,'
                        "Houston Galleria,2025-08-22,80,AT&T,US"
                    ),
                },
            }
            for _fmt_name, _fmt in _FORMAT_TRAINING.items():
                _show = st.toggle(_fmt_name, value=False, key=f"_fmt_toggle_{_fmt_name}")
                if _show:
                    st.markdown(f"**Accepted columns:** {_fmt['columns']}")
                    st.markdown(f"**Example value:** {_fmt['example']}")
                    st.markdown(f"**Usage note:** {_fmt['notes']}")
                    st.code(_fmt["csv"], language="text")
                    st.divider()
        return

    # ── Coordinate format badges (one per loaded file) ────────────────────────
    badge_html = " ".join(
        f'<span class="detect-tag" title="{name}">'
        f'{name.replace(".csv","")}: {describe_detection(fd["detection_info"])}'
        f'</span>'
        for name, fd in files_dict.items()
    )
    st.markdown(badge_html, unsafe_allow_html=True)

    # ── Apply country filter to active layers ─────────────────────────────────
    # Country filter narrows rows within each file; does not remove files
    if country_filter:
        filtered_dict = {}
        for name, fd in files_dict.items():
            if name not in active_names:
                continue
            fd_copy = dict(fd)
            fd_copy["df"] = fd["df"][fd["df"]["country"].isin(country_filter)]
            filtered_dict[name] = fd_copy
    else:
        filtered_dict = {n: files_dict[n] for n in active_names if n in files_dict}

    # ── KPI cards ─────────────────────────────────────────────────────────────
    total, current, review, stale, expired, region_count, layer_count = render_kpis(filtered_dict, active_names, status_filter)

    # ── Top-level alert banners ───────────────────────────────────────────────
    if expired > 0:
        # Collect expired locations across all active files
        exp_locs = []
        for fd in filtered_dict.values():
            df = fd["df"][fd["df"]["staleness_status"] == "EXPIRED"]
            exp_locs.extend(df["location_label"].unique().tolist())
        loc_str = ", ".join(str(l) for l in exp_locs[:5])
        if len(exp_locs) > 5:
            loc_str += f" +{len(exp_locs)-5} more"
        st.markdown(
            f'<div class="alert-banner alert-red">'
            f'🔴 <b>IMMEDIATE ACTION:</b> {expired} camera(s) expired (&gt;360d) across '
            f'{len([n for n in active_names if (filtered_dict.get(n,{}).get("df") is not None and (filtered_dict[n]["df"]["staleness_status"]=="EXPIRED").any())])} '
            f'region(s). Locations: {loc_str}</div>',
            unsafe_allow_html=True,
        )

    if review > 0:
        rv_locs = []
        for fd in filtered_dict.values():
            df = fd["df"][fd["df"]["staleness_status"] == "REVIEW"]
            rv_locs.extend(df["location_label"].unique().tolist())
        loc_str = ", ".join(str(l) for l in rv_locs[:5])
        if len(rv_locs) > 5:
            loc_str += f" +{len(rv_locs)-5} more"
        st.markdown(
            f'<div class="alert-banner alert-yellow">'
            f'🟡 <b>REVIEW SOON:</b> {review} camera(s) at 90–180 days. '
            f'Locations: {loc_str}</div>',
            unsafe_allow_html=True,
        )

    if stale > 0:
        stl_locs = []
        for fd in filtered_dict.values():
            df = fd["df"][fd["df"]["staleness_status"] == "STALE"]
            stl_locs.extend(df["location_label"].unique().tolist())
        loc_str = ", ".join(str(l) for l in stl_locs[:5])
        if len(stl_locs) > 5:
            loc_str += f" +{len(stl_locs)-5} more"
        st.markdown(
            f'<div class="alert-banner alert-warn">'
            f'🟠 <b>STALE:</b> {stale} camera(s) at 180–360 days. Re-pull required. '
            f'Locations: {loc_str}</div>',
            unsafe_allow_html=True,
        )

    total_conflicts = sum(len(fd["errors"]) for fd in files_dict.values())
    if total_conflicts > 0:
        st.markdown(
            f'<div class="alert-banner alert-warn">'
            f'⚡ {total_conflicts} coordinate conflict(s) across '
            f'{sum(1 for fd in files_dict.values() if fd["errors"])} file(s). '
            f'See the Conflicts panel.</div>',
            unsafe_allow_html=True,
        )

    # ── Auto email on load ────────────────────────────────────────────────────
    if email_enabled and expired > 0 and not st.session_state.email_sent:
        bluf = generate_bluf(filtered_dict, active_names, status_filter)
        ok, msg = send_email_alert("WRAITH — Expired Camera Data Alert", bluf)
        st.session_state.email_sent = True
        st.toast("Alert email sent." if ok else f"Email failed: {msg}",
                 icon="✉" if ok else "⚠")

    st.markdown("---")

    # ── PANELS ────────────────────────────────────────────────────────────────

    if view == "Globe":
        st.markdown('<div class="section-label">Globe — Orthographic Projection</div>',
                    unsafe_allow_html=True)
        st.caption("Drag to orbit · Scroll to zoom · Hover for details · "
                   "Dot fill = region · Ring = staleness")
        render_globe(filtered_dict, active_names, status_filter, auto_rotate)

    elif view == "Flat Map":
        st.markdown('<div class="section-label">Flat Map — Natural Earth Projection</div>',
                    unsafe_allow_html=True)
        st.caption("All regions visible simultaneously · Scroll to zoom · "
                   "Dot fill = region · Ring = staleness")
        render_flat_map(filtered_dict, active_names, status_filter)

    elif view == "Heatmap":
        st.markdown('<div class="section-label">Heatmap — Staleness Density</div>',
                    unsafe_allow_html=True)
        st.caption("Toggle region layers in the map's top-right control · "
                   "Click any dot for popup details")
        render_heatmap(
            filtered_dict,
            active_names,
            status_filter,
            tile_style=heat_tile_style,
            use_cluster=heat_use_cluster,
            marker_radius=heat_marker_radius,
            heat_radius=heat_radius,
            show_minimap=heat_show_minimap,
        )

    elif view == "Data Table":
        st.markdown('<div class="section-label">Data Table</div>', unsafe_allow_html=True)
        phone_ui = is_phone_ui()
        tablet_ui = is_tablet_ui()

        # Merge all active files with a source_file column
        all_frames = []
        for name in active_names:
            if name not in filtered_dict:
                continue
            df = filtered_dict[name]["df"].copy()
            df["source_file"] = name
            all_frames.append(df)

        if not all_frames:
            st.info("No data matches current filters.")
        else:
            df_table = pd.concat(all_frames, ignore_index=True)
            if phone_ui:
                show_cols = [
                    "source_file", "location_label", "staleness_status",
                    "country", "last_seen",
                ]
            elif tablet_ui:
                show_cols = [
                    "source_file", "ip", "location_label", "model",
                    "last_seen", "age_months", "staleness_status", "country",
                ]
            else:
                show_cols = [
                    "source_file", "ip", "location_label", "device_type",
                    "model", "last_seen", "age_months", "staleness_status",
                    "country", "port", "org",
                ]
            available = [c for c in show_cols if c in df_table.columns]

            def style_status(val):
                return {
                    "CURRENT": "color:#22c55e;font-weight:600",
                    "REVIEW":  "color:#eab308;font-weight:600",
                    "STALE":   "color:#f97316;font-weight:600",
                    "EXPIRED": "color:#ef4444;font-weight:600",
                }.get(val, "")

            st.dataframe(
                df_table[available].style.map(
                    style_status, subset=["staleness_status"]
                ),
                use_container_width=True, height=520, hide_index=True,
            )

            st.download_button(
                "⬇ Download filtered CSV (all regions)",
                data=df_table[available].to_csv(index=False).encode("utf-8"),
                file_name=f"wraith_combined_{datetime.date.today().isoformat()}.csv",
                mime="text/csv",
            )

    elif view == "Conflicts":
        st.markdown('<div class="section-label">Coordinate Conflict Review</div>',
                    unsafe_allow_html=True)
        render_conflicts(files_dict)

    elif view == "Alerts & Export":
        st.markdown('<div class="section-label">Alerts & Export</div>', unsafe_allow_html=True)
        phone_ui = is_phone_ui()
        tablet_ui = is_tablet_ui()

        bluf_text = generate_bluf(filtered_dict, active_names, status_filter)
        st.text_area("BLUF Summary", value=bluf_text, height=300 if phone_ui else 400)

        st.markdown("---")
        st.markdown('<div class="section-label">Collection Schedule (by poc_batch)</div>', unsafe_allow_html=True)
        render_collection_schedule(filtered_dict, active_names, status_filter)

        if phone_ui:
            col1 = col2 = col3 = None
        else:
            col1, col2, col3 = st.columns(3)

        if phone_ui:
            st.download_button(
                "⬇ BLUF Report (.txt)",
                data=bluf_text,
                file_name=f"wraith_bluf_{datetime.date.today().isoformat()}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            with col1:
                st.download_button(
                    "⬇ BLUF Report (.txt)",
                    data=bluf_text,
                    file_name=f"wraith_bluf_{datetime.date.today().isoformat()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        def _render_full_dataset_btn():
            all_frames = []
            for name in active_names:
                if name not in filtered_dict:
                    continue
                df = filtered_dict[name]["df"].copy()
                df["source_file"] = name
                all_frames.append(df)

            if all_frames:
                combined_csv = pd.concat(all_frames, ignore_index=True)\
                                 .to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇ Full Dataset CSV",
                    data=combined_csv,
                    file_name=f"wraith_full_{datetime.date.today().isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        if phone_ui:
            _render_full_dataset_btn()
        else:
            with col2:
                _render_full_dataset_btn()

        def _render_conflicts_btn():
            all_conflicts = []
            for name, fd in files_dict.items():
                for err in fd["errors"]:
                    row = {
                        "source_file":        name,
                        "original_row_index": err["row_index"],
                        "format_detected":    err["format_detected"],
                        "parse_error":        err["reason"],
                    }
                    row.update(err["raw_values"])
                    all_conflicts.append(row)

            if all_conflicts:
                st.download_button(
                    f"⬇ All Conflicts CSV ({len(all_conflicts)})",
                    data=pd.DataFrame(all_conflicts).to_csv(index=False).encode("utf-8"),
                    file_name=f"camwatch_all_conflicts_{datetime.date.today().isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.button("No conflicts to export", disabled=True, use_container_width=True)

        if phone_ui:
            _render_conflicts_btn()
        else:
            with col3:
                _render_conflicts_btn()

        st.markdown("---")
        st.markdown('<div class="section-label">Manual Email Send</div>', unsafe_allow_html=True)

        if email_enabled:
            if st.button("Send BLUF via Email Now"):
                ok, msg = send_email_alert(
                    f"WRAITH Report — {datetime.date.today().isoformat()}",
                    bluf_text,
                )
                st.success("Email sent.") if ok else st.error(f"Failed: {msg}")
        else:
            st.caption("Enable 'Email Alerts' in the sidebar to unlock manual send.")

    elif view == "Metrics":
        if not admin_metrics_ok:
            st.warning("Admin metrics are locked. Unlock using the sidebar passphrase.")
        else:
            render_metrics_panel(files_dict, filtered_dict, active_names, status_filter)


if __name__ == "__main__":
    main()
