"""CSV ingestion and coordinate parsing for WRAITH."""

# pyright: reportMissingModuleSource=false

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from .coord_normalizer import (
    parse_combined_latlon,
    parse_decimal_pair,
    parse_dms_pair,
)


REQUIRED_BASE_COLUMNS = [
    "ip",
    "device_type",
    "model",
    "location_label",
    "last_seen",
    "port",
    "org",
    "country",
]

DECIMAL_LAT_COLUMNS = ["latitude", "lat"]
DECIMAL_LON_COLUMNS = ["longitude", "lon", "lng"]
COMBINED_COLUMNS = ["coordinates", "lat/lon", "lat_lon", "coord", "coords"]
DMS_LAT_COLUMNS = ["dms_lat"]
DMS_LON_COLUMNS = ["dms_lon"]


def _first_existing(df: pd.DataFrame, names: List[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def _normalize_base_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in REQUIRED_BASE_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    return out


def load_csv(uploaded_file) -> Tuple[pd.DataFrame, Dict[str, str], List[Dict[str, object]]]:
    """
    Load and normalize a WRAITH CSV upload.

    Returns:
      (clean_dataframe, detection_info, errors)
    """
    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file, dtype=str).fillna("")
    if df.empty:
        raise ValueError("CSV is empty.")

    df = _normalize_base_columns(df)
    errors: List[Dict[str, object]] = []

    lat_col = _first_existing(df, DECIMAL_LAT_COLUMNS)
    lon_col = _first_existing(df, DECIMAL_LON_COLUMNS)
    comb_col = _first_existing(df, COMBINED_COLUMNS)
    dms_lat_col = _first_existing(df, DMS_LAT_COLUMNS)
    dms_lon_col = _first_existing(df, DMS_LON_COLUMNS)

    detection_info: Dict[str, str]
    parsed_lat: List[float] = []
    parsed_lon: List[float] = []
    keep_rows: List[int] = []

    if lat_col and lon_col:
        detection_info = {"format": "decimal", "lat_column": lat_col, "lon_column": lon_col}
        fmt = "decimal"
        for idx, row in df.iterrows():
            try:
                lat, lon = parse_decimal_pair(row[lat_col], row[lon_col])
                parsed_lat.append(lat)
                parsed_lon.append(lon)
                keep_rows.append(idx)
            except Exception as exc:
                errors.append(
                    {
                        "row_index": idx,
                        "format_detected": fmt,
                        "reason": str(exc),
                        "raw_values": {lat_col: row.get(lat_col, ""), lon_col: row.get(lon_col, "")},
                    }
                )

    elif comb_col:
        detection_info = {"format": "combined", "column": comb_col}
        fmt = "combined"
        for idx, row in df.iterrows():
            try:
                lat, lon = parse_combined_latlon(row[comb_col])
                parsed_lat.append(lat)
                parsed_lon.append(lon)
                keep_rows.append(idx)
            except Exception as exc:
                errors.append(
                    {
                        "row_index": idx,
                        "format_detected": fmt,
                        "reason": str(exc),
                        "raw_values": {comb_col: row.get(comb_col, "")},
                    }
                )

    elif dms_lat_col and dms_lon_col:
        detection_info = {"format": "dms", "lat_column": dms_lat_col, "lon_column": dms_lon_col}
        fmt = "dms"
        for idx, row in df.iterrows():
            try:
                lat, lon = parse_dms_pair(row[dms_lat_col], row[dms_lon_col])
                parsed_lat.append(lat)
                parsed_lon.append(lon)
                keep_rows.append(idx)
            except Exception as exc:
                errors.append(
                    {
                        "row_index": idx,
                        "format_detected": fmt,
                        "reason": str(exc),
                        "raw_values": {
                            dms_lat_col: row.get(dms_lat_col, ""),
                            dms_lon_col: row.get(dms_lon_col, ""),
                        },
                    }
                )
    else:
        raise ValueError(
            "No supported coordinate columns found. Provide decimal lat/lon, combined coordinates, or dms_lat/dms_lon."
        )

    if not keep_rows:
        raise ValueError("No valid coordinate rows could be parsed from the CSV.")

    clean_df = df.iloc[keep_rows].copy()
    clean_df["latitude"] = parsed_lat
    clean_df["longitude"] = parsed_lon

    # Keep app output stable by exposing the expected core fields first.
    ordered = [
        "ip",
        "latitude",
        "longitude",
        "device_type",
        "model",
        "location_label",
        "last_seen",
        "port",
        "org",
        "country",
    ]
    remaining = [c for c in clean_df.columns if c not in ordered]
    clean_df = clean_df[ordered + remaining]

    return clean_df.reset_index(drop=True), detection_info, errors
