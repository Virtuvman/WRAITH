"""Staleness classification utilities for WRAITH.

Implements a 4-tier 90/180/360 day staleness model:
  - CURRENT: < 90 days
  - REVIEW:  90-179 days
  - STALE:   180-359 days
  - EXPIRED: >= 360 days
"""

from __future__ import annotations

import datetime
from typing import Any


STALENESS_ORDER = ["CURRENT", "REVIEW", "STALE", "EXPIRED"]

THRESHOLDS_DAYS = {
    "CURRENT": (0, 90),
    "REVIEW": (90, 180),
    "STALE": (180, 360),
    "EXPIRED": (360, 10_000),
}

STATUS_COLORS = {
    "CURRENT": "#22c55e",  # green
    "REVIEW": "#eab308",   # yellow
    "STALE": "#f97316",    # orange
    "EXPIRED": "#ef4444",  # red
}

STATUS_CLASS = {
    "CURRENT": "green",
    "REVIEW": "yellow",
    "STALE": "orange",
    "EXPIRED": "red",
}

STALENESS_RING = {
    "CURRENT": {"color": STATUS_COLORS["CURRENT"], "width": 1.0, "opacity": 0.92},
    "REVIEW": {"color": STATUS_COLORS["REVIEW"], "width": 1.8, "opacity": 0.86},
    "STALE": {"color": STATUS_COLORS["STALE"], "width": 2.7, "opacity": 0.76},
    "EXPIRED": {"color": STATUS_COLORS["EXPIRED"], "width": 3.5, "opacity": 0.65},
}


def parse_last_seen_date(value: Any) -> datetime.date | None:
    """Parse common date formats (including Excel serial dates) safely."""
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        pass

    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        pass

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

    try:
        serial = float(s)
        if 20000 <= serial <= 80000:
            return datetime.date(1899, 12, 30) + datetime.timedelta(days=int(serial))
    except Exception:
        pass

    return None


def classify_age_days(age_days: float) -> str:
    if age_days < 90:
        return "CURRENT"
    if age_days < 180:
        return "REVIEW"
    if age_days < 360:
        return "STALE"
    return "EXPIRED"


def apply_staleness(df):
    today = datetime.date.today()
    statuses, colors, classes, ages_days, ages_months = [], [], [], [], []

    for _, row in df.iterrows():
        last = parse_last_seen_date(row.get("last_seen", ""))
        age_days = (today - last).days if last is not None else 9999
        status = classify_age_days(age_days)

        statuses.append(status)
        colors.append(STATUS_COLORS[status])
        classes.append(STATUS_CLASS[status])
        ages_days.append(int(age_days))
        ages_months.append(round(age_days / 30.44, 1))

    out = df.copy()
    out["staleness_status"] = statuses
    out["color_hex"] = colors
    out["color_class"] = classes
    out["age_days"] = ages_days
    out["age_months"] = ages_months
    return out
