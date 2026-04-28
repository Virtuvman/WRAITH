"""
WiGLE API client for WRAITH-WiGLE.

Provides authenticated bounding-box queries against the WiGLE wireless
network database, response normalization to pandas DataFrames, session-level
caching to respect free-tier rate limits, and a mock data generator for
offline development and testing.

API reference: https://api.wigle.net/swagger
Auth note: Use your WiGLE API NAME token — NOT your login password.
           Obtain from https://wigle.net/account after accepting non-commercial terms.
"""

from __future__ import annotations

import base64
import datetime
import random
from typing import Any

import pandas as pd

try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

WIGLE_SEARCH_URL = "https://api.wigle.net/api/v2/network/search"

WIGLE_RESULT_COLUMNS = [
    "trilat",
    "trilong",
    "ssid",
    "netid",
    "encryption",
    "firsttime",
    "lasttime",
    "channel",
    "type",
    "bestrssi",
    "country",
]

_SEARCH_RADIUS_DEG = 0.01  # ~1.1 km at equator; default scatter for mock data

# ─────────────────────────────────────────────────────────────────────────────
# SESSION CACHE
# ─────────────────────────────────────────────────────────────────────────────

_session_cache: dict[tuple, pd.DataFrame] = {}


# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA POOLS
# ─────────────────────────────────────────────────────────────────────────────

_SSID_POOL = [
    "xfinitywifi", "ATT-WiFi", "Starbucks", "Google Starbucks",
    "NETGEAR_5G", "TP-Link_2G", "DIRECT-xx-HP LaserJet",
    "CoxWifi", "Spectrum2G-XXXX", "linksys", "dlink",
    "FiOS-XXXX", "HOME-XXXX-5G", "AndroidAP", "iPhone",
    "ARRIS-XXXX", "XFINITY", "OPTUS_XXXX", "Telstra_XXXX",
    "BTHub-XXXX", "SKY_XXXX", "VIRGIN-XXXX",
]

_ENCRYPTION_DIST = (
    ["wpa2"] * 55 + ["wpa3"] * 15 + ["wpa"] * 12
    + ["open"] * 10 + ["wep"] * 5 + ["unknown"] * 3
)

_NET_TYPES = ["wifi"] * 70 + ["cell"] * 20 + ["bluetooth"] * 10


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _rand_bssid(rng: random.Random) -> str:
    return ":".join(f"{rng.randint(0, 255):02X}" for _ in range(6))


def _rand_date(rng: random.Random, start_year: int = 2018, end_year: int = 2025) -> str:
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    delta = (end - start).days
    return str(start + datetime.timedelta(days=rng.randint(0, delta)))


# ─────────────────────────────────────────────────────────────────────────────
# API CLIENT
# ─────────────────────────────────────────────────────────────────────────────

def wigle_bbox_search(
    lat: float,
    lon: float,
    radius_deg: float,
    username: str,
    token: str,
    result_limit: int = 100,
) -> list[dict]:
    """
    Query WiGLE /network/search for all networks within a bounding box.

    Args:
        lat: Centre latitude.
        lon: Centre longitude.
        radius_deg: Half-width of bounding box in degrees (~0.01° ≈ 1.1 km).
        username: WiGLE account username.
        token: WiGLE API token (from wigle.net/account — NOT login password).
        result_limit: Max results to request (capped at 100 by WiGLE free tier).

    Returns:
        List of raw result dicts from the WiGLE API.

    Raises:
        RuntimeError: Descriptive message for 401, 412, 429, or other HTTP errors.
        RuntimeError: If requests library is not installed.
    """
    if not _REQUESTS_AVAILABLE:
        raise RuntimeError(
            "requests library not installed. Run: pip install requests"
        )

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

    resp = _requests.get(WIGLE_SEARCH_URL, headers=headers, params=params, timeout=10)

    if resp.status_code == 401:
        raise RuntimeError(
            "WiGLE authentication failed (401). "
            "Check your username and API token at wigle.net/account. "
            "Use the API NAME token — NOT your login password."
        )
    if resp.status_code == 412:
        raise RuntimeError(
            "WiGLE API terms not accepted (412). "
            "Go to wigle.net/account, find the API section, and accept the "
            "non-commercial usage terms. This is a one-time step."
        )
    if resp.status_code == 429:
        raise RuntimeError(
            "WiGLE rate limit hit (429). "
            "The free tier has a limited request quota. "
            "Reduce the number of cameras queried or wait before retrying."
        )

    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZATION
# ─────────────────────────────────────────────────────────────────────────────

