"""
RAVEN Media — thumbnail builder, Folium popup HTML, screenshot extractor.
Handles two image sources: base64 strings (Shodan JSON) and local file paths.
"""
import base64
import html
import io
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PILImage = None
    _PIL_AVAILABLE = False

THUMBNAIL_W = 240
THUMBNAIL_H = 180

POPUP_STYLE = (
    "background:#0f172a;color:#e2e8f0;padding:8px;border-radius:6px;"
    "min-width:260px;max-width:280px;font-family:monospace;font-size:12px;"
)


def _load_file_bytes(filepath: str) -> "bytes | None":
    try:
        return Path(filepath).read_bytes()
    except Exception as exc:
        log.debug("_load_file_bytes(%s): %s", filepath, exc)
        return None


def _resize_bytes_to_b64(img_bytes: bytes, w: int = THUMBNAIL_W, h: int = THUMBNAIL_H) -> str:
    if _PIL_AVAILABLE:
        try:
            img = _PILImage.open(io.BytesIO(img_bytes))
            img.thumbnail((w, h), _PILImage.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as exc:
            log.debug("_resize_bytes_to_b64 PIL error: %s", exc)
    return base64.b64encode(img_bytes).decode("utf-8")


def make_thumbnail_b64(row, image_path: "str | None" = None) -> "str | None":
    """Return base64 thumbnail string from local file path or row image_b64. Never raises."""
    try:
        if image_path:
            img_bytes = _load_file_bytes(image_path)
            if img_bytes:
                return _resize_bytes_to_b64(img_bytes)

        b64 = row.get("image_b64") if hasattr(row, "get") else getattr(row, "image_b64", None)
        if b64:
            img_bytes = base64.b64decode(b64)
            return _resize_bytes_to_b64(img_bytes)

        return None
    except Exception as exc:
        log.debug("make_thumbnail_b64 error: %s", exc)
        return None


def build_popup_html(row, image_path: "str | None" = None) -> str:
    """Build self-contained dark-theme HTML popup for a RAVEN device row."""
    try:
        get = (lambda k: row.get(k)) if hasattr(row, "get") else (lambda k: getattr(row, k, None))

        thumb_b64 = make_thumbnail_b64(row, image_path)

        if thumb_b64:
            img_block = (
                f'<img src="data:image/png;base64,{thumb_b64}" '
                'style="width:240px;max-height:180px;object-fit:cover;'
                'border-radius:4px;display:block;margin-bottom:6px;">'
            )
        else:
            img_url = get("image_url")
            if img_url:
                img_block = (
                    f'<img src="{html.escape(str(img_url))}" '
                    'style="width:240px;max-height:180px;object-fit:cover;'
                    'border-radius:4px;display:block;margin-bottom:6px;" '
                    'onerror="this.style.display=\'none\'">'
                )
            else:
                img_block = (
                    '<div style="width:240px;height:60px;background:#1e293b;'
                    'border-radius:4px;display:flex;align-items:center;'
                    'justify-content:center;margin-bottom:6px;'
                    'color:#64748b;font-size:11px;">No image</div>'
                )

        label = html.escape(str(get("label") or get("ip") or "Unknown"))
        ip = html.escape(str(get("ip") or ""))
        port = html.escape(str(get("port") or ""))
        org_raw = str(get("org") or "")
        org = html.escape(org_raw[:40] + ("…" if len(org_raw) > 40 else ""))
        source = html.escape(str(get("source") or ""))
        timestamp = get("timestamp")

        tags = get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        tags_str = html.escape(", ".join(str(t) for t in tags)) if tags else ""

        meta = (
            f'<b style="color:#38bdf8">{label}</b><br>'
            f'<span style="color:#94a3b8">IP:</span> {ip}:{port}<br>'
            f'<span style="color:#94a3b8">Org:</span> {org}<br>'
            f'<span style="color:#94a3b8">Source:</span> {source}<br>'
        )
        if tags_str:
            meta += f'<span style="color:#94a3b8">Tags:</span> {tags_str}<br>'
        if timestamp:
            meta += f'<span style="color:#64748b;font-size:10px;">{html.escape(str(timestamp))}</span>'

        return f'<div style="{POPUP_STYLE}">{img_block}{meta}</div>'

    except Exception as exc:
        log.error("build_popup_html error: %s", exc)
        return "<div>Error building popup</div>"


def build_tooltip_text(row) -> str:
    """Return plain-text tooltip: label | source | lat,lon."""
    try:
        get = (lambda k: row.get(k)) if hasattr(row, "get") else (lambda k: getattr(row, k, None))
        label = str(get("label") or get("ip") or "device")
        source = str(get("source") or "")
        lat = get("lat")
        lon = get("lon")
        coords = f"{float(lat):.4f},{float(lon):.4f}" if lat is not None and lon is not None else ""
        parts = [p for p in [label, source, coords] if p]
        return " | ".join(parts)
    except Exception:
        return ""


def extract_screenshots(
    df: pd.DataFrame,
    output_dir: str = "data/screenshots",
) -> dict:
    """Write image_b64 fields from df to PNG files in output_dir. Never raises."""
    extracted = skipped = errors = 0
    try:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        for _, row in df.iterrows():
            b64 = row.get("image_b64") if hasattr(row, "get") else getattr(row, "image_b64", None)
            if not b64:
                skipped += 1
                continue
            try:
                ip = str(row.get("ip") or "unknown").replace(".", "_")
                port = str(row.get("port") or "0")
                filename = f"{ip}_{port}.png"
                img_bytes = base64.b64decode(b64)
                (out_path / filename).write_bytes(img_bytes)
                extracted += 1
            except Exception as exc:
                log.error("extract_screenshots row error: %s", exc)
                errors += 1

    except Exception as exc:
        log.error("extract_screenshots error: %s", exc)
        errors += 1

    return {"extracted": extracted, "skipped": skipped, "errors": errors, "output_dir": str(output_dir)}
