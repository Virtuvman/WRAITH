"""
OpenStreetMap / Overpass API enrichment module for WRAITH-WiGLE.

Queries the public Overpass API for POIs (amenities, military facilities,
offices, shops) near WiGLE selector coordinates to provide behavioral and
physical-ISR context.

No UI or streamlit dependencies — pure data module.
Session cache prevents duplicate Overpass requests within a run.
"""

from __future__ import annotations

import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

OSM_RESULT_COLUMNS = ["name", "amenity", "lat", "lon", "osm_id", "tags"]

DEFAULT_POI_TAGS = ["amenity", "military", "office", "government", "shop", "landuse=military"]

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_OVERPASS_USER_AGENT = "WRAITH-OSINT/1.0 (research)"

_osm_cache: dict[tuple, pd.DataFrame] = {}


def _build_overpass_query(lat: float, lon: float, radius_m: float, tags: list[str], timeout: int) -> str:
    """Build an Overpass QL query string for the given tags and location."""
    filters = []
    for tag in tags:
        if "=" in tag:
            key, value = tag.split("=", 1)
            filters.append(f'  node["{key}"="{value}"](around:{radius_m},{lat},{lon});')
        else:
            filters.append(f'  node["{tag}"](around:{radius_m},{lat},{lon});')
    body = "\n".join(filters)
    return f"[out:json][timeout:{timeout}];\n(\n{body}\n);\nout center;"


def overpass_pois(
    lat: float,
    lon: float,
    radius_m: float = 500,
    tags: list[str] | None = None,
    timeout: int = 10,
) -> pd.DataFrame:
    """
    Fetch POIs near a coordinate from the Overpass API.

    Results are cached by (lat, lon, radius_m) rounded to 3 decimal places.
    Subsequent calls with the same coordinates hit the cache, not the network.

    Args:
        lat: Center latitude.
        lon: Center longitude.
        radius_m: Search radius in metres (default 500 m).
        tags: List of Overpass tag filters. Defaults to DEFAULT_POI_TAGS.
              Simple tags like "amenity" produce node["amenity"](...).
              Key=value pairs like "landuse=military" produce node["landuse"="military"](...).
        timeout: Overpass server timeout in seconds.

    Returns:
        DataFrame with OSM_RESULT_COLUMNS.
        Empty DataFrame on timeout, network error, or empty result. Never raises.
    """
    cache_key = (round(lat, 3), round(lon, 3), int(radius_m))
    if cache_key in _osm_cache:
        return _osm_cache[cache_key]

    active_tags = tags if tags is not None else DEFAULT_POI_TAGS
    query = _build_overpass_query(lat, lon, radius_m, active_tags, timeout)

    try:
        resp = requests.post(
            _OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": _OVERPASS_USER_AGENT},
            timeout=timeout + 5,  # HTTP timeout slightly above Overpass timeout
        )
        if resp.status_code != 200:
            logger.warning("overpass_pois HTTP %s for %s,%s", resp.status_code, lat, lon)
            result = pd.DataFrame(columns=OSM_RESULT_COLUMNS)
            _osm_cache[cache_key] = result
            return result

        elements = resp.json().get("elements", [])
        rows = []
        for el in elements:
            el_tags = el.get("tags", {})
            el_type = el.get("type", "node")
            if el_type == "node":
                el_lat = el.get("lat")
                el_lon = el.get("lon")
            else:
                center = el.get("center", {})
                el_lat = center.get("lat")
                el_lon = center.get("lon")

            rows.append({
                "name": el_tags.get("name", ""),
                "amenity": el_tags.get("amenity", ""),
                "lat": el_lat,
                "lon": el_lon,
                "osm_id": el.get("id"),
                "tags": str(el_tags),
            })

        result = pd.DataFrame(rows, columns=OSM_RESULT_COLUMNS) if rows else pd.DataFrame(columns=OSM_RESULT_COLUMNS)

    except requests.Timeout:
        logger.warning("overpass_pois timeout for %s,%s radius=%sm", lat, lon, radius_m)
        result = pd.DataFrame(columns=OSM_RESULT_COLUMNS)
    except Exception as exc:
        logger.warning("overpass_pois error for %s,%s: %s", lat, lon, exc)
        result = pd.DataFrame(columns=OSM_RESULT_COLUMNS)

    _osm_cache[cache_key] = result
    return result


def clear_osm_cache() -> None:
    """Clear the module-level Overpass response cache."""
    _osm_cache.clear()
