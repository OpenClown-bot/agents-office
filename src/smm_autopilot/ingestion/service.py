from __future__ import annotations

from datetime import date, datetime, timezone

import httpx
import structlog

from smm_autopilot.db import Database
from smm_autopilot.ingestion import FetchedItem
from smm_autopilot.ingestion import rss, telegram, web

logger = structlog.get_logger()

_METRICS_COUNTER_NAME = "items_ingested"


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _compute_period_dates(today: date) -> dict[str, str]:
    daily = today.isoformat()
    iso_cal = today.isocalendar()
    monday = date.fromisocalendar(iso_cal[0], iso_cal[1], 1)
    weekly = monday.isoformat()
    monthly = date(today.year, today.month, 1).isoformat()
    total = "1970-01-01"
    return {
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "total": total,
    }


class SourceIngester:
    def __init__(self, db: Database, bot_token: str) -> None:
        self._db = db
        self._bot_token = bot_token

    async def run_once(self) -> None:
        sources = await self._db.execute_read(
            "SELECT id, type, url, name FROM source WHERE is_active = 1"
        )
        if not sources:
            logger.info("ingestion_no_active_sources")
            return

        async with httpx.AsyncClient() as client:
            for source in sources:
                source_id: int = source["id"]
                source_type: str = source["type"]
                source_url: str = source["url"]
                try:
                    if source_type == "rss":
                        fetched = await rss.fetch(client, source_url)
                    elif source_type == "telegram_channel":
                        fetched = await telegram.fetch(
                            client, self._bot_token, source_url
                        )
                    elif source_type == "web_page":
                        fetched = await web.fetch(client, source_url)
                    else:
                        logger.warning(
                            "ingestion_unknown_source_type",
                            source_id=source_id,
                            source_type=source_type,
                        )
                        continue
                except Exception as exc:
                    logger.warning(
                        "ingestion_source_error",
                        source_id=source_id,
                        error=str(exc),
                    )
                    continue

                for item in fetched:
                    await self._persist_item(source_id, item)

        logger.info("ingestion_cycle_complete", source_count=len(sources))

    async def _persist_item(self, source_id: int, item: FetchedItem) -> None:
        now = _utcnow()
        try:
            await self._db.execute_write(
                "INSERT INTO raw_item "
                "(source_id, external_id, title, body, url, image_url, "
                "published_at, ingested_at, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
                (
                    source_id,
                    item.external_id,
                    item.title,
                    item.body,
                    item.url,
                    item.image_url,
                    item.published_at,
                    now,
                ),
            )
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                logger.debug(
                    "ingestion_duplicate_skipped",
                    source_id=source_id,
                    external_id=item.external_id,
                )
                return
            logger.error(
                "ingestion_persist_error",
                source_id=source_id,
                external_id=item.external_id,
                error=str(exc),
            )
            return

        await self._increment_items_ingested()

    async def _increment_items_ingested(self) -> None:
        today = datetime.now(tz=timezone.utc).date()
        period_dates = _compute_period_dates(today)
        now = _utcnow()
        for period, period_date in period_dates.items():
            await self._db.execute_write(
                "INSERT INTO metrics (name, period, value, period_date, updated_at) "
                "VALUES (?, ?, 1, ?, ?) "
                "ON CONFLICT (name, period, period_date) DO UPDATE SET "
                "value = value + excluded.value, updated_at = excluded.updated_at",
                (_METRICS_COUNTER_NAME, period, period_date, now),
            )
