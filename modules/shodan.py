"""
Shodan free-tier enrichment module for WRAITH-WiGLE.

Provides IP host lookup and geographic device search against the Shodan API,
with mock fallback for use without a live API key.

No UI or streamlit dependencies — pure data module.
"""

from __future__ import annotations

import logging
import random

import pandas as pd
import requests

logger = logging.getLogger(__name__)

SHODAN_RESULT_COLUMNS = ["ip", "ports", "org", "product", "country", "lat", "lon"]

_MOCK_DEVICES = [
    ("Hikvision camera", "Hikvision"),
    ("MikroTik router", "MikroTik"),
    ("Siemens PLC", "Siemens"),
    ("nginx server", "nginx"),
    ("Apache httpd", "Apache"),
    ("Dahua DVR", "Dahua"),
    ("Axis network camera", "Axis Communications"),
    ("Ubiquiti AirOS", "Ubiquiti Networks"),
]


def shodan_host_lookup(ip: str, api_key: str, mock: bool = False) -> dict:
    """
    Look up a single IP on Shodan.

    Args:
        ip: IPv4 address string.
        api_key: Shodan API key (free tier).
        mock: If True, return synthetic data without making a request.

    Returns:
        Dict with keys: ip, ports, org, hostnames, vulns, error.
        error is None on success, a string on failure. Never raises.
    """
    if mock:
        return {
            "ip": ip,
            "ports": [80, 443],
            "org": "Mock ISP",
            "hostnames": [],
            "vulns": [],
            "error": None,
        }

    try:
        resp = requests.get(
            f"https://api.shodan.io/shodan/host/{ip}",
            params={"key": api_key},
            timeout=10,
        )
        if resp.status_code == 401:
            return {"ip": ip, "ports": [], "org": "", "hostnames": [], "vulns": [], "error": "Invalid API key"}
        if resp.status_code == 404:
            return {"ip": ip, "ports": [], "org": "", "hostnames": [], "vulns": [], "error": "Host not found"}
        if resp.status_code == 429:
            return {"ip": ip, "ports": [], "org": "", "hostnames": [], "vulns": [], "error": "Rate limit — wait 1s and retry"}
        resp.raise_for_status()
        data = resp.json()
        vulns = list(data.get("vulns", {}).keys()) if isinstance(data.get("vulns"), dict) else []
        return {
            "ip": ip,
            "ports": data.get("ports", []),
            "org": data.get("org", ""),
            "hostnames": data.get("hostnames", []),
            "vulns": vulns,
            "error": None,
        }
    except Exception as exc:
        logger.warning("shodan_host_lookup error for %s: %s", ip, exc)
        return {"ip": ip, "ports": [], "org": "", "hostnames": [], "vulns": [], "error": str(exc)}


def shodan_search_near(
    lat: float,
    lon: float,
    radius_km: float,
    api_key: str,
    limit: int = 10,
    mock: bool = False,
) -> pd.DataFrame:
    """
    Search Shodan for exposed devices near a coordinate.

    Args:
        lat: Latitude of search center.
        lon: Longitude of search center.
        radius_km: Search radius in kilometers.
        api_key: Shodan API key.
        limit: Maximum results to return.
        mock: If True, return synthetic data without making a request.

    Returns:
        DataFrame with SHODAN_RESULT_COLUMNS.
        Empty DataFrame on missing key, rate limit, or any error. Never raises.
    """
    if mock:
        return generate_mock_shodan(lat, lon, n=limit)

    if not api_key:
        return pd.DataFrame(columns=SHODAN_RESULT_COLUMNS)

    try:
        resp = requests.get(
            "https://api.shodan.io/shodan/search",
            params={
                "key": api_key,
                "query": f"geo:{lat},{lon},{radius_km}",
                "page": 1,
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning("shodan_search_near HTTP %s for geo:%s,%s", resp.status_code, lat, lon)
            return pd.DataFrame(columns=SHODAN_RESULT_COLUMNS)

        matches = resp.json().get("matches", [])
        rows = []
        for m in matches[:limit]:
            loc = m.get("location", {})
            rows.append({
                "ip": m.get("ip_str", ""),
                "ports": m.get("ports", []),
                "org": m.get("org") or m.get("isp", ""),
                "product": m.get("product", ""),
                "country": loc.get("country_name", ""),
                "lat": loc.get("latitude"),
                "lon": loc.get("longitude"),
            })
        return pd.DataFrame(rows, columns=SHODAN_RESULT_COLUMNS) if rows else pd.DataFrame(columns=SHODAN_RESULT_COLUMNS)

    except Exception as exc:
        logger.warning("shodan_search_near error at %s,%s: %s", lat, lon, exc)
        return pd.DataFrame(columns=SHODAN_RESULT_COLUMNS)


def generate_mock_shodan(lat: float, lon: float, n: int = 5) -> pd.DataFrame:
    """
    Generate synthetic Shodan device records near a coordinate.

    Args:
        lat: Center latitude.
        lon: Center longitude.
        n: Number of records to generate.

    Returns:
        DataFrame with SHODAN_RESULT_COLUMNS.
    """
    rng = random.Random(hash((round(lat, 3), round(lon, 3), n)))
    rows = []
    for i in range(n):
        product, org = _MOCK_DEVICES[i % len(_MOCK_DEVICES)]
        rows.append({
            "ip": f"10.{rng.randint(0,255)}.{rng.randint(0,255)}.{rng.randint(1,254)}",
            "ports": rng.sample([80, 443, 8080, 554, 8888, 22, 23, 9000], k=rng.randint(1, 4)),
            "org": org,
            "product": product,
            "country": "Unknown",
            "lat": lat + rng.uniform(-0.005, 0.005),
            "lon": lon + rng.uniform(-0.005, 0.005),
        })
    return pd.DataFrame(rows, columns=SHODAN_RESULT_COLUMNS)


def enrich_with_shodan(
    df: pd.DataFrame,
    api_key: str,
    mock: bool = False,
) -> pd.DataFrame:
    """
    Enrich a wigle_networks DataFrame with Shodan proximity flags.

    Adds columns:
        shodan_nearby (bool): True if any Shodan devices found within ~1 km.
        shodan_count (int): Number of nearby Shodan devices found.

    Args:
        df: wigle_networks-schema DataFrame with trilat/trilong columns.
        api_key: Shodan API key (may be empty if mock=True).
        mock: If True, use mock Shodan data.

    Returns:
        Input DataFrame with shodan_nearby and shodan_count columns added.
        Empty DataFrame if input is None or empty. Never raises.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    required = {"trilat", "trilong"}
    if not required.issubset(df.columns):
        logger.warning("enrich_with_shodan: missing required columns %s", required - set(df.columns))
        return df.copy()

    result = df.copy()
    result["shodan_nearby"] = False
    result["shodan_count"] = 0

    try:
        # Deduplicate coordinates to avoid redundant API calls
        seen: dict[tuple, tuple[bool, int]] = {}
        for idx, row in result.iterrows():
            coord_key = (round(float(row["trilat"]), 3), round(float(row["trilong"]), 3))
            if coord_key not in seen:
                nearby_df = shodan_search_near(
                    coord_key[0], coord_key[1], 1.0, api_key, mock=mock
                )
                count = len(nearby_df)
                seen[coord_key] = (count > 0, count)
            nearby, count = seen[coord_key]
            result.at[idx, "shodan_nearby"] = nearby
            result.at[idx, "shodan_count"] = count
    except Exception as exc:
        logger.warning("enrich_with_shodan error: %s", exc)

    return result
