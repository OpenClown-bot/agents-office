from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import struct_time
from typing import Optional

import feedparser  # type: ignore[import-untyped]
import httpx
import structlog

from smm_autopilot.ingestion import FetchedItem

logger = structlog.get_logger()

_BACKOFF_DELAYS: tuple[float, ...] = (5.0, 15.0, 45.0)
_MAX_ATTEMPTS: int = 3


def _parse_published(entry: object) -> Optional[str]:
    published_parsed: Optional[struct_time] = getattr(entry, "published_parsed", None)
    if published_parsed is not None:
        try:
            dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        except (TypeError, ValueError):
            return None
    return None


def _extract_image(entry: object) -> Optional[str]:
    media_content: Optional[list[object]] = getattr(entry, "media_content", None)
    if media_content:
        for media in media_content:
            url: Optional[str] = getattr(media, "get", lambda _: None)("url")
            if url:
                return url
    enclosures: Optional[list[object]] = getattr(entry, "enclosures", None)
    if enclosures:
        for enc in enclosures:
            enc_type: Optional[str] = getattr(enc, "get", lambda _: None)("type")
            if enc_type and enc_type.startswith("image/"):
                enc_url: Optional[str] = getattr(enc, "get", lambda _: None)("href")
                if not enc_url:
                    enc_url = getattr(enc, "get", lambda _: None)("url")
                if enc_url:
                    return enc_url
    return None


def _entry_to_item(entry: object) -> Optional[FetchedItem]:
    external_id = getattr(entry, "id", None) or getattr(entry, "link", None)
    if not external_id:
        return None
    title = getattr(entry, "title", None)
    body = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
    url = getattr(entry, "link", None)
    image_url = _extract_image(entry)
    published_at = _parse_published(entry)
    return FetchedItem(
        external_id=external_id,
        title=title,
        body=body,
        url=url,
        image_url=image_url,
        published_at=published_at,
    )


async def fetch(client: httpx.AsyncClient, url: str) -> list[FetchedItem]:
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            break
        except httpx.HTTPStatusError as exc:
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_DELAYS[attempt - 1]
                logger.warning(
                    "rss_fetch_http_error",
                    url=url,
                    status_code=exc.response.status_code,
                    attempt=attempt,
                    retry_in=delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "rss_fetch_http_error_exhausted",
                    url=url,
                    status_code=exc.response.status_code,
                    attempts=attempt,
                )
                return []
        except httpx.HTTPError as exc:
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_DELAYS[attempt - 1]
                logger.warning(
                    "rss_fetch_error",
                    url=url,
                    error=str(exc),
                    attempt=attempt,
                    retry_in=delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "rss_fetch_error_exhausted",
                    url=url,
                    error=str(exc),
                    attempts=attempt,
                )
                return []

    parsed = feedparser.parse(response.text)
    if parsed.bozo and not parsed.entries:
        logger.error("rss_parse_failure", url=url, bozo_exception=str(parsed.bozo_exception))
        return []

    items: list[FetchedItem] = []
    for entry in parsed.entries:
        try:
            item = _entry_to_item(entry)
            if item is not None:
                items.append(item)
        except Exception as exc:
            logger.warning("rss_entry_skip", url=url, error=str(exc))
    return items
