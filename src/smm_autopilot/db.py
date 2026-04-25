from __future__ import annotations

import asyncio
import sqlite3
from datetime import date, datetime, timezone

from typing import Any, Optional

import aiosqlite
import structlog

from smm_autopilot.config import AppConfig
from smm_autopilot.models import METRICS_COUNTER_NAMES, MetricsPeriod

logger = structlog.get_logger()

_CURRENT_SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('rss', 'telegram_channel', 'web_page')),
    url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    added_by TEXT NOT NULL DEFAULT 'po_manual' CHECK(added_by IN ('po_manual', 'autodiscovery')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(id),
    external_id TEXT NOT NULL,
    title TEXT,
    body TEXT NOT NULL,
    url TEXT,
    image_url TEXT,
    published_at TEXT,
    ingested_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processed', 'error')),
    UNIQUE(source_id, external_id)
);

CREATE TABLE IF NOT EXISTS classified_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_item_id INTEGER NOT NULL UNIQUE REFERENCES raw_item(id),
    category TEXT NOT NULL CHECK(category IN ('privacy', 'circumvention', 'platform_policy', 'competitors', 'product_launches', 'other')),
    is_sensitive INTEGER NOT NULL DEFAULT 0,
    is_time_sensitive INTEGER NOT NULL DEFAULT 0,
    relevance_score REAL NOT NULL DEFAULT 0.0,
    classification_method TEXT NOT NULL DEFAULT 'llm' CHECK(classification_method IN ('llm', 'keyword_fallback')),
    status TEXT NOT NULL DEFAULT 'classified' CHECK(status IN ('classified', 'discarded', 'generation_failed')),
    generation_retry_count INTEGER NOT NULL DEFAULT 0,
    next_generation_attempt_at TEXT,
    last_generation_error TEXT,
    classified_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS channel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL CHECK(platform IN ('telegram', 'x', 'threads', 'instagram')),
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0,
    credentials_provisioned INTEGER NOT NULL DEFAULT 0,
    cadence_posts_per_day INTEGER NOT NULL DEFAULT 1,
    cadence_posts_per_week_target INTEGER,
    publish_window_utc TEXT NOT NULL DEFAULT '',
    char_limit INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS draft (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classified_item_id INTEGER NOT NULL REFERENCES classified_item(id),
    channel_id INTEGER NOT NULL REFERENCES channel(id),
    variant_a_text TEXT NOT NULL,
    variant_b_text TEXT NOT NULL,
    image_url TEXT,
    citations TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'ready' CHECK(status IN ('ready', 'unverified', 'approved', 'rejected', 'deferred', 'expired', 'generation_failed')),
    chosen_variant TEXT CHECK(chosen_variant IN ('a', 'b')),
    po_edit_text TEXT,
    is_sensitive INTEGER NOT NULL DEFAULT 0,
    approved_at TEXT,
    expires_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publish_job (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL REFERENCES draft(id),
    channel_id INTEGER NOT NULL REFERENCES channel(id),
    scheduled_at TEXT NOT NULL,
    published_at TEXT,
    platform_post_id TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'publishing', 'published', 'failed', 'cancelled')),
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retry_count INTEGER NOT NULL DEFAULT 3,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_candidate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK(type IN ('rss', 'telegram_channel', 'web_page')),
    discovered_from_item_id INTEGER NOT NULL REFERENCES raw_item(id),
    status TEXT NOT NULL DEFAULT 'pending_approval' CHECK(status IN ('pending_approval', 'approved', 'rejected')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cadence_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    global_kill_switch INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sensitivity_keyword (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publish_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    publish_job_id INTEGER NOT NULL REFERENCES publish_job(id),
    event TEXT NOT NULL CHECK(event IN ('attempt', 'success', 'failure', 'retry')),
    detail TEXT NOT NULL DEFAULT '',
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
    name TEXT NOT NULL,
    period TEXT NOT NULL CHECK(period IN ('daily', 'weekly', 'monthly', 'total')),
    value INTEGER NOT NULL DEFAULT 0,
    period_date TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (name, period, period_date)
);
"""


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _compute_period_dates(today: date) -> dict[MetricsPeriod, str]:
    daily = today.isoformat()
    iso_cal = today.isocalendar()
    monday = date.fromisocalendar(iso_cal[0], iso_cal[1], 1)
    weekly = monday.isoformat()
    monthly = date(today.year, today.month, 1).isoformat()
    total = "1970-01-01"
    return {
        MetricsPeriod.daily: daily,
        MetricsPeriod.weekly: weekly,
        MetricsPeriod.monthly: monthly,
        MetricsPeriod.total: total,
    }


class Database:
    def __init__(self, config: AppConfig) -> None:
        self._db_path = config.db_path
        self._db: Optional[aiosqlite.Connection] = None
        self._write_lock = asyncio.Lock()
        self._write_queue: asyncio.Queue[tuple[str, tuple[Any, ...], asyncio.Future[None]]] = asyncio.Queue()
        self._writer_task: Optional[asyncio.Task[None]] = None

    async def connect(self) -> None:
        db_path = self._db_path
        db_dir = db_path.parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(db_path))
        self._db.row_factory = sqlite3.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        self._writer_task = asyncio.create_task(self._write_worker())
        logger.info("database_connected", db_path=str(db_path))

    async def close(self) -> None:
        if self._writer_task is not None:
            await self._write_queue.join()
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
            self._writer_task = None
        if self._db is not None:
            await self._db.close()
            self._db = None
        logger.info("database_closed")

    async def _write_worker(self) -> None:
        while True:
            sql, params, future = await self._write_queue.get()
            try:
                if self._db is None:
                    raise RuntimeError("Database not connected")
                await self._db.execute(sql, params)
                await self._db.commit()
                if not future.done():
                    future.set_result(None)
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)
            finally:
                self._write_queue.task_done()

    async def execute_write(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[None] = loop.create_future()
        await self._write_queue.put((sql, params, future))
        await future

    async def execute_read(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        if self._db is None:
            raise RuntimeError("Database not connected")
        async with self._write_lock:
            cursor = await self._db.execute(sql, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def init_schema(self) -> None:
        if self._db is None:
            raise RuntimeError("Database not connected")
        await self._db.executescript(_SCHEMA_SQL)
        await self._db.commit()
        row = await self._db.execute("SELECT version FROM schema_version WHERE id = 1")
        result = await row.fetchone()
        current_version = dict(result)["version"] if result else 0
        if current_version < _CURRENT_SCHEMA_VERSION:
            await self.execute_write(
                "INSERT INTO schema_version (id, version, applied_at) VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET version = excluded.version, applied_at = excluded.applied_at",
                (1, _CURRENT_SCHEMA_VERSION, _utcnow()),
            )
        await self._seed_metrics()
        logger.info("schema_initialized", version=_CURRENT_SCHEMA_VERSION)

    async def _seed_metrics(self) -> None:
        if self._db is None:
            raise RuntimeError("Database not connected")
        rows = await self.execute_read("SELECT COUNT(*) as cnt FROM metrics")
        if rows[0]["cnt"] > 0:
            return
        today = date.today()
        period_dates = _compute_period_dates(today)
        now = _utcnow()
        for counter_name in METRICS_COUNTER_NAMES:
            for period in MetricsPeriod:
                period_date = period_dates[period]
                await self.execute_write(
                    "INSERT INTO metrics (name, period, value, period_date, updated_at) "
                    "VALUES (?, ?, 0, ?, ?)",
                    (counter_name, period.value, period_date, now),
                )
        logger.info("metrics_seeded", counters=len(METRICS_COUNTER_NAMES), periods=len(MetricsPeriod))

    async def get_journal_mode(self) -> str:
        rows = await self.execute_read("PRAGMA journal_mode")
        return str(rows[0]["journal_mode"])
