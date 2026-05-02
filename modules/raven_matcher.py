"""
RAVEN Matcher — camera type classifier and DataFrame filter.
Operates on RAVEN schema DataFrames from raven_ingest.
"""
import logging

import pandas as pd

log = logging.getLogger(__name__)

CAMERA_KEYWORDS = [
    "hikvision", "dahua", "axis", "vivotek", "bosch", "hanwha", "samsung",
    "rtsp", "ipcam", "webcam", "traffic", "cctv", "camera", "surveillance",
    "nvr", "dvr", "milestone", "genetec", "mobotix", "avigilon", "pelco",
    "panasonic", "sony", "flir", "reolink", "amcrest",
]

CAMERA_PORTS = {554, 8554, 9000, 37777}  # RTSP and common camera management ports

_CAMERA_TYPE_RULES = [
    ("traffic", ["traffic", "highway", "dot ", "caltrans", "wsdot", "txdot"]),
    ("ip_camera", ["hikvision", "dahua", "axis", "vivotek", "bosch", "hanwha",
                   "avigilon", "pelco", "amcrest", "reolink", "flir"]),
    ("webcam", ["webcam", "web cam", "ipcam"]),
    ("nvr_dvr", ["nvr", "dvr", "milestone", "genetec"]),
]


def classify_camera(row) -> bool:
    """Return True if row looks like a camera device."""
    try:
        product = str(row.get("product") or "").lower()
        label = str(row.get("label") or "").lower()
        org = str(row.get("org") or "").lower()
        combined = f"{product} {label} {org}"

        tags = row.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        tags_lower = [str(t).lower() for t in tags]

        for kw in CAMERA_KEYWORDS:
            if kw in combined:
                return True

        for tag in tags_lower:
            if any(kw in tag for kw in ["camera", "webcam", "iot", "screenshot"]):
                return True

        port = row.get("port")
        if port is not None:
            try:
                if int(port) in CAMERA_PORTS:
                    return True
            except (TypeError, ValueError):
                pass

        return False
    except Exception as exc:
        log.debug("classify_camera error: %s", exc)
        return False


def filter_cameras(df: pd.DataFrame) -> pd.DataFrame:
    """Return only rows classified as camera devices."""
    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else [])
    try:
        mask = df.apply(classify_camera, axis=1)
        return df[mask].reset_index(drop=True)
    except Exception as exc:
        log.error("filter_cameras error: %s", exc)
        return pd.DataFrame(columns=df.columns)


def _classify_camera_type(row) -> str:
    """Classify into a named camera type category."""
    try:
        product = str(row.get("product") or "").lower()
        label = str(row.get("label") or "").lower()
        combined = f"{product} {label}"

        for type_name, keywords in _CAMERA_TYPE_RULES:
            for kw in keywords:
                if kw in combined:
                    return type_name

        return "unknown"
    except Exception:
        return "unknown"


def tag_camera_type(df: pd.DataFrame) -> pd.DataFrame:
    """Add camera_type column to a copy of df."""
    if df is None or df.empty:
        out = df.copy() if df is not None else pd.DataFrame()
        out["camera_type"] = []
        return out
    try:
        out = df.copy()
        out["camera_type"] = out.apply(_classify_camera_type, axis=1)
        return out
    except Exception as exc:
        log.error("tag_camera_type error: %s", exc)
        out = df.copy()
        out["camera_type"] = "unknown"
        return out