def normalize_wigle_response(
    results: list[dict],
    near_camera: str = "",
) -> pd.DataFrame:
    """
    Normalize a raw WiGLE results list to a WRAITH-compatible DataFrame.

    Ensures all WIGLE_RESULT_COLUMNS exist (fills missing with "").
    Returns an empty DataFrame (does not raise) if results is empty.

    Args:
        results: List of dicts from wigle_bbox_search().
        near_camera: Label of the camera this query was centred on.

    Returns:
        pandas DataFrame with standardized columns + near_camera column.
    """
    if not results:
        df = pd.DataFrame(columns=WIGLE_RESULT_COLUMNS + ["near_camera"])
        return df

    df = pd.DataFrame(results)
    for col in WIGLE_RESULT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df["near_camera"] = near_camera
    return df[WIGLE_RESULT_COLUMNS + ["near_camera"]].copy()


# ─────────────────────────────────────────────────────────────────────────────
# CACHED SEARCH
# ─────────────────────────────────────────────────────────────────────────────

def cached_bbox_search(
    lat: float,
    lon: float,
    radius_deg: float,
    username: str,
    token: str,
    near_camera: str = "",
) -> pd.DataFrame:
    """
    Session-cached wrapper around wigle_bbox_search + normalize_wigle_response.

    Identical (lat, lon, radius_deg) tuples (rounded to 4 dp) return a cached
    DataFrame without making a second API call. Cache is in-memory only —
    cleared when the Python process restarts.

    Args:
        lat: Centre latitude.
        lon: Centre longitude.
        radius_deg: Bounding box half-width in degrees.
        username: WiGLE username.
        token: WiGLE API token.
        near_camera: Label attached to all returned records.

    Returns:
        Normalized DataFrame (may be empty if no results).
    """
    cache_key = (round(lat, 4), round(lon, 4), radius_deg)
    if cache_key in _session_cache:
        cached = _session_cache[cache_key].copy()
        if near_camera:
            cached["near_camera"] = near_camera
        return cached

    results = wigle_bbox_search(lat, lon, radius_deg, username, token)
    df = normalize_wigle_response(results, near_camera=near_camera)
    _session_cache[cache_key] = df.copy()
    return df


def clear_session_cache() -> None:
    """Clear the in-memory session cache (e.g. on new search session)."""
    _session_cache.clear()


# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_mock_networks(
    cameras_df: pd.DataFrame,
    networks_per_camera: int = 8,
    seed: int = 99,
) -> pd.DataFrame:
    """
    Generate realistic mock WiGLE observations scattered near each camera.

    Used for offline development, testing, and demo mode when WiGLE credentials
    are not available. Produces WiFi, cell tower, and Bluetooth records with
    realistic distributions of encryption types, SSIDs, channels, and RSSI values.

    Args:
        cameras_df: DataFrame with at least latitude, longitude, location_label,
                    and country columns (WRAITH camera schema).
        networks_per_camera: Average number of network observations per camera.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with WIGLE_RESULT_COLUMNS + near_camera column.
    """
    rng = random.Random(seed)
    rows = []
    for _, cam in cameras_df.iterrows():
        n_net = rng.randint(
            max(1, networks_per_camera - 4),
            networks_per_camera + 6,
        )
        for _ in range(n_net):
            net_type = rng.choice(_NET_TYPES)
            enc = rng.choice(_ENCRYPTION_DIST) if net_type == "wifi" else "n/a"
            first = _rand_date(rng, 2018, 2022)
            last = _rand_date(rng, 2023, 2026)
            rows.append({
                "trilat":      round(cam["latitude"]  + rng.uniform(-_SEARCH_RADIUS_DEG, _SEARCH_RADIUS_DEG), 6),
                "trilong":     round(cam["longitude"] + rng.uniform(-_SEARCH_RADIUS_DEG, _SEARCH_RADIUS_DEG), 6),
                "ssid":        rng.choice(_SSID_POOL) if net_type == "wifi" else "",
                "netid":       _rand_bssid(rng),
                "encryption":  enc,
                "firsttime":   first,
                "lasttime":    last,
                "channel":     rng.choice([1, 6, 11, 36, 40, 44, 48, 0]) if net_type == "wifi" else 0,
                "type":        net_type,
                "bestrssi":    rng.randint(-90, -40),
                "country":     cam.get("country", ""),
                "near_camera": cam.get("location_label", ""),
            })

    if not rows:
        return pd.DataFrame(columns=WIGLE_RESULT_COLUMNS + ["near_camera"])

    return pd.DataFrame(rows)
