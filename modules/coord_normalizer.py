"""Coordinate format detection and normalization utilities for WRAITH."""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple


def describe_detection(detection_info: Optional[Dict[str, str]]) -> str:
    """Return a short human-readable description for the UI badge."""
    if not detection_info:
        return "Unknown"
    fmt = str(detection_info.get("format", "unknown")).lower()
    mapping = {
        "decimal": "Decimal degrees",
        "combined": "Combined lat/lon",
        "mgrs": "MGRS",
        "dms": "DMS",
        "utm": "UTM",
        "unknown": "Unknown",
    }
    return mapping.get(fmt, fmt.upper())


def parse_decimal_pair(lat_value: object, lon_value: object) -> Tuple[float, float]:
    """Parse decimal latitude and longitude values and range-check them."""
    try:
        lat = float(str(lat_value).strip())
        lon = float(str(lon_value).strip())
    except Exception as exc:
        raise ValueError("Invalid decimal lat/lon values") from exc

    if not (-90 <= lat <= 90):
        raise ValueError("Latitude out of range")
    if not (-180 <= lon <= 180):
        raise ValueError("Longitude out of range")
    return lat, lon


def parse_combined_latlon(value: object) -> Tuple[float, float]:
    """Parse combined lat/lon text, e.g. '38.9, -77.0'."""
    text = str(value or "").strip()
    if not text:
        raise ValueError("Empty combined coordinate value")

    # Split on comma first, then fall back to whitespace separation.
    if "," in text:
        parts = [p.strip() for p in text.split(",") if p.strip()]
    else:
        parts = [p.strip() for p in text.split() if p.strip()]

    if len(parts) != 2:
        raise ValueError("Expected two coordinate components")

    return parse_decimal_pair(parts[0], parts[1])


_DMS_PATTERN = re.compile(
    r"^\s*(\d{1,3})\D+(\d{1,2})\D+(\d{1,2}(?:\.\d+)?)\D*([NSEW])\s*$",
    re.IGNORECASE,
)


def _dms_to_decimal(text: object) -> float:
    match = _DMS_PATTERN.match(str(text or ""))
    if not match:
        raise ValueError("Invalid DMS value")

    deg, minutes, seconds, hemi = match.groups()
    value = float(deg) + float(minutes) / 60.0 + float(seconds) / 3600.0
    if hemi.upper() in {"S", "W"}:
        value *= -1
    return value


def parse_dms_pair(dms_lat: object, dms_lon: object) -> Tuple[float, float]:
    """Parse DMS latitude and longitude values."""
    lat = _dms_to_decimal(dms_lat)
    lon = _dms_to_decimal(dms_lon)
    return parse_decimal_pair(lat, lon)
