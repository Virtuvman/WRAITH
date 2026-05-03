"""
WRAITH × WiGLE — Integration Proof of Concept
==============================================
Standalone Streamlit app demonstrating what WiGLE wireless network data
would look like layered into WRAITH's existing globe/map/analytics stack.

Run:
    streamlit run poc_wigle_integration.py

No API key required — ships with realistic mock data.
To test against the real WiGLE API: enter credentials in the sidebar.

WiGLE API docs: https://api.wigle.net/swagger
Free registration: https://wigle.net/account
Auth: HTTP Basic with your WiGLE username + API token (NOT your password).
"""

from __future__ import annotations

import datetime
import random
import math
import base64
import logging
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import folium
    from folium.plugins import HeatMap, MarkerCluster
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

CAMERA_COLOR   = "#38bdf8"   # sky blue  — matches WRAITH layer 0
WIFI_COLOR     = "#a78bfa"   # violet
CELL_COLOR     = "#34d399"   # emerald
BT_COLOR       = "#fb923c"   # orange

ENCRYPTION_COLORS = {
    "open":   "#ef4444",   # red — high concern
    "wep":    "#f97316",   # orange — deprecated/vulnerable
    "wpa":    "#eab308",   # yellow — aging
    "wpa2":   "#22c55e",   # green — standard
    "wpa3":   "#38bdf8",   # sky — modern
    "unknown":"#64748b",   # slate
}

WIGLE_SEARCH_URL = "https://api.wigle.net/api/v2/network/search"

SEARCH_RADIUS_DEG = 0.01  # ~1.1 km at equator; used for mock scatter


# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────────────────────────────────────

_SSID_POOL = [
    "xfinitywifi", "ATT-WiFi", "Starbucks", "Google Starbucks",
    "NETGEAR_5G", "TP-Link_2G", "DIRECT-xx-HP LaserJet",
    "CoxWifi", "Spectrum2G-XXXX", "linksys", "dlink",
    "FiOS-XXXX", "HOME-XXXX-5G", "AndroidAP", "iPhone",
    "ARRIS-XXXX", "XFINITY", "OPTUS_XXXX", "Telstra_XXXX",
    "BTHub-XXXX", "SKY_XXXX", "VIRGIN-XXXX",
]

_ENCRYPTION_DIST = ["wpa2"] * 55 + ["wpa3"] * 15 + ["wpa"] * 12 + \
                   ["open"] * 10 + ["wep"] * 5 + ["unknown"] * 3

_NET_TYPES = ["wifi"] * 70 + ["cell"] * 20 + ["bluetooth"] * 10


def _rand_bssid(rng: random.Random) -> str:
    return ":".join(f"{rng.randint(0, 255):02X}" for _ in range(6))


def _rand_date(rng: random.Random, start_year: int = 2018, end_year: int = 2025) -> str:
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    delta = (end - start).days
    return str(start + datetime.timedelta(days=rng.randint(0, delta)))


def generate_mock_cameras(n: int = 40, seed: int = 42) -> pd.DataFrame:
    """Return a small camera dataset matching WRAITH's schema."""
    rng = random.Random(seed)
    cities = [
        (40.71, -74.01, "New York", "US"),
        (51.51, -0.13,  "London",   "GB"),
        (35.69, 139.69, "Tokyo",    "JP"),
        (48.86,  2.35,  "Paris",    "FR"),
        (-33.87, 151.21,"Sydney",   "AU"),
        (19.43, -99.13, "Mexico City","MX"),
        (55.75,  37.62, "Moscow",   "RU"),
        (1.35,  103.82, "Singapore","SG"),
        (52.52,  13.41, "Berlin",   "DE"),
        (28.61,  77.21, "New Delhi","IN"),
    ]
    device_models = [
        ("PTZ Camera",  "Sony SNC-EP580"),
        ("IP Camera",   "Hanwha XNV-8080R"),
        ("Fixed Camera","Axis P3245-V"),
        ("Dome Camera", "Bosch FLEXIDOME"),
        ("PTZ Camera",  "Hikvision DS-2DE4A425IWG"),
    ]
    rows = []
    for i in range(n):
        lat0, lon0, city, country = rng.choice(cities)
        lat = lat0 + rng.uniform(-0.08, 0.08)
        lon = lon0 + rng.uniform(-0.08, 0.08)
        dtype, model = rng.choice(device_models)
        last_seen = _rand_date(rng, 2024, 2026)
        rows.append({
            "ip": f"10.{rng.randint(0,255)}.{rng.randint(0,255)}.{rng.randint(1,254)}",
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "device_type": dtype,
            "model": model,
            "location_label": f"{city} Cam {i+1:03d}",
            "last_seen": last_seen,
            "port": rng.choice([80, 443, 8080, 554]),
            "org": rng.choice(["Verizon", "Comcast", "BT", "Orange", "Telstra"]),
            "country": country,
            "region": city,
            "poc_batch": "WIGLE_POC",
        })
    return pd.DataFrame(rows)


