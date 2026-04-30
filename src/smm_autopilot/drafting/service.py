from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timezone

import structlog

from smm_autopilot.db import Database
from smm_autopilot.drafting.prompts import SYSTEM_PROMPT, build_draft_prompt
from smm_autopilot.drafting.validation import validate_attribution
from smm_autopilot.llm.client import LLMClient
from smm_autopilot.models import DraftStatus

logger = structlog.get_logger()

_MAX_DRAFT_RETRIES = 2
_DRAFT_RETRY_BACKOFF_SECONDS = 15.0
_METRICS_COUNTER_NAME = "drafts_generated"


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


def _parse_draft_response(content: str) -> dict[str, object] | None:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        logger.warning("draft_response_not_json", content=content[:200])
        return None
    if not isinstance(data, dict):
        return None
    variant_a = data.get("variant_a")
    variant_b = data.get("variant_b")
    citations = data.get("citations")
    if not isinstance(variant_a, str) or not isinstance(variant_b, str):
        return None
    if not variant_a.strip() or not variant_b.strip():
        return None
    if citations is not None and not isinstance(citations, list):
        return None
    return {
        "variant_a": variant_a,
        "variant_b": variant_b,
        "citations": citations if isinstance(citations, list) else [],
    }


class DraftGeneratorService:
    def __init__(self, db: Database, llm_client: LLMClient) -> None:
        self._db = db
        self._llm = llm_client

    async def generate_drafts(self) -> None:
        items = await self._db.execute_read(
            "SELECT ci.id, ci.raw_item_id, ci.category, ci.is_sensitive, "
            "ci.is_time_sensitive, ci.relevance_score, ci.status, "
            "ri.title, ri.body, ri.url "
            "FROM classified_item ci "
            "JOIN raw_item ri ON ci.raw_item_id = ri.id "
            "WHERE ci.status = 'classified'"
        )
        if not items:
            logger.info("draft_generator_no_classified_items")
            return

        channels = await self._db.execute_read(
            "SELECT id, platform, name, char_limit FROM channel WHERE is_active = 1"
        )
        if not channels:
            logger.info("draft_generator_no_active_channels")
            return

        for item in items:
            any_success = False
            any_failure = False
            for channel in channels:
                success = await self._generate_draft_for_channel(item, channel)
                if success:
                    any_success = True
                else:
                    any_failure = True
            if any_failure and not any_success:
                classified_item_id = int(item["id"])
                await self._mark_generation_failed(classified_item_id, "all_channels_failed")

        logger.info("draft_generator_cycle_complete", item_count=len(items))

    async def _generate_draft_for_channel(
        self,
        item: dict[str, object],
        channel: dict[str, object],
    ) -> bool:
        classified_item_id: int = int(item["id"])  # type: ignore[call-overload]
        channel_id: int = int(channel["id"])  # type: ignore[call-overload]
        char_limit: int = int(channel.get("char_limit") or 0)  # type: ignore[call-overload]

        title: str = item.get("title") or ""  # type: ignore[assignment]
        body: str = item["body"]  # type: ignore[assignment]
        source_url: str = item.get("url") or ""  # type: ignore[assignment]
        is_sensitive: int = int(item.get("is_sensitive", 0))  # type: ignore[call-overload]

        source_text = f"{title}\n\n{body}" if title else body
        user_content = build_draft_prompt(
            source_text,
            char_limit=char_limit if char_limit > 0 else None,
        )

        parsed: dict[str, object] | None = None
        last_error: str | None = None

        for attempt in range(_MAX_DRAFT_RETRIES + 1):
            try:
                llm_response = await self._llm.classify(SYSTEM_PROMPT, user_content)
                if llm_response is None:
                    last_error = "all_llm_providers_failed"
                    if attempt < _MAX_DRAFT_RETRIES:
                        await asyncio.sleep(_DRAFT_RETRY_BACKOFF_SECONDS)
                    continue
                parsed = _parse_draft_response(llm_response.content)
                if parsed is None:
                    last_error = "llm_response_unparseable"
                    if attempt < _MAX_DRAFT_RETRIES:
                        await asyncio.sleep(_DRAFT_RETRY_BACKOFF_SECONDS)
                    continue
                break
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "draft_generation_attempt_failed",
                    classified_item_id=classified_item_id,
                    channel_id=channel_id,
                    attempt=attempt + 1,
                    error=last_error,
                )
                if attempt < _MAX_DRAFT_RETRIES:
                    await asyncio.sleep(_DRAFT_RETRY_BACKOFF_SECONDS)

        if parsed is None:
            return False

        variant_a: str = str(parsed["variant_a"])
        variant_b: str = str(parsed["variant_b"])
        citations_raw: list[object] = list(parsed.get("citations", []))  # type: ignore[call-overload]

        if char_limit > 0:
            variant_a = variant_a[:char_limit]
            variant_b = variant_b[:char_limit]

        citation_urls: list[str] = []
        if source_url:
            citation_urls.append(source_url)
        for c in citations_raw:
            if isinstance(c, str) and c:
                citation_urls.append(c)

        is_verified = validate_attribution(
            variant_a,
            variant_b,
            title,
            body,
            citation_urls,
        )

        status = DraftStatus.ready if is_verified else DraftStatus.unverified
        citations_json = json.dumps(citation_urls)
        now = _utcnow()

        await self._db.execute_write(
            "INSERT OR IGNORE INTO draft "
            "(classified_item_id, channel_id, variant_a_text, variant_b_text, "
            "image_url, citations, status, is_sensitive, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)",
            (
                classified_item_id,
                channel_id,
                variant_a,
                variant_b,
                citations_json,
                status.value,
                is_sensitive,
                now,
                now,
            ),
        )

        await self._increment_drafts_generated()
        return True

    async def _mark_generation_failed(
        self,
        classified_item_id: int,
        error: str | None,
    ) -> None:
        from datetime import timedelta

        next_attempt = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
        await self._db.execute_write(
            "UPDATE classified_item "
            "SET status = 'generation_failed', "
            "generation_retry_count = generation_retry_count + 1, "
            "next_generation_attempt_at = ?, "
            "last_generation_error = ? "
            "WHERE id = ?",
            (next_attempt.isoformat(), error, classified_item_id),
        )
        logger.warning(
            "draft_generation_failed",
            classified_item_id=classified_item_id,
            error=error,
        )

    async def _increment_drafts_generated(self) -> None:
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
