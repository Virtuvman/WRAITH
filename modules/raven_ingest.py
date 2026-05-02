"""
RAVEN Ingest — Shodan/FOFA JSON parser and mock data generator.
Normalizes all records to RAVEN_SCHEMA_COLUMNS regardless of source format.
"""
import json
import hashlib
import random
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

RAVEN_SCHEMA_COLUMNS = [
    "source", "lat", "lon", "label", "ip", "port", "org",
    "product", "tags", "image_b64", "image_url", "timestamp", "metadata",
]

# Minimal valid 1x1 transparent PNG (base64)
MOCK_B64_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

_MOCK_PRODUCTS = [
    "Hikvision IP Camera",
    "Dahua IPC",
    "Axis M3106",
    "Vivotek FD9391",
    "Bosch Flexidome",
    "traffic camera MJPEG",
]

_MOCK_ORGS = [
    "AS7922 Comcast Cable",
    "AS20115 Charter Communications",
    "AS701 Verizon Business",
    "AS6167 Cellco Partnership",
    "AS7018 AT&T Services",
    "AS11426 Charter Communications",
]


def _empty_record() -> dict:
    base = {col: None for col in RAVEN_SCHEMA_COLUMNS}
    base["tags"] = []
    base["metadata"] = {}
    return base


def _safe_float(val) -> "float | None":
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_shodan_record(record: dict) -> dict:
    out = _empty_record()
    loc = record.get("location") or {}
    screenshot = record.get("screenshot") or {}

    out["source"] = "shodan"
    out["ip"] = record.get("ip_str")
    out["port"] = record.get("port")
    out["org"] = record.get("org")
    out["product"] = record.get("product")
    out["tags"] = list(record.get("tags") or [])
    out["lat"] = _safe_float(loc.get("latitude"))
    out["lon"] = _safe_float(loc.get("longitude"))
    out["image_b64"] = screenshot.get("data")
    out["image_url"] = None
    out["timestamp"] = record.get("timestamp")

    product = out["product"] or out["org"] or out["ip"] or ""
    out["label"] = product

    out["metadata"] = {
        "country": loc.get("country_code"),
        "city": loc.get("city"),
        "screenshot_labels": screenshot.get("labels", []),
        "mime": screenshot.get("mime"),
    }
    return out


def _parse_fofa_record(record: dict) -> dict:
    out = _empty_record()

    out["source"] = "fofa"
    out["ip"] = record.get("ip")
    out["port"] = record.get("port")
    out["org"] = record.get("as_organization") or record.get("isp")
    out["product"] = record.get("title") or record.get("product")
    out["tags"] = []
    out["lat"] = _safe_float(record.get("latitude"))
    out["lon"] = _safe_float(record.get("longitude"))
    out["image_b64"] = record.get("screenshot") or record.get("base64_screenshot")
    out["image_url"] = None
    out["timestamp"] = record.get("lastupdatetime") or record.get("updated_time")

    product = out["product"] or out["ip"] or ""
    out["label"] = product

    out["metadata"] = {
        "country": record.get("country_name"),
        "city": record.get("city"),
        "host": record.get("host"),
        "protocol": record.get("protocol"),
    }
    return out


def _detect_format(data: dict) -> str:
    if not isinstance(data, dict):
        return "unknown"
    if "matches" in data:
        return "shodan"
    if "ip_str" in data:
        return "shodan_single"
    if "results" in data:
        results = data.get("results", [])
        if results and isinstance(results[0], dict):
            return "fofa"
    return "unknown"


def load_raven_file(filepath: str) -> pd.DataFrame:
    """Load a Shodan or FOFA JSON export and return a RAVEN schema DataFrame."""
    try:
        path = Path(filepath)
        text = path.read_text(encoding="utf-8")

        # Support newline-delimited JSON (one record per line)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if len(lines) > 1:
            try:
                records = [json.loads(ln) for ln in lines]
                parsed = [_parse_shodan_record(r) for r in records]
                return pd.DataFrame(parsed, columns=RAVEN_SCHEMA_COLUMNS)
            except Exception:
                pass

        data = json.loads(text)
        fmt = _detect_format(data)

        if fmt == "shodan":
            parsed = [_parse_shodan_record(r) for r in data.get("matches", [])]
        elif fmt == "shodan_single":
            parsed = [_parse_shodan_record(data)]
        elif fmt == "fofa":
            parsed = [_parse_fofa_record(r) for r in data.get("results", [])]
        else:
            log.warning("raven_ingest: unknown format in %s", filepath)
            return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)

        return pd.DataFrame(parsed, columns=RAVEN_SCHEMA_COLUMNS)

    except Exception as exc:
        log.error("raven_ingest.load_raven_file error: %s", exc)
        return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)


def generate_mock_raven(
    lat: float = 37.77,
    lon: float = -122.41,
    n: int = 10,
) -> pd.DataFrame:
    """Generate n mock RAVEN camera records around (lat, lon)."""
    seed = int(hashlib.md5(f"{round(lat,2)},{round(lon,2)},{n}".encode()).hexdigest(), 16) % (2**31)
    rng = random.Random(seed)

    rows = []
    for i in range(n):
        product = _MOCK_PRODUCTS[i % len(_MOCK_PRODUCTS)]
        org = _MOCK_ORGS[i % len(_MOCK_ORGS)]
        ip = f"10.{rng.randint(0,255)}.{rng.randint(0,255)}.{rng.randint(1,254)}"
        port = rng.choice([80, 443, 8080, 554])
        rec = _empty_record()
        rec["source"] = "shodan"
        rec["lat"] = round(lat + rng.uniform(-0.01, 0.01), 6)
        rec["lon"] = round(lon + rng.uniform(-0.01, 0.01), 6)
        rec["ip"] = ip
        rec["port"] = port
        rec["org"] = org
        rec["product"] = product
        rec["label"] = product
        rec["tags"] = ["screenshot", "camera"]
        rec["image_b64"] = MOCK_B64_PNG
        rec["image_url"] = None
        rec["timestamp"] = "2026-01-15T10:00:00.000000"
        rec["metadata"] = {"country": "US", "city": "Mock City"}
        rows.append(rec)

    return pd.DataFrame(rows, columns=RAVEN_SCHEMA_COLUMNS)
