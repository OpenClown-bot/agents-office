from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path


import pytest
import pytest_asyncio

from smm_autopilot.config import AppConfig, load_config
from smm_autopilot.db import Database, _compute_period_dates
from smm_autopilot.models import METRICS_COUNTER_NAMES, MetricsPeriod


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        db_path=tmp_path / "test.db",
        log_level="INFO",
        telegram_bot_token="",
        telegram_publish_chat_id="",
        x_api_key="",
        x_api_secret="",
        x_access_token="",
        x_access_secret="",
        threads_access_token="",
        instagram_access_token="",
        llm_api_key="",
        llm_provider="glm-4-flash",
        po_telegram_user_id="",
    )


@pytest_asyncio.fixture
async def db(config: AppConfig) -> Database:
    database = Database(config)
    await database.connect()
    await database.init_schema()
    yield database
    await database.close()


def test_compute_period_dates() -> None:
    today = date(2026, 4, 24)
    dates = _compute_period_dates(today)
    assert dates[MetricsPeriod.daily] == "2026-04-24"
    assert dates[MetricsPeriod.weekly] == "2026-04-20"
    assert dates[MetricsPeriod.monthly] == "2026-04-01"
    assert dates[MetricsPeriod.total] == "1970-01-01"


@pytest.mark.asyncio
async def test_wal_mode(db: Database) -> None:
    mode = await db.get_journal_mode()
    assert mode == "wal"


@pytest.mark.asyncio
async def test_schema_tables_exist(db: Database, config: AppConfig) -> None:
    conn = sqlite3.connect(str(config.db_path))
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    expected = {
        "schema_version",
        "source",
        "raw_item",
        "classified_item",
        "channel",
        "draft",
        "publish_job",
        "source_candidate",
        "cadence_config",
        "sensitivity_keyword",
        "publish_log",
        "metrics",
    }
    assert expected.issubset(tables)


@pytest.mark.asyncio
async def test_metrics_seeded(db: Database) -> None:
    rows = await db.execute_read("SELECT COUNT(*) as cnt FROM metrics")
    assert rows[0]["cnt"] == len(METRICS_COUNTER_NAMES) * len(MetricsPeriod)

    counter_names_in_db = await db.execute_read("SELECT DISTINCT name FROM metrics ORDER BY name")
    db_names = {r["name"] for r in counter_names_in_db}
    assert db_names == set(METRICS_COUNTER_NAMES)

    periods_in_db = await db.execute_read("SELECT DISTINCT period FROM metrics ORDER BY period")
    db_periods = {r["period"] for r in periods_in_db}
    assert db_periods == {"daily", "weekly", "monthly", "total"}


@pytest.mark.asyncio
async def test_metrics_period_dates(db: Database) -> None:
    rows = await db.execute_read(
        "SELECT period, period_date FROM metrics WHERE name = ?",
        ("items_ingested",),
    )
    by_period = {r["period"]: r["period_date"] for r in rows}
    today = datetime.now(tz=timezone.utc).date()
    iso_cal = today.isocalendar()
    monday = date.fromisocalendar(iso_cal[0], iso_cal[1], 1)
    assert by_period["daily"] == today.isoformat()
    assert by_period["weekly"] == monday.isoformat()
    assert by_period["monthly"] == date(today.year, today.month, 1).isoformat()
    assert by_period["total"] == "1970-01-01"


@pytest.mark.asyncio
async def test_metrics_composite_pk(db: Database, config: AppConfig) -> None:
    conn = sqlite3.connect(str(config.db_path))
    cursor = conn.execute("PRAGMA table_info(metrics)")
    cols = {row[1] for row in cursor.fetchall()}
    conn.close()
    assert "name" in cols
    assert "period" in cols
    assert "period_date" in cols


@pytest.mark.asyncio
async def test_schema_version(db: Database) -> None:
    rows = await db.execute_read("SELECT version FROM schema_version WHERE id = 1")
    assert len(rows) == 1
    assert rows[0]["version"] >= 1


@pytest.mark.asyncio
async def test_write_queue(db: Database) -> None:
    await db.execute_write(
        "INSERT INTO sensitivity_keyword (keyword, created_at) VALUES (?, ?)",
        ("test_keyword", "2026-04-24T00:00:00+00:00"),
    )
    rows = await db.execute_read(
        "SELECT keyword FROM sensitivity_keyword WHERE keyword = ?",
        ("test_keyword",),
    )
    assert len(rows) == 1
    assert rows[0]["keyword"] == "test_keyword"


@pytest.mark.asyncio
async def test_db_created_at_configured_path(config: AppConfig) -> None:
    database = Database(config)
    await database.connect()
    await database.init_schema()
    assert config.db_path.exists()
    await database.close()


@pytest.mark.asyncio
async def test_metrics_seeding_idempotent_partial_state(config: AppConfig) -> None:
    database = Database(config)
    await database.connect()
    if database._db is None:
        pytest.skip("db not connected")
    await database._db.executescript(
        "CREATE TABLE IF NOT EXISTS metrics ("
        "name TEXT NOT NULL, period TEXT NOT NULL, "
        "value INTEGER NOT NULL DEFAULT 0, "
        "period_date TEXT NOT NULL, updated_at TEXT NOT NULL, "
        "PRIMARY KEY (name, period, period_date))"
    )
    await database._db.commit()
    from smm_autopilot.db import _compute_period_dates, _utcnow
    today = datetime.now(tz=timezone.utc).date()
    period_dates = _compute_period_dates(today)
    now = _utcnow()
    half_names = METRICS_COUNTER_NAMES[:5]
    for counter_name in half_names:
        for period in MetricsPeriod:
            await database.execute_write(
                "INSERT INTO metrics (name, period, value, period_date, updated_at) "
                "VALUES (?, ?, 0, ?, ?)",
                (counter_name, period.value, period_dates[period], now),
            )
    rows_before = await database.execute_read("SELECT COUNT(*) as cnt FROM metrics")
    assert rows_before[0]["cnt"] < len(METRICS_COUNTER_NAMES) * len(MetricsPeriod)
    await database._seed_metrics()
    rows_after = await database.execute_read("SELECT COUNT(*) as cnt FROM metrics")
    expected_total = len(METRICS_COUNTER_NAMES) * len(MetricsPeriod)
    assert rows_after[0]["cnt"] == expected_total
    await database.close()


def test_log_level_from_env(monkeypatch: object) -> None:
    monkeypatch.setenv("SMM_LOG_LEVEL", "DEBUG")  # type: ignore[attr-defined]
    cfg = load_config()
    assert cfg.log_level == "DEBUG"
