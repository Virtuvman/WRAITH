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
from pathlib import Path
import datetime
import smtplib
import logging
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

from modules.ingestion import load_csv
from modules.coord_normalizer import describe_detection

load_dotenv()
logging.basicConfig(level=logging.INFO)

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

# Ring color + width encodes staleness on every dot, regardless of file color
STALENESS_RING = {
    "FRESH":   {"color": "#22c55e", "width": 1.0, "opacity": 0.92},
    "STALE":   {"color": "#eab308", "width": 2.2, "opacity": 0.80},
    "EXPIRED": {"color": "#ef4444", "width": 3.5, "opacity": 0.65},
}

HEATMAP_TILES = {
    "Dark (CartoDB)": {"tiles": "CartoDB dark_matter", "attr": "CartoDB"},
    "Light (CartoDB)": {"tiles": "CartoDB positron", "attr": "CartoDB"},
    "Street (OpenStreetMap)": {"tiles": "OpenStreetMap", "attr": "OpenStreetMap"},
    "Terrain": {"tiles": "Stamen Terrain", "attr": "Stamen"},
    "Satellite": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Tiles © Esri",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="WRAITH",
    page_icon="👻",
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
    display:flex; align-items:baseline; gap:14px;
    padding:0.4rem 0 1.2rem;
    border-bottom:1px solid rgba(255,255,255,0.08);
    margin-bottom:1.2rem;
}
.cw-header h1 {
    font-family:'Share Tech Mono',monospace; font-size:1.5rem;
    font-weight:400; letter-spacing:0.12em; color:#e2e8f0; margin:0;
}
.cw-header .cw-sub {
    font-size:0.72rem; color:#64748b;
    letter-spacing:0.08em; text-transform:uppercase;
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
.kpi-card.red    .kpi-num { color:#ef4444; }

.file-table { width:100%; border-collapse:collapse; font-size:0.78rem; margin-top:0.4rem; }
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


def next_color():
    """Return the next unused layer color based on how many files are loaded."""
    return FILE_COLORS[len(st.session_state.files) % len(FILE_COLORS)]


def _parse_last_seen_date(value) -> datetime.date | None:
    """Parse common date formats (including Excel serial dates) safely."""
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    # Fast path for ISO-like values (YYYY-MM-DD or ISO datetime variants).
    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        pass

    # Try full ISO datetime strings (including trailing Z).
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        pass

    # Common non-ISO exports.
    for fmt in (
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%b %d %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            continue

    # Excel serial date fallback (days since 1899-12-30).
    try:
        serial = float(s)
        if 20000 <= serial <= 80000:
            return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(serial)))
    except Exception:
        pass

    return None


# ─────────────────────────────────────────────────────────────────────────────
# STALENESS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def compute_staleness(df):
    today = datetime.date.today()
    statuses, colors, classes, ages = [], [], [], []
    for _, row in df.iterrows():
        try:
            last = _parse_last_seen_date(row.get("last_seen", ""))
            if last is None:
                raise ValueError("Unparseable last_seen")
            months = (today - last).days / 30.44
        except Exception:
            months = 999
        if months < 3:
            statuses.append("FRESH");   colors.append("#22c55e"); classes.append("green")
        elif months < 6:
            statuses.append("STALE");   colors.append("#eab308"); classes.append("yellow")
        else:
            statuses.append("EXPIRED"); colors.append("#ef4444"); classes.append("red")
        ages.append(round(months, 1))
    df = df.copy()
    df["staleness_status"] = statuses
    df["color_hex"]        = colors
    df["color_class"]      = classes
    df["age_months"]       = ages
    return df


# ─────────────────────────────────────────────────────────────────────────────
# GLOBE VIEW
# Per-file traces, staleness encoded as ring color/width on each dot.
# Legend groups by file; each status is a sub-entry within that group.
# ─────────────────────────────────────────────────────────────────────────────

def render_globe(files_dict, active_names, status_filter, auto_rotate=False):
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
        for status in ["FRESH", "STALE", "EXPIRED"]:
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
    fig.update_layout(
        height=560, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="v", x=1.01, y=1, xanchor="left",
            font=dict(size=10, color="#94a3b8"),
            bgcolor="rgba(15,23,42,0.75)",
            bordercolor="rgba(255,255,255,0.1)", borderwidth=1,
            groupclick="toggleitem",
        ),
        dragmode="orbit",
    )

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
        for status in ["FRESH", "STALE", "EXPIRED"]:
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
    fig.update_layout(
        height=540, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="v", x=1.01, y=1, xanchor="left",
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

    weight_map = {"EXPIRED": 3, "STALE": 2, "FRESH": 1}

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

    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    st_folium(m, use_container_width=True, height=560, returned_objects=[])

    # Legend row below map
    _render_file_legend(files_dict, active_names, show_ring_key=True)


# ─────────────────────────────────────────────────────────────────────────────
# FILE COLOR LEGEND
# ─────────────────────────────────────────────────────────────────────────────

def _render_file_legend(files_dict, active_names, show_ring_key=False):
    swatches = " &nbsp; ".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;font-size:0.75rem;color:#94a3b8">'
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
            '<span style="color:#22c55e">●</span> Fresh &nbsp;'
            '<span style="color:#eab308">●</span> Stale &nbsp;'
            '<span style="color:#ef4444">●</span> Expired</span>'
        )
    st.markdown(
        f'<div style="margin-top:0.5rem;padding:0.3rem 0">{swatches}{ring_key}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS — combined totals + per-file breakdown
# ─────────────────────────────────────────────────────────────────────────────

def render_kpis(files_dict, active_names, status_filter):
    total = fresh = stale = expired = 0
    file_rows = []

    for name in active_names:
        if name not in files_dict:
            continue
        df = files_dict[name]["df"]
        df = df[df["staleness_status"].isin(status_filter)]
        f  = int((df["color_class"] == "green").sum())
        s  = int((df["color_class"] == "yellow").sum())
        e  = int((df["color_class"] == "red").sum())
        t  = len(df)
        total   += t
        fresh   += f
        stale   += s
        expired += e
        file_rows.append((name, files_dict[name]["color"], t, f, s, e))

    st.markdown(
        f'<div class="kpi-row">'
        f'<div class="kpi-card total"><div class="kpi-num">{total}</div>'
        f'<div class="kpi-lbl">Total Cameras</div></div>'
        f'<div class="kpi-card green"><div class="kpi-num">{fresh}</div>'
        f'<div class="kpi-lbl">Fresh &lt;3mo</div></div>'
        f'<div class="kpi-card yellow"><div class="kpi-num">{stale}</div>'
        f'<div class="kpi-lbl">Stale 3–6mo</div></div>'
        f'<div class="kpi-card red"><div class="kpi-num">{expired}</div>'
        f'<div class="kpi-lbl">Expired &gt;6mo</div></div>'
        f'<div class="kpi-card total"><div class="kpi-num">{len(active_names)}</div>'
        f'<div class="kpi-lbl">Regions</div></div>'
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
                f'<td style="text-align:center;color:#22c55e">{f}</td>'
                f'<td style="text-align:center;color:#eab308">{s}</td>'
                f'<td style="text-align:center;color:#ef4444">{e}</td>'
                f'</tr>'
                for name, color, t, f, s, e in file_rows
            )
            st.markdown(
                f'<table class="file-table"><thead><tr>'
                f'<th>Region / File</th><th>Total</th>'
                f'<th>Fresh</th><th>Stale</th><th>Expired</th>'
                f'</tr></thead><tbody>{rows_html}</tbody></table>',
                unsafe_allow_html=True,
            )

    return total, fresh, stale, expired


# ─────────────────────────────────────────────────────────────────────────────
# CONFLICTS PANEL — per-file coordinate conflict reporting
# ─────────────────────────────────────────────────────────────────────────────

def render_conflicts(files_dict):
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
            f'<span class="cc-reason">{err["reason"]}</span><br>'
            f'<span style="color:#64748b;font-size:0.71rem">'
            f'Raw: {" | ".join(f"{k}:{v}" for k,v in err["raw_values"].items()) or "N/A"}'
            f'</span></div>'
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
    fresh    = int((df_all["color_class"] == "green").sum())
    stale    = int((df_all["color_class"] == "yellow").sum())
    expired  = int((df_all["color_class"] == "red").sum())
    exp_locs = df_all[df_all["color_class"]=="red"]["location_label"].unique().tolist()
    stl_locs = df_all[df_all["color_class"]=="yellow"]["location_label"].unique().tolist()

    region_names = ", ".join(n.replace(".csv", "") for n in active_names)

    lines = [
        "=" * 64,
        "WRAITH — CAMERA INTELLIGENCE STALENESS REPORT",
        f"Generated : {today}",
        f"Regions   : {len(active_names)} — {region_names}",
        "=" * 64, "",
        "BOTTOM LINE UP FRONT:",
        f"  {total} total cameras across all active regions.",
        f"  {expired} EXPIRED (>6mo)  — immediate source-data refresh required.",
        f"  {stale} STALE (3–6mo) — schedule review within 30 days.",
        f"  {fresh} FRESH (<3mo)  — no action required.", "",
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
            f"    Fresh:   {int((df['color_class']=='green').sum())}",
            f"    Stale:   {int((df['color_class']=='yellow').sum())}",
            f"    Expired: {int((df['color_class']=='red').sum())}",
        ]
        if errs:
            lines += [f"    Coord conflicts: {errs} rows — see Conflicts panel"]
        lines += [""]

    lines += [
        "─" * 64,
        "NEXT REVIEW DATES:",
        f"  3-month : {(datetime.date.today()+datetime.timedelta(days=90)).isoformat()}",
        f"  6-month : {(datetime.date.today()+datetime.timedelta(days=180)).isoformat()}",
        "",
        "=" * 64,
        "ETHICAL USE: Data sourced from approved passive OSINT exports only.",
        "No camera streams accessed. Operator review required before action.",
        "=" * 64,
    ]
    return "\n".join(lines)


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
    st.sidebar.markdown(
        '<p style="font-family:\'Share Tech Mono\',monospace;font-size:0.75rem;'
        'letter-spacing:0.12em;color:#475569;text-transform:uppercase;">'
        'WRAITH // Controls</p>',
        unsafe_allow_html=True,
    )

    # ── Multi-file uploader ───────────────────────────────────────────────────
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

    # Quick local sample loaders (avoids file-picker confusion)
    st.sidebar.caption("Quick load local samples")
    load_sample_decimal = st.sidebar.button(
        "Load sample_cameras_decimal.csv",
        help="Loads the project-root sample file directly into WRAITH.",
    )
    load_sample_combined = st.sidebar.button(
        "Load sample_cameras_combined.csv",
        help="Loads the project-root combined-coordinate sample file directly into WRAITH.",
    )

    st.sidebar.markdown("---")

    # ── Layer controls — one row per loaded file ──────────────────────────────
    active_names = []
    if files_dict:
        st.sidebar.markdown('<div class="section-label">Layers</div>', unsafe_allow_html=True)

        to_remove = []
        for name, fdata in files_dict.items():
            c1, c2 = st.sidebar.columns([6, 1])
            with c1:
                visible = st.checkbox(
                    f"{name.replace('.csv','')}",
                    value=True,
                    key=f"layer_{name}",
                )
            with c2:
                if st.button("✕", key=f"rm_{name}", help=f"Remove {name}"):
                    to_remove.append(name)

            # Color swatch + camera count + conflict warning
            conflict_note = f"  ⚡ {len(fdata['errors'])} conflicts" if fdata["errors"] else ""
            st.sidebar.markdown(
                f'<div style="margin:-12px 0 6px 22px;font-size:0.65rem;color:#475569">'
                f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
                f'background:{fdata["color"]};margin-right:4px;vertical-align:middle"></span>'
                f'{len(fdata["df"])} cameras{conflict_note}</div>',
                unsafe_allow_html=True,
            )

            if visible:
                active_names.append(name)

        # Process removals after iterating
        for name in to_remove:
            if name in st.session_state.files:
                del st.session_state.files[name]
        if to_remove:
            st.rerun()

    st.sidebar.markdown("---")

    # ── Panel selector ────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="section-label">View</div>', unsafe_allow_html=True)
    view = st.sidebar.radio(
        "Panel",
        options=["Globe", "Flat Map", "Heatmap", "Data Table", "Conflicts", "Alerts & Export"],
        label_visibility="collapsed",
    )

    # Map options
    auto_rotate = False
    heat_tile_style = "Dark (CartoDB)"
    heat_use_cluster = True
    heat_marker_radius = 6
    heat_radius = 20
    heat_show_minimap = True

    if view == "Globe":
        st.sidebar.markdown(
            '<div class="section-label" style="margin-top:0.4rem">Map Options</div>',
            unsafe_allow_html=True,
        )
        auto_rotate = st.sidebar.toggle("Auto-rotate", value=False)
    elif view == "Heatmap":
        st.sidebar.markdown(
            '<div class="section-label" style="margin-top:0.4rem">Map Options</div>',
            unsafe_allow_html=True,
        )
        heat_tile_style = st.sidebar.selectbox(
            "Basemap",
            options=list(HEATMAP_TILES.keys()),
            index=0,
            help="Switch to a more detailed base map (street, terrain, satellite, etc.).",
        )
        heat_use_cluster = st.sidebar.toggle(
            "Cluster markers",
            value=True,
            help="Group nearby cameras at low zoom for denser regions.",
        )
        heat_show_minimap = st.sidebar.toggle(
            "Show minimap",
            value=True,
            help="Display a small overview map for quicker navigation.",
        )
        heat_marker_radius = st.sidebar.slider(
            "Marker size",
            min_value=4,
            max_value=10,
            value=6,
        )
        heat_radius = st.sidebar.slider(
            "Heat radius",
            min_value=10,
            max_value=35,
            value=20,
        )

    st.sidebar.markdown("---")

    # ── Filters ───────────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="section-label">Filters</div>', unsafe_allow_html=True)

    status_filter = st.sidebar.multiselect(
        "Staleness",
        options=["FRESH", "STALE", "EXPIRED"],
        default=["FRESH", "STALE", "EXPIRED"],
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

    # ── Email alerts ──────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="section-label">Email Alerts</div>', unsafe_allow_html=True)
    email_enabled = st.sidebar.toggle(
        "Enable email alerts", value=False,
        help="Set ALERT_EMAIL_FROM / _PASSWORD / _TO in .env",
    )
    if email_enabled:
        if st.sidebar.button("Send test email"):
            ok, msg = send_email_alert("WRAITH — Test Alert", "Test alert from WRAITH.")
            st.sidebar.success("Sent.") if ok else st.sidebar.error(msg)

    return (
        uploaded_files, view, auto_rotate,
        status_filter, country_filter, email_enabled, active_names,
        load_sample_decimal, load_sample_combined,
        heat_tile_style, heat_use_cluster, heat_marker_radius, heat_radius, heat_show_minimap,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    init_session()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="cw-header">'
        '<h1>◈ WRAITH</h1>'
        '<span class="cw-sub">Wide-area Reconnaissance & Asset Intelligence Tracking Hub</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    files_dict = st.session_state.files

    # ── Sidebar ───────────────────────────────────────────────────────────────
    (uploaded_files, view, auto_rotate,
     status_filter, country_filter, email_enabled, active_names,
     load_sample_decimal, load_sample_combined,
     heat_tile_style, heat_use_cluster, heat_marker_radius, heat_radius, heat_show_minimap) = render_sidebar(files_dict)

    # Build a unified list of incoming files from uploader + local sample buttons.
    incoming_files = list(uploaded_files) if uploaded_files else []

    if load_sample_decimal:
        p = Path("sample_cameras_decimal.csv")
        if p.exists():
            incoming_files.append(str(p))
        else:
            st.error("Local sample not found: sample_cameras_decimal.csv")

    if load_sample_combined:
        p = Path("sample_cameras_combined.csv")
        if p.exists():
            incoming_files.append(str(p))
        else:
            st.error("Local sample not found: sample_cameras_combined.csv")

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
        with st.expander("Supported coordinate formats"):
            st.markdown("""
| Format | Accepted column names | Example |
|---|---|---|
| Decimal degrees | `lat`, `lon`, `latitude`, `longitude` | `38.8951` / `-77.0364` |
| MGRS | `mgrs`, `grid`, `grid_ref` | `18SUJ2338308450` |
| DMS | `dms_lat`, `dms_lon` | `38°53'42"N` |
| UTM | `utm`, `utm_coord` | `18N 323830 4308450` |
| Combined | `coordinates`, `lat/lon` | `38.8951, -77.0364` |
""")
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
    total, fresh, stale, expired = render_kpis(filtered_dict, active_names, status_filter)

    # ── Top-level alert banners ───────────────────────────────────────────────
    if expired > 0:
        # Collect expired locations across all active files
        exp_locs = []
        for fd in filtered_dict.values():
            df = fd["df"][fd["df"]["color_class"] == "red"]
            exp_locs.extend(df["location_label"].unique().tolist())
        loc_str = ", ".join(str(l) for l in exp_locs[:5])
        if len(exp_locs) > 5:
            loc_str += f" +{len(exp_locs)-5} more"
        st.markdown(
            f'<div class="alert-banner alert-red">'
            f'🔴 <b>IMMEDIATE ACTION:</b> {expired} camera(s) expired (&gt;6mo) across '
            f'{len([n for n in active_names if (filtered_dict.get(n,{}).get("df") is not None and (filtered_dict[n]["df"]["color_class"]=="red").any())])} '
            f'region(s). Locations: {loc_str}</div>',
            unsafe_allow_html=True,
        )

    if stale > 0:
        stl_locs = []
        for fd in filtered_dict.values():
            df = fd["df"][fd["df"]["color_class"] == "yellow"]
            stl_locs.extend(df["location_label"].unique().tolist())
        loc_str = ", ".join(str(l) for l in stl_locs[:5])
        if len(stl_locs) > 5:
            loc_str += f" +{len(stl_locs)-5} more"
        st.markdown(
            f'<div class="alert-banner alert-yellow">'
            f'🟡 <b>REVIEW SOON:</b> {stale} camera(s) approaching 6-month threshold. '
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
            show_cols = [
                "source_file", "ip", "location_label", "device_type",
                "model", "last_seen", "age_months", "staleness_status",
                "country", "port", "org",
            ]
            available = [c for c in show_cols if c in df_table.columns]

            def style_status(val):
                return {
                    "FRESH":   "color:#22c55e;font-weight:600",
                    "STALE":   "color:#eab308;font-weight:600",
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

        bluf_text = generate_bluf(filtered_dict, active_names, status_filter)
        st.text_area("BLUF Summary", value=bluf_text, height=400)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                "⬇ BLUF Report (.txt)",
                data=bluf_text,
                file_name=f"wraith_bluf_{datetime.date.today().isoformat()}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with col2:
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

        with col3:
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


if __name__ == "__main__":
    main()
