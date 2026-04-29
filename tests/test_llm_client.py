from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio

from smm_autopilot.config import AppConfig
from smm_autopilot.db import Database
from smm_autopilot.llm.client import LLMClient
from smm_autopilot.llm.providers import GLMProvider, LLMResponse, QwenProvider
from smm_autopilot.llm.usage import UsageTracker


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
        llm_api_key="test-key",
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


def _make_glm_response(content: str, total_tokens: int = 50) -> httpx.Response:
    body = {
        "choices": [{"message": {"content": content}}],
        "usage": {"total_tokens": total_tokens},
    }
    return httpx.Response(200, json=body)


def _make_qwen_response(content: str, total_tokens: int = 50) -> httpx.Response:
    body = {
        "choices": [{"message": {"content": content}}],
        "usage": {"total_tokens": total_tokens},
    }
    return httpx.Response(200, json=body)


class SyncMockTransport(httpx.AsyncBaseTransport):
    def __init__(self, handler: Any) -> None:
        self._handler = handler

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return self._handler(request)


@pytest.mark.asyncio
async def test_glm_provider_success() -> None:
    response_json = {
        "choices": [{"message": {"content": '{"category": "privacy", "relevance_score": 0.8}'}}],
        "usage": {"total_tokens": 50},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_json)

    provider = GLMProvider(api_key="test-key", timeout=10.0)
    async with httpx.AsyncClient(transport=SyncMockTransport(handler)) as client:
        result = await provider.call(client, "system", "user")

    assert result.content == '{"category": "privacy", "relevance_score": 0.8}'
    assert result.total_tokens == 50


@pytest.mark.asyncio
async def test_qwen_provider_success() -> None:
    response_json = {
        "choices": [{"message": {"content": '{"category": "circumvention", "relevance_score": 0.9}'}}],
        "usage": {"total_tokens": 60},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_json)

    provider = QwenProvider(api_key="test-key", timeout=10.0)
    async with httpx.AsyncClient(transport=SyncMockTransport(handler)) as client:
        result = await provider.call(client, "system", "user")

    assert result.content == '{"category": "circumvention", "relevance_score": 0.9}'
    assert result.total_tokens == 60


