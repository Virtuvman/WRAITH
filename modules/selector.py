"""
Selector query, temporal filter, and co-location detection for WRAITH-WiGLE.

Operates on a wigle_networks DataFrame (produced by modules/wigle.py) to:
  - Filter observations by selector field and value (partial, case-insensitive)
  - Apply a date range filter on the lasttime column
  - Detect other networks co-located with selector observations

No UI or network dependencies — pure data module.
"""

from __future__ import annotations

import datetime

import pandas as pd


SELECTOR_FIELDS = ["ssid", "netid", "encryption", "type", "near_camera"]


def query_selector(
    df: pd.DataFrame,
    field: str,
    value: str,
) -> pd.DataFrame:
    """
    Filter wigle_networks DataFrame by a selector field and value.

    Args:
        df: wigle_networks DataFrame (WIGLE_RESULT_COLUMNS + near_camera).
        field: Column to search. Must be one of SELECTOR_FIELDS.
        value: Search string — partial match, case-insensitive.

    Returns:
        Filtered DataFrame. Empty DataFrame (not raises) if no match or df is empty.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else [])

    value = value.strip()
    if not value or field not in df.columns:
        return pd.DataFrame(columns=df.columns)

    mask = df[field].astype(str).str.contains(value, case=False, na=False, regex=False)
    return df[mask].copy()


def apply_temporal_filter(
    df: pd.DataFrame,
    start_date: datetime.date,
    end_date: datetime.date,
) -> pd.DataFrame:
    """
    Filter wigle_networks by lasttime observation date range.

    Rows where lasttime cannot be parsed are excluded silently.

    Args:
        df: wigle_networks DataFrame with a lasttime column.
        start_date: Inclusive start date.
        end_date: Inclusive end date.

    Returns:
        Filtered DataFrame. Empty DataFrame (not raises) if nothing in range or df is empty.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else [])

    if "lasttime" not in df.columns:
        return df.copy()

    parsed = pd.to_datetime(df["lasttime"], errors="coerce")
    mask = (
        parsed.notna()
        & (parsed.dt.date >= start_date)
        & (parsed.dt.date <= end_date)
    )
    return df[mask].copy()


def find_collocated(
    selector_df: pd.DataFrame,
    full_df: pd.DataFrame,
    radius_deg: float = 0.01,
) -> pd.DataFrame:
    """
    Find networks in full_df that appear within radius_deg of any selector observation.

    Uses Euclidean distance on lat/lon (sufficient for OSINT proximity at city scale).
    Excludes the selector's own netids from results.
    Adds a coloc_count column indicating how many selector observations each
    co-located network was near.

    Args:
        selector_df: Filtered selector observations (subset of full_df).
        full_df: Full wigle_networks DataFrame to search within.
        radius_deg: Proximity radius in degrees (~0.01° ≈ 1.1 km).

    Returns:
        Deduplicated DataFrame of co-located networks sorted by coloc_count desc.
        Empty DataFrame (not raises) if either input is empty.
    """
    if selector_df is None or selector_df.empty or full_df is None or full_df.empty:
        return pd.DataFrame()

    required = {"trilat", "trilong", "netid"}
    if not required.issubset(selector_df.columns) or not required.issubset(full_df.columns):
        return pd.DataFrame()

    selector_netids = set(selector_df["netid"].astype(str).unique())
    coloc_indices: dict[int, int] = {}

    for _, srow in selector_df.iterrows():
        slat = srow["trilat"]
        slon = srow["trilong"]
        dist = (
            (full_df["trilat"] - slat).abs() +
            (full_df["trilong"] - slon).abs()
        )
        nearby = full_df[(dist <= radius_deg) & (~full_df["netid"].astype(str).isin(selector_netids))]
        for idx in nearby.index:
            coloc_indices[idx] = coloc_indices.get(idx, 0) + 1

    if not coloc_indices:
        return pd.DataFrame()

    result = full_df.loc[list(coloc_indices.keys())].copy()
    result["coloc_count"] = [coloc_indices[i] for i in result.index]
    result = result.drop_duplicates(subset=["netid"]).sort_values("coloc_count", ascending=False)
    return result.reset_index(drop=True)
