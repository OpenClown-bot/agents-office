from __future__ import annotations

import json
from datetime import date, datetime, timezone

import structlog

from smm_autopilot.classifier.prompts import TAXONOMY, SYSTEM_PROMPT, build_user_content
from smm_autopilot.classifier.sensitivity import check_sensitivity, load_sensitivity_keywords
from smm_autopilot.db import Database
from smm_autopilot.llm.client import LLMClient
from smm_autopilot.models import (
    Category,
    ClassifiedItemStatus,
    ClassificationMethod,
)

logger = structlog.get_logger()

_METRICS_COUNTER_NAME = "items_classified"

_KEYWORD_CATEGORY_MAP: dict[str, Category] = {
    "vpn": Category.circumvention,
    "privacy": Category.privacy,
    "censorship": Category.circumvention,
    "surveillance": Category.privacy,
    "ban": Category.platform_policy,
    "block": Category.circumvention,
    "firewall": Category.circumvention,
    "proxy": Category.circumvention,
    "encryption": Category.privacy,
    "competitor": Category.competitors,
    "launch": Category.product_launches,
}


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


def _parse_llm_response(content: str) -> tuple[Category, float] | None:
    try:
        data = json.loads(content.strip())
    except json.JSONDecodeError:
        logger.warning("llm_response_not_json", content=content[:200])
        return None

    if not isinstance(data, dict):
        return None

    category_str = data.get("category")
    score = data.get("relevance_score")

    if not isinstance(category_str, str) or not isinstance(score, (int, float)):
        return None

    if category_str not in TAXONOMY:
        return None

    score = float(score)
    if score < 0.0 or score > 1.0:
        score = max(0.0, min(1.0, score))

    return Category(category_str), score


def _keyword_fallback_classify(body: str) -> tuple[Category, float]:
    lower_body = body.lower()
    for keyword, category in _KEYWORD_CATEGORY_MAP.items():
        if keyword in lower_body:
            return category, 0.3
    return Category.other, 0.1


class ClassifierService:
    def __init__(self, db: Database, llm_client: LLMClient) -> None:
        self._db = db
        self._llm = llm_client

    async def classify_pending(self) -> None:
        rows = await self._db.execute_read(
            "SELECT id, source_id, external_id, title, body, url, image_url, "
            "published_at, ingested_at FROM raw_item WHERE status = 'pending'"
        )
        if not rows:
            logger.info("classifier_no_pending_items")
            return

        keywords = await load_sensitivity_keywords(self._db)

        for row in rows:
            await self._classify_item(row, keywords)

        logger.info("classifier_cycle_complete", item_count=len(rows))

    async def _classify_item(
        self, raw_item: dict[str, object], keywords: list[str]
    ) -> None:
        raw_item_id: int = int(raw_item["id"])  # type: ignore[call-overload]
        title: str = raw_item.get("title") or ""  # type: ignore[assignment]
        body: str = raw_item["body"]  # type: ignore[assignment]
        source_text = f"{title}\n\n{body}" if title else body

        is_sensitive = check_sensitivity(body, keywords)

        category: Category
        relevance_score: float
        classification_method: ClassificationMethod
        is_time_sensitive: bool

        llm_response = await self._llm.classify(SYSTEM_PROMPT, build_user_content(source_text))

        if llm_response is not None:
            parsed = _parse_llm_response(llm_response.content)
            if parsed is not None:
                category, relevance_score = parsed
                classification_method = ClassificationMethod.llm
                is_time_sensitive = _detect_time_sensitivity(body)
            else:
                category, relevance_score = _keyword_fallback_classify(body)
                classification_method = ClassificationMethod.keyword_fallback
                is_time_sensitive = True
        else:
            category, relevance_score = _keyword_fallback_classify(body)
            classification_method = ClassificationMethod.keyword_fallback
            is_time_sensitive = True

        status = ClassifiedItemStatus.discarded if category == Category.other else ClassifiedItemStatus.classified

        now = _utcnow()
        await self._db.execute_write(
            "INSERT INTO classified_item "
            "(raw_item_id, category, is_sensitive, is_time_sensitive, "
            "relevance_score, classification_method, status, classified_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                raw_item_id,
                category.value,
                int(is_sensitive),
                int(is_time_sensitive),
                relevance_score,
                classification_method.value,
                status.value,
                now,
            ),
        )

        await self._db.execute_write(
            "UPDATE raw_item SET status = 'processed' WHERE id = ?",
            (raw_item_id,),
        )

        await self._increment_items_classified()

    async def _increment_items_classified(self) -> None:
        today = datetime.now(tz=timezone.utc).date()
        period_dates = _compute_period_dates(today)
        now = _utcnow()
        for period, period_date in period_dates.items():
            await self._db.execute_write(
                "INSERT INTO metrics (name, period, value, period_date, updated_at) "
                "VALUES (?, ?, 1, ?, ?) "
                "ON CONFLICT (name, period, period_date) DO UPDATE SET "
                "value = value + 1, updated_at = excluded.updated_at",
                (_METRICS_COUNTER_NAME, period, period_date, now),
            )


def _detect_time_sensitivity(body: str) -> bool:
    time_keywords = [
        "breaking",
        "urgent",
        "just announced",
        "today",
        "this week",
        "deadline",
        "expires",
        "last chance",
        "now",
        "immediately",
        "live",
        "update:",
        "alert",
    ]
    lower = body.lower()
    return any(kw in lower for kw in time_keywords)
