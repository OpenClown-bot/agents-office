from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import structlog

from smm_autopilot.ingestion import FetchedItem

logger = structlog.get_logger()

_BACKOFF_DELAYS: tuple[float, ...] = (5.0, 15.0, 45.0)
_MAX_ATTEMPTS: int = 3


def _extract_text(message: dict[str, Any]) -> str:
    text = message.get("text")
    if text:
        return str(text)
    caption = message.get("caption")
    if caption:
        return str(caption)
    return ""


def _extract_image(message: dict[str, Any]) -> Optional[str]:
    photos = message.get("photo")
    if isinstance(photos, list) and photos:
        largest = photos[-1]
        if isinstance(largest, dict):
            file_id = largest.get("file_id")
            if file_id:
                return f"tg://file/{file_id}"
    return None


def _format_published(message: dict[str, Any]) -> Optional[str]:
    date_val = message.get("date")
    if isinstance(date_val, (int, float)):
        return datetime.fromtimestamp(date_val, tz=timezone.utc).isoformat()
    return None


def _message_to_item(message: dict[str, Any], channel_username: str) -> Optional[FetchedItem]:
    message_id = message.get("message_id")
    if message_id is None:
        return None
    external_id = str(message_id)
    body = _extract_text(message)
    if not body:
        return None
    image_url = _extract_image(message)
    published_at = _format_published(message)
    url: Optional[str] = None
    if channel_username:
        url = f"https://t.me/{channel_username}/{message_id}"
    return FetchedItem(
        external_id=external_id,
        title=None,
        body=body,
        url=url,
        image_url=image_url,
        published_at=published_at,
    )


async def fetch(
    client: httpx.AsyncClient,
    bot_token: str,
    channel_username: str,
    offset: int = 0,
) -> list[FetchedItem]:
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = await client.post(
                url,
                json={
                    "offset": offset,
                    "allowed_updates": ["channel_post", "message"],
                    "timeout": 10,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            break
        except httpx.HTTPStatusError as exc:
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_DELAYS[attempt - 1]
                logger.warning(
                    "telegram_fetch_http_error",
                    channel=channel_username,
                    status_code=exc.response.status_code,
                    attempt=attempt,
                    retry_in=delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "telegram_fetch_http_error_exhausted",
                    channel=channel_username,
                    status_code=exc.response.status_code,
                    attempts=attempt,
                )
                return []
        except httpx.HTTPError as exc:
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_DELAYS[attempt - 1]
                logger.warning(
                    "telegram_fetch_error",
                    channel=channel_username,
                    error=str(exc),
                    attempt=attempt,
                    retry_in=delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "telegram_fetch_error_exhausted",
                    channel=channel_username,
                    error=str(exc),
                    attempts=attempt,
                )
                return []

    data: dict[str, Any] = response.json()
    if not data.get("ok"):
        logger.error(
            "telegram_api_not_ok",
            channel=channel_username,
            description=data.get("description", ""),
        )
        return []

    items: list[FetchedItem] = []
    results: list[dict[str, Any]] = data.get("result", [])
    for update in results:
        message: Any = update.get("channel_post") or update.get("message")
        if message is None or not isinstance(message, dict):
            continue
        try:
            item = _message_to_item(message, channel_username)
            if item is not None:
                items.append(item)
        except Exception as exc:
            logger.warning("telegram_message_skip", channel=channel_username, error=str(exc))
    return items
