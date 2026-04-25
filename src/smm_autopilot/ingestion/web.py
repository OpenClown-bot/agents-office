from __future__ import annotations

import asyncio
import hashlib
from typing import Optional

import httpx
import structlog
from bs4 import BeautifulSoup

from smm_autopilot.ingestion import FetchedItem

logger = structlog.get_logger()

_BACKOFF_DELAYS: tuple[float, ...] = (5.0, 15.0, 45.0)
_MAX_ATTEMPTS: int = 3


def _extract_og_image(soup: BeautifulSoup) -> Optional[str]:
    meta = soup.find("meta", property="og:image")
    if meta:
        content = meta.get("content")
        if isinstance(content, str):
            return content
    return None


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)
    return None


def _extract_body(soup: BeautifulSoup) -> str:
    article = soup.find("article")
    if article:
        return article.get_text(separator="\n", strip=True)
    main = soup.find("main")
    if main:
        return main.get_text(separator="\n", strip=True)
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)


def _parse_html(html: str, source_url: str) -> Optional[FetchedItem]:
    soup = BeautifulSoup(html, "lxml")
    title = _extract_title(soup)
    body = _extract_body(soup)
    if not body:
        return None
    external_id = hashlib.sha256(source_url.encode()).hexdigest()
    image_url = _extract_og_image(soup)
    return FetchedItem(
        external_id=external_id,
        title=title,
        body=body,
        url=source_url,
        image_url=image_url,
        published_at=None,
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
                    "web_fetch_http_error",
                    url=url,
                    status_code=exc.response.status_code,
                    attempt=attempt,
                    retry_in=delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "web_fetch_http_error_exhausted",
                    url=url,
                    status_code=exc.response.status_code,
                    attempts=attempt,
                )
                return []
        except httpx.HTTPError as exc:
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_DELAYS[attempt - 1]
                logger.warning(
                    "web_fetch_error",
                    url=url,
                    error=str(exc),
                    attempt=attempt,
                    retry_in=delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "web_fetch_error_exhausted",
                    url=url,
                    error=str(exc),
                    attempts=attempt,
                )
                return []

    try:
        item = _parse_html(response.text, url)
    except Exception as exc:
        logger.error("web_parse_failure", url=url, error=str(exc))
        return []

    if item is None:
        logger.warning("web_parse_empty", url=url)
        return []
    return [item]
