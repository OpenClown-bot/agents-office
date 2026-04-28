from __future__ import annotations

import os
from datetime import date, datetime, timezone

import structlog

from smm_autopilot.db import Database

logger = structlog.get_logger()

_DEFAULT_MONTHLY_TOKEN_BUDGET = 500_000


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


class UsageTracker:
    def __init__(self, db: Database, budget: int | None = None) -> None:
        self._db = db
        self._budget = budget or int(
            os.environ.get("SMM_LLM_MONTHLY_TOKEN_BUDGET", str(_DEFAULT_MONTHLY_TOKEN_BUDGET))
        )

    async def is_budget_exceeded(self) -> bool:
        today = datetime.now(tz=timezone.utc).date()
        first_of_month = date(today.year, today.month, 1).isoformat()
        rows = await self._db.execute_read(
            "SELECT value FROM metrics WHERE name = 'llm_tokens_total' AND period = 'monthly' AND period_date = ?",
            (first_of_month,),
        )
        current = rows[0]["value"] if rows else 0
        return current >= self._budget

    async def record_call(self, total_tokens: int) -> None:
        today = datetime.now(tz=timezone.utc).date()
        period_dates = _compute_period_dates(today)
        now = _utcnow()
        for period, period_date in period_dates.items():
            await self._db.execute_write(
                "INSERT INTO metrics (name, period, value, period_date, updated_at) "
                "VALUES ('llm_calls_total', ?, 1, ?, ?) "
                "ON CONFLICT (name, period, period_date) DO UPDATE SET "
                "value = value + 1, updated_at = excluded.updated_at",
                (period, period_date, now),
            )
            await self._db.execute_write(
                "INSERT INTO metrics (name, period, value, period_date, updated_at) "
                "VALUES ('llm_tokens_total', ?, ?, ?, ?) "
                "ON CONFLICT (name, period, period_date) DO UPDATE SET "
                "value = value + excluded.value, updated_at = excluded.updated_at",
                (period, total_tokens, period_date, now),
            )

    async def record_error(self) -> None:
        today = datetime.now(tz=timezone.utc).date()
        period_dates = _compute_period_dates(today)
        now = _utcnow()
        for period, period_date in period_dates.items():
            await self._db.execute_write(
                "INSERT INTO metrics (name, period, value, period_date, updated_at) "
                "VALUES ('llm_errors', ?, 1, ?, ?) "
                "ON CONFLICT (name, period, period_date) DO UPDATE SET "
                "value = value + 1, updated_at = excluded.updated_at",
                (period, period_date, now),
            )

    @property
    def budget(self) -> int:
        return self._budget