def generate_mock_wigle_networks(cameras_df: pd.DataFrame, networks_per_camera: int = 8, seed: int = 99) -> pd.DataFrame:
    """Scatter realistic WiFi/cell/BT observations near each camera."""
    rng = random.Random(seed)
    rows = []
    for _, cam in cameras_df.iterrows():
        n_net = rng.randint(max(1, networks_per_camera - 4), networks_per_camera + 6)
        for _ in range(n_net):
            net_type = rng.choice(_NET_TYPES)
            enc = rng.choice(_ENCRYPTION_DIST) if net_type == "wifi" else "n/a"
            first = _rand_date(rng, 2018, 2022)
            last  = _rand_date(rng, 2023, 2026)
            rows.append({
                "trilat":     round(cam["latitude"]  + rng.uniform(-SEARCH_RADIUS_DEG, SEARCH_RADIUS_DEG), 6),
                "trilong":    round(cam["longitude"] + rng.uniform(-SEARCH_RADIUS_DEG, SEARCH_RADIUS_DEG), 6),
                "ssid":       rng.choice(_SSID_POOL) if net_type == "wifi" else "",
                "netid":      _rand_bssid(rng),
                "encryption": enc,
                "firsttime":  first,
                "lasttime":   last,
                "channel":    rng.choice([1, 6, 11, 36, 40, 44, 48, 0]) if net_type == "wifi" else 0,
                "type":       net_type,
                "bestrssi":   rng.randint(-90, -40),
                "country":    cam["country"],
                "near_camera": cam["location_label"],
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# WIGLE API CLIENT
# ─────────────────────────────────────────────────────────────────────────────

def wigle_bbox_search(
    lat: float, lon: float, radius_deg: float,
    username: str, token: str,
    result_limit: int = 100,
) -> list[dict]:
    """
    Call WiGLE /network/search for a bounding box around (lat, lon).
    Returns the raw results list or raises on error.
    """
    if not REQUESTS_AVAILABLE:
        raise RuntimeError("requests library not installed.")

    cred = base64.b64encode(f"{username}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {cred}",
        "Accept": "application/json",
    }
    params = {
        "latrange1": lat - radius_deg,
        "latrange2": lat + radius_deg,
        "longrange1": lon - radius_deg,
        "longrange2": lon + radius_deg,
        "resultsPerPage": min(result_limit, 100),
    }
    resp = requests.get(WIGLE_SEARCH_URL, headers=headers, params=params, timeout=10)

    if resp.status_code == 401:
        raise RuntimeError(
            "Authentication failed (401). Check your WiGLE username and API token. "
            "Use your API token from wigle.net/account — NOT your login password."
        )
    if resp.status_code == 412:
        raise RuntimeError(
            "WiGLE API terms not accepted (412). "
            "Go to wigle.net/account, find the API section, and check the box agreeing to non-commercial usage terms. "
            "This is a one-time step — retry after accepting."
        )
    if resp.status_code == 429:
        raise RuntimeError(
            "WiGLE rate limit hit (429). Free tier has a limited request quota. "
            "Reduce the number of cameras queried or wait before retrying."
        )

    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


def fetch_wigle_for_cameras(
    cameras_df: pd.DataFrame,
    username: str, token: str,
    radius_deg: float = 0.01,
    limit_cameras: int = 10,
) -> pd.DataFrame:
    """
    Fetch WiGLE data for the first N camera locations and combine into a DataFrame.
    Adds near_camera label to each result.
    """
    all_rows = []
    sample = cameras_df.head(limit_cameras)
    progress = st.progress(0, text="Querying WiGLE API...")
    for i, (_, cam) in enumerate(sample.iterrows()):
        try:
            results = wigle_bbox_search(
                cam["latitude"], cam["longitude"], radius_deg, username, token
            )
            for r in results:
                r["near_camera"] = cam["location_label"]
                r["trilat"]  = r.get("trilat", cam["latitude"])
                r["trilong"] = r.get("trilong", cam["longitude"])
            all_rows.extend(results)
        except Exception as exc:
            st.warning(f"WiGLE query failed for {cam['location_label']}: {exc}")
        progress.progress((i + 1) / len(sample), text=f"Queried {i+1}/{len(sample)} cameras…")
    progress.empty()
    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    col_map = {
        "ssid": "ssid", "netid": "netid", "encryption": "encryption",
        "firsttime": "firsttime", "lasttime": "lasttime",
        "channel": "channel", "type": "type", "bestrssi": "bestrssi",
        "country": "country",
    }
    for dest, src in col_map.items():
        if dest not in df.columns and src in df.columns:
            df[dest] = df[src]
        elif dest not in df.columns:
            df[dest] = ""
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PROXIMITY HELPER
# ─────────────────────────────────────────────────────────────────────────────

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_proximity_table(cameras_df: pd.DataFrame, networks_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each camera, count how many networks are within 1 km and flag
    open/WEP networks (high-risk).
    """
    rows = []
    for _, cam in cameras_df.iterrows():
        nearby = networks_df[networks_df["near_camera"] == cam["location_label"]]
        total = len(nearby)
        open_nets = len(nearby[nearby["encryption"].isin(["open", "wep"])])
        wifi_count = len(nearby[nearby["type"] == "wifi"])
        cell_count = len(nearby[nearby["type"] == "cell"])
        rows.append({
            "Camera":         cam["location_label"],
            "Country":        cam["country"],
            "Last Seen":      cam["last_seen"],
            "WiFi Nearby":    wifi_count,
            "Cell Nearby":    cell_count,
            "Open/WEP Nets":  open_nets,
            "Total Signals":  total,
            "Risk Flag":      "HIGH" if open_nets >= 3 else ("MED" if open_nets >= 1 else "LOW"),
        })
    return pd.DataFrame(rows).sort_values("Open/WEP Nets", ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATIONS
# ─────────────────────────────────────────────────────────────────────────────

def render_dual_globe(cameras_df: pd.DataFrame, networks_df: pd.DataFrame, show_wifi: bool, show_cell: bool, show_bt: bool):
    """Globe showing camera locations + WiGLE network observations as a second layer."""
    fig = go.Figure()

    # Camera layer
    fig.add_trace(go.Scattergeo(
        lat=cameras_df["latitude"],
        lon=cameras_df["longitude"],
        mode="markers",
        marker=dict(size=6, color=CAMERA_COLOR, opacity=0.85, symbol="circle"),
        name="Cameras",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Model: %{customdata[1]}<br>"
            "Last Seen: %{customdata[2]}<br>"
            "Country: %{customdata[3]}<extra></extra>"
        ),
        customdata=cameras_df[["location_label", "model", "last_seen", "country"]].values,
    ))

    # WiFi layer
    if show_wifi:
        wifi = networks_df[networks_df["type"] == "wifi"]
        if not wifi.empty:
            fig.add_trace(go.Scattergeo(
                lat=wifi["trilat"],
                lon=wifi["trilong"],
                mode="markers",
                marker=dict(
                    size=4,
                    color=[ENCRYPTION_COLORS.get(str(e).lower(), ENCRYPTION_COLORS["unknown"]) for e in wifi["encryption"]],
                    opacity=0.6,
                    symbol="circle-open",
                ),
                name="WiFi Networks",
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "BSSID: %{customdata[1]}<br>"
                    "Enc: %{customdata[2]}<br>"
                    "RSSI: %{customdata[3]} dBm<br>"
                    "Near: %{customdata[4]}<extra></extra>"
                ),
                customdata=wifi[["ssid", "netid", "encryption", "bestrssi", "near_camera"]].values,
            ))

    # Cell layer
    if show_cell:
        cell = networks_df[networks_df["type"] == "cell"]
        if not cell.empty:
            fig.add_trace(go.Scattergeo(
                lat=cell["trilat"],
                lon=cell["trilong"],
                mode="markers",
                marker=dict(size=4, color=CELL_COLOR, opacity=0.55, symbol="triangle-up-open"),
                name="Cell Towers",
                hovertemplate="BSSID: %{customdata[0]}<br>Near: %{customdata[1]}<extra></extra>",
                customdata=cell[["netid", "near_camera"]].values,
            ))

    # Bluetooth layer
    if show_bt:
        bt = networks_df[networks_df["type"] == "bluetooth"]
        if not bt.empty:
            fig.add_trace(go.Scattergeo(
                lat=bt["trilat"],
                lon=bt["trilong"],
                mode="markers",
                marker=dict(size=3, color=BT_COLOR, opacity=0.5, symbol="square-open"),
                name="Bluetooth",
                hovertemplate="Near: %{customdata[0]}<extra></extra>",
                customdata=bt[["near_camera"]].values,
            ))

    fig.update_geos(
        projection_type="orthographic",
        showland=True, landcolor="#1a2035",
        showocean=True, oceancolor="#0d1526",
        showcoastlines=True, coastlinecolor="#334155",
        showcountries=True, countrycolor="#1e3a52",
        showframe=False,
        bgcolor="#0d1117",
    )
    fig.update_layout(
        height=580,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0d1117",
        legend=dict(
            bgcolor="rgba(13,17,23,0.85)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(color="#94a3b8", size=11),
        ),
        geo=dict(bgcolor="#0d1117"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_encryption_breakdown(networks_df: pd.DataFrame):
    """Bar chart of encryption type distribution — open/WEP flagged in red."""
    wifi = networks_df[networks_df["type"] == "wifi"].copy()
    if wifi.empty:
        st.info("No WiFi records to analyze.")
        return

    counts = wifi["encryption"].str.lower().value_counts().reset_index()
    counts.columns = ["encryption", "count"]
    counts["color"] = counts["encryption"].map(lambda e: ENCRYPTION_COLORS.get(e, ENCRYPTION_COLORS["unknown"]))

    fig = go.Figure(go.Bar(
        x=counts["encryption"].str.upper(),
        y=counts["count"],
        marker_color=counts["color"],
        text=counts["count"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="WiFi Encryption Distribution", font=dict(color="#94a3b8", size=13)),
        xaxis=dict(title="Encryption Type", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        yaxis=dict(title="Networks", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#94a3b8"),
        height=340,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    open_count = len(wifi[wifi["encryption"].isin(["open", "wep"])])
    pct = round(100 * open_count / len(wifi), 1)
    if open_count > 0:
        st.markdown(
            f'<div style="background:rgba(239,68,68,0.08);border-left:3px solid #ef4444;'
            f'padding:0.5rem 1rem;border-radius:6px;font-size:0.82rem;color:#fca5a5;">'
            f'<b>{open_count} open/WEP networks</b> ({pct}%) detected near camera locations — '
            f'potential eavesdropping or pivot surface.</div>',
            unsafe_allow_html=True
        )


def render_temporal_correlation(cameras_df: pd.DataFrame, networks_df: pd.DataFrame):
    """
    Scatter: camera age (days since last_seen) vs median network age (days since lasttime).
    Shows whether old cameras correlate with stale surrounding infrastructure.
    """
    today = datetime.date.today()

    cam_ages = {}
    for _, cam in cameras_df.iterrows():
        try:
            d = datetime.date.fromisoformat(str(cam["last_seen"])[:10])
            cam_ages[cam["location_label"]] = (today - d).days
        except Exception:
            cam_ages[cam["location_label"]] = None

    net_ages = {}
    for label, grp in networks_df.groupby("near_camera"):
        ages = []
        for val in grp["lasttime"]:
            try:
                d = datetime.date.fromisoformat(str(val)[:10])
                ages.append((today - d).days)
            except Exception:
                pass
        net_ages[label] = round(sum(ages) / len(ages)) if ages else None

    plot_rows = []
    for label, cam_age in cam_ages.items():
        net_age = net_ages.get(label)
        if cam_age is not None and net_age is not None:
            plot_rows.append({
                "camera": label,
                "camera_age_days": cam_age,
                "network_age_days": net_age,
            })

    if not plot_rows:
        st.info("Insufficient temporal data.")
        return

    df_plot = pd.DataFrame(plot_rows)
    fig = go.Figure(go.Scatter(
        x=df_plot["camera_age_days"],
        y=df_plot["network_age_days"],
        mode="markers",
        marker=dict(
            size=9,
            color=df_plot["camera_age_days"],
            colorscale=[[0, "#22c55e"], [0.33, "#eab308"], [0.66, "#f97316"], [1.0, "#ef4444"]],
            showscale=True,
            colorbar=dict(title="Cam Age (d)", tickfont=dict(color="#94a3b8")),
            opacity=0.8,
        ),
        text=df_plot["camera"],
        hovertemplate="<b>%{text}</b><br>Camera age: %{x}d<br>Avg network age: %{y}d<extra></extra>",
    ))
    # Diagonal reference line: if cam_age ≈ net_age they're aging together
    max_val = max(df_plot[["camera_age_days", "network_age_days"]].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines",
        line=dict(color="#334155", dash="dot", width=1),
        name="1:1 reference",
        hoverinfo="skip",
    ))
    fig.update_layout(
        title=dict(text="Camera Age vs Surrounding Network Age", font=dict(color="#94a3b8", size=13)),
        xaxis=dict(title="Camera — Days Since Last Seen", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        yaxis=dict(title="WiFi Networks — Avg Days Since Last Seen", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#94a3b8"),
        height=380,
        margin=dict(l=40, r=20, t=40, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Points near the diagonal line: camera staleness tracks surrounding infrastructure age — "
        "consistent with a location that hasn't been actively maintained. "
        "Points above the line: camera recently checked in but infrastructure is older (possible re-deployment). "
        "Points below: camera stale but networks actively seen — location still occupied."
    )


def render_signal_heatmap(networks_df: pd.DataFrame):
    """Folium heatmap of WiFi signal observations."""
    if not FOLIUM_AVAILABLE:
        st.warning("streamlit-folium not installed. Run: pip install folium streamlit-folium")
        return

    wifi = networks_df[networks_df["type"] == "wifi"].dropna(subset=["trilat", "trilong"])
    if wifi.empty:
        st.info("No WiFi observations to map.")
        return

    center_lat = wifi["trilat"].mean()
    center_lon = wifi["trilong"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="CartoDB dark_matter",
    )
    heat_data = [[row["trilat"], row["trilong"], max(0, (row["bestrssi"] + 100) / 60)]
                 for _, row in wifi.iterrows() if pd.notna(row.get("bestrssi"))]
    if heat_data:
        HeatMap(heat_data, radius=12, blur=10, min_opacity=0.3).add_to(m)

    st_folium(m, height=380, use_container_width=True)


def render_network_type_pie(networks_df: pd.DataFrame):
    """Donut chart of network types."""
    counts = networks_df["type"].value_counts().reset_index()
    counts.columns = ["type", "count"]
    color_map = {"wifi": WIFI_COLOR, "cell": CELL_COLOR, "bluetooth": BT_COLOR}

    fig = go.Figure(go.Pie(
        labels=counts["type"].str.capitalize(),
        values=counts["count"],
        hole=0.55,
        marker_colors=[color_map.get(t, "#64748b") for t in counts["type"]],
        textfont=dict(color="#e2e8f0"),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        paper_bgcolor="#0d1117",
        font=dict(color="#94a3b8"),
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(font=dict(color="#94a3b8")),
        title=dict(text="Signal Types Detected", font=dict(color="#94a3b8", size=13)),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_ssid_frequency(networks_df: pd.DataFrame, top_n: int = 15):
    """Horizontal bar of most-common SSIDs."""
    wifi = networks_df[(networks_df["type"] == "wifi") & (networks_df["ssid"].str.strip() != "")]
    if wifi.empty:
        return
    top = wifi["ssid"].value_counts().head(top_n).reset_index()
    top.columns = ["ssid", "count"]
    top = top.sort_values("count")

    fig = go.Figure(go.Bar(
        y=top["ssid"],
        x=top["count"],
        orientation="h",
        marker_color=WIFI_COLOR,
        text=top["count"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x} observations<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"Top {top_n} SSIDs Near Camera Locations", font=dict(color="#94a3b8", size=13)),
        xaxis=dict(title="Observations", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        yaxis=dict(tickfont=dict(color="#94a3b8", size=10)),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#94a3b8"),
        height=max(280, top_n * 22),
        margin=dict(l=130, r=40, t=40, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_channel_distribution(networks_df: pd.DataFrame):
    """Bar chart of WiFi channel usage."""
    wifi = networks_df[(networks_df["type"] == "wifi") & (networks_df["channel"] != 0)]
    if wifi.empty:
        return
    counts = wifi["channel"].value_counts().sort_index().reset_index()
    counts.columns = ["channel", "count"]

    congested = {1, 6, 11}
    colors = ["#ef4444" if c in congested else WIFI_COLOR for c in counts["channel"]]

    fig = go.Figure(go.Bar(
        x=counts["channel"].astype(str),
        y=counts["count"],
        marker_color=colors,
        hovertemplate="Ch %{x}: %{y} networks<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="WiFi Channel Usage (red = congested 2.4 GHz)", font=dict(color="#94a3b8", size=13)),
        xaxis=dict(title="Channel", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        yaxis=dict(title="Count", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#94a3b8"),
        height=300,
        margin=dict(l=40, r=20, t=40, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_coverage_gap(cameras_df: pd.DataFrame, networks_df: pd.DataFrame):
    """Flag cameras with zero nearby WiFi — could be rural, air-gapped, or data gap."""
    net_counts = networks_df[networks_df["type"] == "wifi"].groupby("near_camera").size().to_dict()
    rows = []
    for _, cam in cameras_df.iterrows():
        n = net_counts.get(cam["location_label"], 0)
        rows.append({
            "Camera": cam["location_label"],
            "Country": cam["country"],
            "WiFi Nearby": n,
            "Interpretation": "No WiFi detected — rural / isolated / data gap" if n == 0
                              else ("Sparse coverage" if n < 3 else "Normal urban density"),
        })
    df = pd.DataFrame(rows)
    gaps = df[df["WiFi Nearby"] == 0]
    if not gaps.empty:
        st.markdown(
            f'<div style="background:rgba(99,102,241,0.08);border-left:3px solid #6366f1;'
            f'padding:0.5rem 1rem;border-radius:6px;font-size:0.82rem;color:#a5b4fc;margin-bottom:0.75rem;">'
            f'<b>{len(gaps)} cameras</b> returned zero WiFi observations — '
            f'may indicate rural deployment, Faraday-shielded environment, or WiGLE coverage gap.</div>',
            unsafe_allow_html=True
        )
    st.dataframe(
        df.style.applymap(
            lambda v: "color: #ef4444" if v == 0 else ("color: #eab308" if v < 3 else ""),
            subset=["WiFi Nearby"]
        ),
        use_container_width=True, hide_index=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────────────────────────────────────────

def render_pros_cons():
    st.markdown("""
<style>
.pc-grid { display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:0.5rem; }
.pc-card { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
           border-radius:10px; padding:1rem 1.2rem; }
.pc-card.pro  { border-left:3px solid #22c55e; }
.pc-card.con  { border-left:3px solid #f97316; }
.pc-card h4 { font-size:0.75rem; letter-spacing:0.1em; text-transform:uppercase;
              margin:0 0 0.6rem 0; }
.pc-card.pro h4 { color:#22c55e; }
.pc-card.con h4 { color:#f97316; }
.pc-card ul { margin:0; padding-left:1.1rem; font-size:0.82rem; color:#94a3b8; line-height:1.75; }
@media (max-width:700px) { .pc-grid { grid-template-columns:1fr; } }
</style>
<div class="pc-grid">
  <div class="pc-card pro">
    <h4>Pros</h4>
    <ul>
      <li><b>Free data, no scraping</b> — WiGLE API is free with registration; crowdsourced observations, billions of records</li>
      <li><b>Geospatial-native</b> — trilat/trilong drops directly into existing coordinate pipeline with zero transformation work</li>
      <li><b>Physical infrastructure context</b> — WiFi/cell observations corroborate or contradict claimed camera locations</li>
      <li><b>Staleness cross-reference</b> — network "lasttime" vs camera "last_seen" enables independent staleness validation</li>
      <li><b>Encryption intelligence</b> — open/WEP networks near a camera are an OPSEC/pivot surface worth flagging</li>
      <li><b>Coverage gap detection</b> — zero WiGLE observations can flag rural, air-gapped, or falsified locations</li>
      <li><b>Multi-type signals</b> — WiFi, cell tower, Bluetooth in one API — richer environment fingerprint</li>
      <li><b>Minimal integration cost</b> — new ingestion module + layer toggle, no schema changes to core WRAITH data model</li>
    </ul>
  </div>
  <div class="pc-card con">
    <h4>Cons / Risks</h4>
    <ul>
      <li><b>Crowdsourced accuracy</b> — WiGLE relies on user submissions; rural/restricted areas have sparse or absent coverage</li>
      <li><b>API rate limits</b> — free tier is throttled; querying 500 cameras per session will hit limits quickly</li>
      <li><b>Location jitter</b> — trilateration estimates can be 50–200m off in dense urban environments</li>
      <li><b>Static snapshot</b> — WiGLE records when a network was <i>observed</i>, not if it's currently active</li>
      <li><b>SSID/BSSID spoofing</b> — common SSIDs like "xfinitywifi" appear globally and offer little locational value</li>
      <li><b>Privacy/legal grey area</b> — WiFi scanning is legal in most jurisdictions but should stay passive-only</li>
      <li><b>Registration required</b> — API key not instant; adds onboarding friction vs fully open sources</li>
      <li><b>No real-time feed</b> — WiGLE is historical; unsuitable for live situational awareness</li>
    </ul>
  </div>
</div>
""", unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="WRAITH × WiGLE PoC",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif; }
.section-label {
    font-family:'Share Tech Mono',monospace; font-size:0.68rem;
    letter-spacing:0.15em; text-transform:uppercase; color:#475569;
    margin-bottom:0.5rem; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:4px;
}
.kpi-row { display:flex; gap:10px; margin-bottom:1rem; flex-wrap:wrap; }
.kpi-card {
    flex:1; min-width:88px; background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.07); border-radius:10px;
    padding:0.8rem 0.9rem; text-align:center;
}
.kpi-card .kpi-num { font-family:'Share Tech Mono',monospace; font-size:1.8rem; line-height:1.1; }
.kpi-card .kpi-lbl { font-size:0.62rem; letter-spacing:0.1em; text-transform:uppercase; color:#64748b; margin-top:3px; }
.kpi-card.blue   .kpi-num { color:#38bdf8; }
.kpi-card.violet .kpi-num { color:#a78bfa; }
.kpi-card.green  .kpi-num { color:#34d399; }
.kpi-card.red    .kpi-num { color:#ef4444; }
.kpi-card.orange .kpi-num { color:#fb923c; }
</style>
""", unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="padding:0.4rem 0 1.2rem; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:1.2rem;">
  <span style="font-family:'Share Tech Mono',monospace; font-size:1.4rem; color:#e2e8f0; letter-spacing:0.12em;">
    WRAITH × WiGLE
  </span>
  <span style="font-size:0.72rem; color:#64748b; letter-spacing:0.08em; text-transform:uppercase; margin-left:14px;">
    Integration Proof of Concept
  </span>
</div>
""", unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="section-label">Data Source</div>', unsafe_allow_html=True)
        use_mock = st.radio("Source", ["Mock data (offline)", "WiGLE API (live)"], index=0) == "Mock data (offline)"

        wigle_user, wigle_token = "", ""
        search_radius = 0.01
        camera_limit = 10
        if not use_mock:
            st.markdown('<div class="section-label">WiGLE Credentials</div>', unsafe_allow_html=True)
            st.caption("Username + API token from wigle.net/account — NOT your password.")
            wigle_user  = st.text_input("WiGLE Username")
            wigle_token = st.text_input("API Token", type="password")
            search_radius = st.slider("Search radius (°)", 0.005, 0.05, 0.01, 0.005,
                                      help="~0.01° ≈ 1.1 km")
            camera_limit = st.slider("Max cameras to query", 1, 50, 10,
                                     help="Free tier rate limits apply")
            if not REQUESTS_AVAILABLE:
                st.error("requests not installed: pip install requests")

        st.divider()
        st.markdown('<div class="section-label">Globe Layers</div>', unsafe_allow_html=True)
        show_wifi = st.checkbox("WiFi Networks", value=True)
        show_cell = st.checkbox("Cell Towers",   value=True)
        show_bt   = st.checkbox("Bluetooth",     value=False)

        st.divider()
        st.markdown('<div class="section-label">Mock Data</div>', unsafe_allow_html=True)
        n_cameras = st.slider("Cameras", 10, 80, 40) if use_mock else 40
        nets_per_cam = st.slider("Networks per camera", 4, 20, 8) if use_mock else 8

    # ── Load Data ─────────────────────────────────────────────────────────────
    cameras_df = generate_mock_cameras(n=n_cameras)

    if use_mock:
        networks_df = generate_mock_wigle_networks(cameras_df, networks_per_camera=nets_per_cam)
        st.info("Running on **mock data**. Flip to *WiGLE API* in the sidebar to query live data.")
    else:
        if not wigle_user or not wigle_token:
            st.warning("Enter WiGLE username and API token in the sidebar to fetch live data.")
            st.stop()
        with st.spinner("Fetching WiGLE data…"):
            networks_df = fetch_wigle_for_cameras(cameras_df, wigle_user, wigle_token,
                                                   radius_deg=search_radius, limit_cameras=camera_limit)
        if networks_df.empty:
            st.error("No WiGLE results returned. Check credentials and try a larger radius.")
            st.stop()

    proximity_df = compute_proximity_table(cameras_df, networks_df)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    wifi_df   = networks_df[networks_df["type"] == "wifi"]
    open_nets = len(wifi_df[wifi_df["encryption"].isin(["open", "wep"])])
    high_risk = len(proximity_df[proximity_df["Risk Flag"] == "HIGH"])

    st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card blue">
    <div class="kpi-num">{len(cameras_df)}</div>
    <div class="kpi-lbl">Cameras</div>
  </div>
  <div class="kpi-card violet">
    <div class="kpi-num">{len(wifi_df)}</div>
    <div class="kpi-lbl">WiFi Obs.</div>
  </div>
  <div class="kpi-card green">
    <div class="kpi-num">{len(networks_df[networks_df['type']=='cell'])}</div>
    <div class="kpi-lbl">Cell Obs.</div>
  </div>
  <div class="kpi-card red">
    <div class="kpi-num">{open_nets}</div>
    <div class="kpi-lbl">Open/WEP</div>
  </div>
  <div class="kpi-card orange">
    <div class="kpi-num">{high_risk}</div>
    <div class="kpi-lbl">High-Risk Sites</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "Globe",
        "Encryption & Signals",
        "Temporal Correlation",
        "Coverage Gaps",
        "Proximity Table",
        "Pros & Cons",
    ])

    with tabs[0]:
        st.markdown('<div class="section-label">Dual-Layer Globe — Cameras + WiGLE Observations</div>', unsafe_allow_html=True)
        st.caption("Camera dots (sky blue). WiFi rings colored by encryption: green=WPA2, sky=WPA3, yellow=WPA, orange=WEP, red=open.")
        render_dual_globe(cameras_df, networks_df, show_wifi, show_cell, show_bt)

    with tabs[1]:
        col1, col2 = st.columns([3, 2])
        with col1:
            render_encryption_breakdown(networks_df)
        with col2:
            render_network_type_pie(networks_df)
        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            render_ssid_frequency(networks_df)
        with col4:
            render_channel_distribution(networks_df)

    with tabs[2]:
        st.markdown('<div class="section-label">Camera Staleness vs Surrounding Network Age</div>', unsafe_allow_html=True)
        render_temporal_correlation(cameras_df, networks_df)

    with tabs[3]:
        st.markdown('<div class="section-label">WiFi Coverage Gaps by Camera Location</div>', unsafe_allow_html=True)
        render_coverage_gap(cameras_df, networks_df)
        if FOLIUM_AVAILABLE:
            st.markdown('<div class="section-label" style="margin-top:1rem;">Signal Density Heatmap</div>', unsafe_allow_html=True)
            render_signal_heatmap(networks_df)

    with tabs[4]:
        st.markdown('<div class="section-label">Per-Camera Proximity & Risk Summary</div>', unsafe_allow_html=True)
        st.dataframe(
            proximity_df.style.applymap(
                lambda v: "color:#ef4444;font-weight:600" if v == "HIGH"
                          else ("color:#eab308" if v == "MED" else "color:#22c55e"),
                subset=["Risk Flag"]
            ),
            use_container_width=True, hide_index=True,
        )
        csv = proximity_df.to_csv(index=False).encode()
        st.download_button("Export proximity table", csv, "wigle_proximity.csv", "text/csv")

    with tabs[5]:
        st.markdown('<div class="section-label">Integration Assessment</div>', unsafe_allow_html=True)
        render_pros_cons()
        st.divider()
        st.markdown("""
**Recommended integration path (if proceeding):**
1. Add `modules/wigle.py` — API client + bbox search + DataFrame normalizer
2. Add WiGLE as a sidebar toggle in `app.py` (similar to existing layer toggles)
3. Store fetched networks in `st.session_state.wigle_networks` keyed by search radius + camera set hash
4. Add a new Plotly trace to `render_globe()` for WiFi observations
5. Add a new expander section in the flat map / heatmap view for signal density
6. Extend the BLUF section with an open-network count + high-risk site flag

Estimated effort: **1–2 PAUL phases** (ingestion module + UI layer).
Run `/paul:init` to plan it properly.
""")


if __name__ == "__main__":
    main()
