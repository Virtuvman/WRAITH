"""
Movement velocity analysis module for WRAITH-WiGLE.

Computes haversine distances and speeds between sequential WiGLE observations
for the same selector (SSID/BSSID), classifies physically implausible movements
as anomalies, and supports multi-selector batch processing.

No UI or streamlit dependencies — pure data module.
No new pip dependencies — pandas + stdlib math only.
"""

from __future__ import annotations

import logging
import math

import pandas as pd

logger = logging.getLogger(__name__)

ANOMALY_THRESHOLD_KMH = 500.0  # Faster than commercial aircraft — implausible for fixed device
VELOCITY_COLUMNS = ["speed_kmh", "distance_km", "time_delta_h", "prev_lat", "prev_lon"]

_EARTH_RADIUS_KM = 6371.0


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance between two lat/lon points in kilometres.

    Args:
        lat1, lon1: Origin coordinate in decimal degrees.
        lat2, lon2: Destination coordinate in decimal degrees.

    Returns:
        Distance in kilometres.
    """
    rlat1, rlon1, rlat2, rlon2 = (
        math.radians(lat1), math.radians(lon1),
        math.radians(lat2), math.radians(lon2),
    )
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return _EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def compute_velocity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute movement velocity between sequential observations.

    Observations are sorted by lasttime ascending before differencing.
    The first observation (no prior) gets speed_kmh=0, distance_km=0,
    time_delta_h=0, prev_lat/lon = own coordinates.

    Args:
        df: DataFrame with columns: trilat, trilong, lasttime.
            Additional columns are preserved in output.

    Returns:
        DataFrame with original columns + VELOCITY_COLUMNS + is_anomaly.
        Empty DataFrame (with correct columns) if input is None or empty.
        Never raises.
    """
    empty_cols = list(df.columns) + VELOCITY_COLUMNS if df is not None and not df.empty else VELOCITY_COLUMNS
    if df is None or df.empty:
        return pd.DataFrame(columns=empty_cols)

    required = {"trilat", "trilong", "lasttime"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        logger.warning("compute_velocity: missing columns %s", missing)
        result = df.copy()
        for col in VELOCITY_COLUMNS:
            result[col] = 0.0
        return result

    try:
        result = df.copy()
        result["_dt"] = pd.to_datetime(result["lasttime"], errors="coerce")
        result = result.sort_values("_dt").reset_index(drop=True)

        # Shift to align previous row
        prev_lat = result["trilat"].shift(1)
        prev_lon = result["trilong"].shift(1)
        prev_dt  = result["_dt"].shift(1)

        def _row_distance(row):
            if pd.isna(row["_prev_lat"]):
                return 0.0
            try:
                return _haversine(
                    float(row["_prev_lat"]), float(row["_prev_lon"]),
                    float(row["trilat"]),    float(row["trilong"]),
                )
            except Exception:
                return 0.0

        result["_prev_lat"] = prev_lat
        result["_prev_lon"] = prev_lon
        result["_prev_dt"]  = prev_dt

        result["distance_km"] = result.apply(_row_distance, axis=1)

        def _time_delta(row):
            if pd.isna(row["_prev_dt"]) or pd.isna(row["_dt"]):
                return 0.0
            delta = (row["_dt"] - row["_prev_dt"]).total_seconds() / 3600.0
            return max(delta, 0.0)

        result["time_delta_h"] = result.apply(_time_delta, axis=1)
        result["speed_kmh"] = result.apply(
            lambda r: r["distance_km"] / r["time_delta_h"] if r["time_delta_h"] > 0 else 0.0,
            axis=1,
        )
        result["prev_lat"] = result["_prev_lat"].fillna(result["trilat"])
        result["prev_lon"] = result["_prev_lon"].fillna(result["trilong"])

        # Drop working columns
        result = result.drop(columns=["_dt", "_prev_lat", "_prev_lon", "_prev_dt"])
        return result

    except Exception as exc:
        logger.warning("compute_velocity error: %s", exc)
        result = df.copy()
        for col in VELOCITY_COLUMNS:
            result[col] = 0.0
        return result


def classify_velocity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add is_anomaly column — True where speed_kmh exceeds ANOMALY_THRESHOLD_KMH.

    Args:
        df: DataFrame with speed_kmh column (output of compute_velocity).

    Returns:
        Input DataFrame with is_anomaly (bool) column added.
        Returns input unchanged if speed_kmh column missing.
        Empty DataFrame if input is None or empty. Never raises.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=(list(df.columns) if df is not None else []) + ["is_anomaly"])

    if "speed_kmh" not in df.columns:
        logger.warning("classify_velocity: speed_kmh column missing")
        return df.copy()

    try:
        result = df.copy()
        result["is_anomaly"] = result["speed_kmh"] > ANOMALY_THRESHOLD_KMH
        return result
    except Exception as exc:
        logger.warning("classify_velocity error: %s", exc)
        result = df.copy()
        result["is_anomaly"] = False
        return result


def compute_velocity_by_selector(
    df: pd.DataFrame,
    field: str = "netid",
) -> pd.DataFrame:
    """
    Compute velocity independently for each unique selector value.

    Each selector's observations are processed in isolation — no cross-selector
    differencing. Anomaly classification is applied to each subset.

    Args:
        df: wigle_networks-schema DataFrame.
        field: Column to group by (default "netid"; also valid: "ssid").

    Returns:
        Combined DataFrame with original columns + VELOCITY_COLUMNS + is_anomaly.
        Empty DataFrame if input is None/empty or field missing. Never raises.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=VELOCITY_COLUMNS + ["is_anomaly"])

    if field not in df.columns:
        logger.warning("compute_velocity_by_selector: field '%s' not in DataFrame", field)
        return pd.DataFrame(columns=VELOCITY_COLUMNS + ["is_anomaly"])

    try:
        frames = []
        for val in df[field].unique():
            subset = df[df[field] == val].copy()
            vel = compute_velocity(subset)
            vel = classify_velocity(vel)
            frames.append(vel)

        if not frames:
            return pd.DataFrame(columns=list(df.columns) + VELOCITY_COLUMNS + ["is_anomaly"])

        return pd.concat(frames, ignore_index=True)

    except Exception as exc:
        logger.warning("compute_velocity_by_selector error: %s", exc)
        return pd.DataFrame(columns=VELOCITY_COLUMNS + ["is_anomaly"])
