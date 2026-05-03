"""
RAVEN Feeds — public municipal traffic camera APIs and YouTube thumbnail fetchers.
All sources normalize to RAVEN_SCHEMA_COLUMNS. Pure data module — UI-free.
"""
import base64
import hashlib
import json
import logging
import random
from pathlib import Path

import pandas as pd
import requests

from modules.raven_ingest import MOCK_B64_PNG, RAVEN_SCHEMA_COLUMNS, load_raven_csv

log = logging.getLogger(__name__)

CALTRANS_DISTRICTS = [3, 4, 7]
WSDOT_URL = "https://www.wsdot.wa.gov/traffic/api/HighwayCameras/HighwayCamerasREST.svc/GetCamerasAsJSON"
YOUTUBE_CAMERAS_FILE = "data/youtube_cameras.json"
YOUTUBE_THUMB_URL = "https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
CSV_CAMERAS_DIR = "data"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_raven() -> dict:
    base = {col: None for col in RAVEN_SCHEMA_COLUMNS}
    base["tags"] = []
    base["metadata"] = {}
    return base


def _mock_seed(label: str) -> random.Random:
    seed = int(hashlib.md5(label.encode()).hexdigest(), 16) % (2 ** 31)
    return random.Random(seed)


def _safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Caltrans
# ---------------------------------------------------------------------------

def _parse_caltrans_record(row: dict) -> dict:
    cctv = row.get("cctv", row)
    location = cctv.get("location", {})
    image_data = cctv.get("imageData", {})
    static_img = image_data.get("static", {})

    lat = _safe_float(location.get("locationLat"))
    lon = _safe_float(location.get("locationLong"))
    name = location.get("locationName") or location.get("linearReference", "")
    img_url = static_img.get("currentImageURL") or image_data.get("streamingVideoURL")

    district = cctv.get("location", {}).get("district", "")
    out = _empty_raven()
    out["source"] = "municipal"
    out["lat"] = lat
    out["lon"] = lon
    out["label"] = f"Caltrans: {name}"
    out["image_url"] = img_url
    out["tags"] = ["traffic", "caltrans", "municipal"]
    out["metadata"] = {"provider": "Caltrans", "district": district}
    return out


def fetch_caltrans_cameras(
    district: int = 4,
    timeout: int = 10,
    mock: bool = False,
) -> pd.DataFrame:
    if mock:
        rng = _mock_seed(f"caltrans_{district}")
        rows = []
        for i in range(8):
            out = _empty_raven()
            out["source"] = "municipal"
            out["lat"] = round(37.8 + rng.uniform(-0.1, 0.1), 6)
            out["lon"] = round(-122.2 + rng.uniform(-0.1, 0.1), 6)
            out["label"] = f"Caltrans D{district} Camera {i}"
            out["image_url"] = f"https://mock.caltrans.gov/d{district}/{i}.jpg"
            out["tags"] = ["traffic", "caltrans", "municipal"]
            out["metadata"] = {"provider": "Caltrans", "district": str(district)}
            rows.append(out)
        return pd.DataFrame(rows, columns=RAVEN_SCHEMA_COLUMNS)

    try:
        url = f"https://cwwp2.dot.ca.gov/data/d{district}/cctv/cctvStatusD{district:02d}.json"
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        raw_rows = data.get("data", {}).get("row", [])
        parsed = [_parse_caltrans_record(r) for r in raw_rows]
        return pd.DataFrame(parsed, columns=RAVEN_SCHEMA_COLUMNS)
    except Exception as exc:
        log.error("fetch_caltrans_cameras error (district=%s): %s", district, exc)
        return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)


# ---------------------------------------------------------------------------
# WSDOT
# ---------------------------------------------------------------------------

def _parse_wsdot_record(cam: dict) -> dict:
    out = _empty_raven()
    out["source"] = "municipal"
    out["ip"] = None
    out["lat"] = _safe_float(cam.get("Latitude"))
    out["lon"] = _safe_float(cam.get("Longitude"))
    out["label"] = f"WSDOT: {cam.get('Title', '')}"
    out["image_url"] = cam.get("ImageURL") or cam.get("ImageURLSecure")
    out["tags"] = ["traffic", "wsdot", "municipal"]
    out["timestamp"] = cam.get("LastUpdated")
    out["metadata"] = {"provider": "WSDOT", "road": cam.get("RoadName", "")}
    return out


def fetch_wsdot_cameras(
    timeout: int = 10,
    mock: bool = False,
) -> pd.DataFrame:
    if mock:
        rng = _mock_seed("wsdot")
        rows = []
        for i in range(8):
            out = _empty_raven()
            out["source"] = "municipal"
            out["lat"] = round(47.6 + rng.uniform(-0.1, 0.1), 6)
            out["lon"] = round(-122.3 + rng.uniform(-0.1, 0.1), 6)
            out["label"] = f"WSDOT Camera {i}"
            out["image_url"] = f"https://mock.wsdot.wa.gov/cam/{i}.jpg"
            out["tags"] = ["traffic", "wsdot", "municipal"]
            out["metadata"] = {"provider": "WSDOT", "road": f"SR-{99 + i}"}
            rows.append(out)
        return pd.DataFrame(rows, columns=RAVEN_SCHEMA_COLUMNS)

    try:
        resp = requests.get(WSDOT_URL, timeout=timeout)
        resp.raise_for_status()
        cameras = resp.json()
        parsed = [_parse_wsdot_record(c) for c in cameras]
        return pd.DataFrame(parsed, columns=RAVEN_SCHEMA_COLUMNS)
    except Exception as exc:
        log.error("fetch_wsdot_cameras error: %s", exc)
        return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)


