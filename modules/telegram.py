"""
Telegram public channel scraper for WRAITH-WiGLE.

Scrapes public Telegram channel web previews (t.me/s/{channel}) for
selector keyword mentions. No authentication, no bot token, no new
dependencies — uses requests + stdlib only.

Passive OSINT only. Public channels only. Never raises.
"""

from __future__ import annotations

import html as _html
import logging
import re

import pandas as pd
import requests

logger = logging.getLogger(__name__)

TG_RESULT_COLUMNS = ["channel", "date", "text", "url"]

DEFAULT_CHANNELS = [
    "cybersecuritynews",
    "osintforall",
    "securityaffairs",
    "netblocks",
    "bellingcat",
]

_TG_BASE = "https://t.me/s/{channel}"
_TG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WRAITH-OSINT/1.0; research)",
    "Accept": "text/html",
}

# Regex patterns for t.me/s/ HTML structure
_RE_MESSAGE_TEXT = re.compile(
    r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
    re.DOTALL | re.IGNORECASE,
)
_RE_DATE = re.compile(r'<time[^>]+datetime="([^"]+)"', re.IGNORECASE)
_RE_TAG = re.compile(r"<[^>]+>")

_tg_cache: dict[tuple, pd.DataFrame] = {}


def _strip_tags(text: str) -> str:
    """Remove HTML tags and unescape entities from a string."""
    text = _RE_TAG.sub(" ", text)
    text = _html.unescape(text)
    return " ".join(text.split()).strip()


def scrape_channel(
    channel: str,
    keyword: str,
    limit: int = 20,
    timeout: int = 10,
) -> pd.DataFrame:
    """
    Scrape a public Telegram channel for messages containing keyword.

    Uses the t.me/s/{channel} web preview — no auth, no bot token.
    Returns up to `limit` most recent matching messages.

    Results are cached by (channel, keyword) for the session duration.

    Args:
        channel: Public channel username (e.g. "durov", "bellingcat").
        keyword: Search term (case-insensitive partial match).
        limit: Maximum matching rows to return.
        timeout: HTTP request timeout in seconds.

    Returns:
        DataFrame with TG_RESULT_COLUMNS.
        Empty DataFrame on network error, parse failure, or no match. Never raises.
    """
    cache_key = (channel.lower().strip(), keyword.lower().strip())
    if cache_key in _tg_cache:
        return _tg_cache[cache_key]

    url = _TG_BASE.format(channel=channel.strip())
    try:
        resp = requests.get(url, headers=_TG_HEADERS, timeout=timeout)
        if resp.status_code != 200:
            logger.warning("telegram scrape HTTP %s for channel=%s", resp.status_code, channel)
            result = pd.DataFrame(columns=TG_RESULT_COLUMNS)
            _tg_cache[cache_key] = result
            return result

        html_body = resp.text

        # Extract parallel lists from HTML
        texts_raw = _RE_MESSAGE_TEXT.findall(html_body)
        dates = _RE_DATE.findall(html_body)

        # Build message URLs: t.me/{channel}/\d+
        url_pattern = re.compile(
            rf'href="(https://t\.me/{re.escape(channel.strip())}/\d+)"',
            re.IGNORECASE,
        )
        urls = url_pattern.findall(html_body)

        # Strip tags from message texts
        texts = [_strip_tags(t) for t in texts_raw]

        # Zip into rows, padding shorter lists with empty strings
        max_len = max(len(texts), len(dates), len(urls), 1)
        texts  += [""] * (max_len - len(texts))
        dates  += [""] * (max_len - len(dates))
        urls   += [""] * (max_len - len(urls))

        kw_lower = keyword.lower()
        rows = []
        for text, date, msg_url in zip(texts, dates, urls):
            if not text:
                continue
            if kw_lower and kw_lower not in text.lower():
                continue
            rows.append({
                "channel": channel.strip(),
                "date": date,
                "text": text,
                "url": msg_url,
            })

        result = (
            pd.DataFrame(rows[:limit], columns=TG_RESULT_COLUMNS)
            if rows
            else pd.DataFrame(columns=TG_RESULT_COLUMNS)
        )

    except requests.Timeout:
        logger.warning("telegram scrape timeout for channel=%s", channel)
        result = pd.DataFrame(columns=TG_RESULT_COLUMNS)
    except Exception as exc:
        logger.warning("telegram scrape error for channel=%s: %s", channel, exc)
        result = pd.DataFrame(columns=TG_RESULT_COLUMNS)

    _tg_cache[cache_key] = result
    return result


def search_selector_in_channels(
    keyword: str,
    channels: list[str] | None = None,
    limit_per_channel: int = 10,
) -> pd.DataFrame:
    """
    Search multiple public Telegram channels for a selector keyword.

    Args:
        keyword: Search term (case-insensitive partial match).
        channels: List of channel usernames. Defaults to DEFAULT_CHANNELS.
        limit_per_channel: Max results per channel.

    Returns:
        Combined DataFrame with TG_RESULT_COLUMNS, deduplicated by url,
        sorted by date descending (best-effort). Empty DataFrame if all
        channels return no results. Never raises.
    """
    active_channels = channels if channels is not None else DEFAULT_CHANNELS
    frames = []
    for ch in active_channels:
        try:
            df = scrape_channel(ch, keyword, limit=limit_per_channel)
            if not df.empty:
                frames.append(df)
        except Exception as exc:
            logger.warning("search_selector_in_channels skipping %s: %s", ch, exc)

    if not frames:
        return pd.DataFrame(columns=TG_RESULT_COLUMNS)

    combined = pd.concat(frames, ignore_index=True)

    # Deduplicate by url (empty urls kept — may be from same channel)
    combined = combined.drop_duplicates(subset=["url"], keep="first")

    # Sort by date descending (best-effort — ISO strings sort correctly)
    try:
        combined = combined.sort_values("date", ascending=False).reset_index(drop=True)
    except Exception:
        pass

    return combined


def clear_tg_cache() -> None:
    """Clear the module-level Telegram scrape cache."""
    _tg_cache.clear()