@pytest.mark.asyncio
async def test_glm_provider_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    provider = GLMProvider(api_key="test-key", timeout=10.0)
    async with httpx.AsyncClient(transport=SyncMockTransport(handler)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await provider.call(client, "system", "user")


@pytest.mark.asyncio
async def test_qwen_provider_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout")

    class TimeoutTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout")

    provider = QwenProvider(api_key="test-key", timeout=0.001)
    async with httpx.AsyncClient(transport=TimeoutTransport()) as client:
        with pytest.raises(httpx.ReadTimeout):
            await provider.call(client, "system", "user")


@pytest.mark.asyncio
async def test_usage_tracker_record_call(db: Database) -> None:
    tracker = UsageTracker(db)
    await tracker.record_call(total_tokens=100)

    rows = await db.execute_read(
        "SELECT period, value FROM metrics WHERE name = 'llm_calls_total' ORDER BY period"
    )
    assert len(rows) == 4
    for row in rows:
        assert row["value"] == 1

    token_rows = await db.execute_read(
        "SELECT period, value FROM metrics WHERE name = 'llm_tokens_total' ORDER BY period"
    )
    assert len(token_rows) == 4
    for row in token_rows:
        assert row["value"] == 100


@pytest.mark.asyncio
async def test_usage_tracker_record_error(db: Database) -> None:
    tracker = UsageTracker(db)
    await tracker.record_error()

    error_rows = await db.execute_read(
        "SELECT period, value FROM metrics WHERE name = 'llm_errors' ORDER BY period"
    )
    assert len(error_rows) == 4
    for row in error_rows:
        assert row["value"] == 1

    calls_rows = await db.execute_read(
        "SELECT period, value FROM metrics WHERE name = 'llm_calls_total' ORDER BY period"
    )
    assert len(calls_rows) == 4
    for row in calls_rows:
        assert row["value"] == 1


@pytest.mark.asyncio
async def test_usage_tracker_failed_call_increments_both_metrics(db: Database) -> None:
    tracker = UsageTracker(db)
    await tracker.record_error()

    calls_rows = await db.execute_read(
        "SELECT value FROM metrics WHERE name = 'llm_calls_total' AND period = 'total'"
    )
    assert calls_rows[0]["value"] == 1

    error_rows = await db.execute_read(
        "SELECT value FROM metrics WHERE name = 'llm_errors' AND period = 'total'"
    )
    assert error_rows[0]["value"] == 1


@pytest.mark.asyncio
async def test_usage_tracker_budget_not_exceeded(db: Database) -> None:
    tracker = UsageTracker(db, budget=10000)
    assert not await tracker.is_budget_exceeded()


@pytest.mark.asyncio
async def test_usage_tracker_budget_exceeded(db: Database) -> None:
    tracker = UsageTracker(db, budget=10)
    await tracker.record_call(total_tokens=100)
    assert await tracker.is_budget_exceeded()


@pytest.mark.asyncio
async def test_llm_client_glm_primary() -> None:
    glm_provider = AsyncMock(spec=GLMProvider)
    glm_provider.call = AsyncMock(
        return_value=LLMResponse(content='{"category": "privacy"}', total_tokens=50)
    )
    qwen_provider = AsyncMock(spec=QwenProvider)
    usage = AsyncMock(spec=UsageTracker)
    usage.is_budget_exceeded = AsyncMock(return_value=False)
    usage.record_call = AsyncMock()
    usage.record_error = AsyncMock()

    client = LLMClient(glm_provider, qwen_provider, usage)
    result = await client.classify("system prompt", "user content")

    assert result is not None
    assert result.content == '{"category": "privacy"}'
    glm_provider.call.assert_called_once()
    qwen_provider.call.assert_not_called()
    usage.record_call.assert_called_once_with(50)


@pytest.mark.asyncio
async def test_llm_client_fallback_to_qwen() -> None:
    glm_provider = AsyncMock(spec=GLMProvider)
    glm_provider.call = AsyncMock(side_effect=httpx.ReadTimeout("timeout"))
    qwen_provider = AsyncMock(spec=QwenProvider)
    qwen_provider.call = AsyncMock(
        return_value=LLMResponse(content='{"category": "circumvention"}', total_tokens=60)
    )
    usage = AsyncMock(spec=UsageTracker)
    usage.is_budget_exceeded = AsyncMock(return_value=False)
    usage.record_call = AsyncMock()
    usage.record_error = AsyncMock()

    client = LLMClient(glm_provider, qwen_provider, usage)
    with patch("smm_autopilot.llm.client.asyncio.sleep", new_callable=AsyncMock):
        result = await client.classify("system prompt", "user content")

    assert result is not None
    assert result.content == '{"category": "circumvention"}'
    assert glm_provider.call.call_count == 3
    qwen_provider.call.assert_called_once()


@pytest.mark.asyncio
async def test_llm_client_both_providers_fail() -> None:
    glm_provider = AsyncMock(spec=GLMProvider)
    glm_provider.call = AsyncMock(side_effect=httpx.ReadTimeout("timeout"))
    qwen_provider = AsyncMock(spec=QwenProvider)
    qwen_provider.call = AsyncMock(side_effect=httpx.ReadTimeout("timeout"))
    usage = AsyncMock(spec=UsageTracker)
    usage.is_budget_exceeded = AsyncMock(return_value=False)
    usage.record_call = AsyncMock()
    usage.record_error = AsyncMock()

    client = LLMClient(glm_provider, qwen_provider, usage)
    with patch("smm_autopilot.llm.client.asyncio.sleep", new_callable=AsyncMock):
        result = await client.classify("system prompt", "user content")

    assert result is None
    assert glm_provider.call.call_count == 3
    assert qwen_provider.call.call_count == 3


@pytest.mark.asyncio
async def test_llm_client_budget_exceeded() -> None:
    glm_provider = AsyncMock(spec=GLMProvider)
    qwen_provider = AsyncMock(spec=QwenProvider)
    usage = AsyncMock(spec=UsageTracker)
    usage.is_budget_exceeded = AsyncMock(return_value=True)

    client = LLMClient(glm_provider, qwen_provider, usage)
    result = await client.classify("system prompt", "user content")

    assert result is None
    glm_provider.call.assert_not_called()
    qwen_provider.call.assert_not_called()


@pytest.mark.asyncio
async def test_usage_tracker_accumulate_tokens(db: Database) -> None:
    tracker = UsageTracker(db)
    await tracker.record_call(total_tokens=50)
    await tracker.record_call(total_tokens=30)

    rows = await db.execute_read(
        "SELECT value FROM metrics WHERE name = 'llm_tokens_total' AND period = 'total'"
    )
    assert rows[0]["value"] == 80

    call_rows = await db.execute_read(
        "SELECT value FROM metrics WHERE name = 'llm_calls_total' AND period = 'total'"
    )
    assert call_rows[0]["value"] == 2