# ---------------------------------------------------------------------------
# YouTube thumbnails
# ---------------------------------------------------------------------------

def _load_youtube_cameras(cameras_file: str = YOUTUBE_CAMERAS_FILE) -> list:
    try:
        data = json.loads(Path(cameras_file).read_text(encoding="utf-8"))
        return data.get("cameras", [])
    except Exception as exc:
        log.error("_load_youtube_cameras error: %s", exc)
        return []


def _fetch_youtube_thumb_b64(video_id: str, timeout: int = 8) -> "str | None":
    try:
        url = YOUTUBE_THUMB_URL.format(video_id=video_id)
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return base64.b64encode(resp.content).decode("utf-8")
    except Exception:
        pass
    return None


def fetch_youtube_thumbnails(
    cameras_file: str = YOUTUBE_CAMERAS_FILE,
    timeout: int = 10,
    mock: bool = False,
) -> pd.DataFrame:
    cameras = _load_youtube_cameras(cameras_file)
    if not cameras:
        return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)

    rows = []
    for cam in cameras:
        out = _empty_raven()
        out["source"] = "youtube"
        out["lat"] = _safe_float(cam.get("lat"))
        out["lon"] = _safe_float(cam.get("lon"))
        out["label"] = cam.get("name") or cam.get("city") or "YouTube camera"
        out["tags"] = cam.get("tags", ["traffic", "youtube"])
        out["metadata"] = {
            "city": cam.get("city"),
            "country": cam.get("country"),
            "video_id": cam.get("video_id"),
        }

        if mock:
            out["image_b64"] = MOCK_B64_PNG
            out["image_url"] = None
        else:
            vid = cam.get("video_id", "")
            if vid and not vid.startswith("REPLACE"):
                out["image_b64"] = _fetch_youtube_thumb_b64(vid, timeout)
            out["image_url"] = (
                f"https://img.youtube.com/vi/{vid}/hqdefault.jpg" if vid else None
            )

        rows.append(out)

    return pd.DataFrame(rows, columns=RAVEN_SCHEMA_COLUMNS)


# ---------------------------------------------------------------------------
# CSV cameras
# ---------------------------------------------------------------------------

def fetch_csv_cameras(
    filepath: "str | None" = None,
    mock: bool = False,
) -> pd.DataFrame:
    if mock:
        rng = _mock_seed("csv")
        rows = []
        for i in range(8):
            out = _empty_raven()
            out["source"] = "csv"
            out["lat"] = round(38.9 + rng.uniform(-0.1, 0.1), 6)
            out["lon"] = round(-77.0 + rng.uniform(-0.1, 0.1), 6)
            out["label"] = f"CSV Camera {i}"
            out["image_b64"] = MOCK_B64_PNG
            out["tags"] = ["csv", "camera"]
            out["metadata"] = {"source_file": "mock"}
            rows.append(out)
        return pd.DataFrame(rows, columns=RAVEN_SCHEMA_COLUMNS)

    try:
        if filepath is not None:
            df = load_raven_csv(filepath)
            df["source"] = df["source"].where(df["source"].notna(), "csv")
            return df[RAVEN_SCHEMA_COLUMNS]

        # Scan CSV_CAMERAS_DIR for *.csv files
        frames = []
        for csv_path in sorted(Path(CSV_CAMERAS_DIR).glob("*.csv")):
            try:
                df = load_raven_csv(str(csv_path))
                df["source"] = df["source"].where(df["source"].notna(), "csv")
                frames.append(df[RAVEN_SCHEMA_COLUMNS])
            except Exception as exc:
                log.warning("fetch_csv_cameras: skipping %s — %s", csv_path.name, exc)

        if frames:
            return pd.concat(frames, ignore_index=True)
        return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)

    except Exception as exc:
        log.error("fetch_csv_cameras error: %s", exc)
        return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)


# ---------------------------------------------------------------------------
# Combined feed
# ---------------------------------------------------------------------------

def fetch_all_feeds(
    sources: "list | None" = None,
    caltrans_districts: list = CALTRANS_DISTRICTS,
    youtube_file: str = YOUTUBE_CAMERAS_FILE,
    csv_file: "str | None" = None,
    timeout: int = 10,
    mock: bool = False,
) -> pd.DataFrame:
    if sources is None:
        sources = ["caltrans", "wsdot", "youtube", "csv"]

    frames = []
    try:
        if "caltrans" in sources:
            for d in caltrans_districts:
                frames.append(fetch_caltrans_cameras(district=d, timeout=timeout, mock=mock))

        if "wsdot" in sources:
            frames.append(fetch_wsdot_cameras(timeout=timeout, mock=mock))

        if "youtube" in sources:
            frames.append(fetch_youtube_thumbnails(cameras_file=youtube_file, timeout=timeout, mock=mock))

        if "csv" in sources:
            frames.append(fetch_csv_cameras(filepath=csv_file, mock=mock))

        non_empty = [f for f in frames if not f.empty]
        if not non_empty:
            return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)
        return pd.concat(non_empty, ignore_index=True)

    except Exception as exc:
        log.error("fetch_all_feeds error: %s", exc)
        return pd.DataFrame(columns=RAVEN_SCHEMA_COLUMNS)
