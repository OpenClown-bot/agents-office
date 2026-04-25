from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio

from smm_autopilot.config import AppConfig
from smm_autopilot.db import Database
from smm_autopilot.ingestion import FetchedItem
from smm_autopilot.ingestion import rss, telegram, web
from smm_autopilot.ingestion.service import SourceIngester, _extract_telegram_channel_username


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        db_path=tmp_path / "test.db",
        log_level="INFO",
        telegram_bot_token="test-bot-token",
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


SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Test Article</title>
      <link>https://example.com/article-1</link>
      <description>Article body text</description>
      <pubDate>Thu, 24 Apr 2026 12:00:00 GMT</pubDate>
      <guid>article-1</guid>
    </item>
    <item>
      <title>Second Article</title>
      <link>https://example.com/article-2</link>
      <description>Second body text</description>
      <pubDate>Thu, 24 Apr 2026 13:00:00 GMT</pubDate>
      <guid>article-2</guid>
      <enclosure url="https://example.com/image.jpg" type="image/jpeg" length="12345"/>
    </item>
  </channel>
</rss>"""


MALFORMED_RSS_XML = """<?xml version="1.0"?>
<rss><broken><no-items></no-items>"""


SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Test Page Title</title>
    <meta property="og:image" content="https://example.com/og-image.jpg"/>
</head>
<body>
    <article>
        <h1>Article Heading</h1>
        <p>This is the article body with some content.</p>
    </article>
</body>
</html>"""


class MockTransport(httpx.AsyncBaseTransport):
    def __init__(self, responses: dict[str, httpx.Response]) -> None:
        self._responses = responses

    async def handle_async_request(
        self, request: httpx.Request
    ) -> httpx.Response:
        url_str = str(request.url)
        for pattern, response in self._responses.items():
            if pattern in url_str:
                return response
        return httpx.Response(404)


def _make_client(responses: dict[str, httpx.Response]) -> httpx.AsyncClient:
    transport = MockTransport(responses)
    return httpx.AsyncClient(transport=transport)


def _mock_client_from_handler(
    handler: Any,
) -> httpx.AsyncClient:
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


@pytest.mark.asyncio
async def test_rss_fetch_success() -> None:
    responses = {
        "feed.example.com": httpx.Response(200, text=SAMPLE_RSS_XML),
    }
    async with _make_client(responses) as client:
        items = await rss.fetch(client, "https://feed.example.com/rss")
    assert len(items) == 2
    assert items[0].external_id == "article-1"
    assert items[0].title == "Test Article"
    assert items[0].body == "Article body text"
    assert items[0].url == "https://example.com/article-1"
    assert items[0].image_url is None
    assert items[1].image_url == "https://example.com/image.jpg"


@pytest.mark.asyncio
async def test_rss_fetch_http_500() -> None:
    responses = {
        "feed.example.com": httpx.Response(500, text="Internal Server Error"),
    }
    async with _make_client(responses) as client:
        items = await rss.fetch(client, "https://feed.example.com/rss")
    assert items == []


@pytest.mark.asyncio
async def test_rss_fetch_malformed_xml() -> None:
    responses = {
        "feed.example.com": httpx.Response(200, text=MALFORMED_RSS_XML),
    }
    async with _make_client(responses) as client:
        items = await rss.fetch(client, "https://feed.example.com/rss")
    assert items == []


@pytest.mark.asyncio
async def test_rss_fetch_http_error_exhausted() -> None:
    call_count = 0

    class FailTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(
            self, request: httpx.Request
        ) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(503, text="Service Unavailable")

    async with httpx.AsyncClient(transport=FailTransport()) as client:
        items = await rss.fetch(client, "https://feed.example.com/rss")
    assert items == []
    assert call_count == 3


@pytest.mark.asyncio
async def test_web_fetch_success() -> None:
    responses = {
        "example.com": httpx.Response(200, text=SAMPLE_HTML),
    }
    async with _make_client(responses) as client:
        items = await web.fetch(client, "https://example.com/page")
    assert len(items) == 1
    assert items[0].title == "Article Heading"
    assert "article body" in items[0].body
    assert items[0].url == "https://example.com/page"
    assert items[0].image_url == "https://example.com/og-image.jpg"
    assert items[0].published_at is None


@pytest.mark.asyncio
async def test_web_fetch_http_500() -> None:
    responses = {
        "example.com": httpx.Response(500, text="Error"),
    }
    async with _make_client(responses) as client:
        items = await web.fetch(client, "https://example.com/page")
    assert items == []


@pytest.mark.asyncio
async def test_telegram_fetch_success() -> None:
    tg_response = {
        "ok": True,
        "result": [
            {
                "update_id": 100,
                "channel_post": {
                    "message_id": 42,
                    "chat": {"username": "testchannel"},
                    "text": "Test channel message",
                    "date": 1745496000,
                },
            },
            {
                "update_id": 101,
                "channel_post": {
                    "message_id": 43,
                    "chat": {"username": "testchannel"},
                    "text": "Second message",
                    "date": 1745496060,
                },
            },
        ],
    }

    responses = {
        "api.telegram.org": httpx.Response(200, text=json.dumps(tg_response)),
    }
    async with _make_client(responses) as client:
        items = await telegram.fetch(client, "test-bot-token", "testchannel")
    assert len(items) == 2
    assert items[0].external_id == "42"
    assert items[0].body == "Test channel message"
    assert items[0].url == "https://t.me/testchannel/42"
    assert items[0].title is None


@pytest.mark.asyncio
async def test_telegram_fetch_api_error() -> None:
    tg_response = {"ok": False, "description": "Unauthorized"}

    responses = {
        "api.telegram.org": httpx.Response(200, text=json.dumps(tg_response)),
    }
    async with _make_client(responses) as client:
        items = await telegram.fetch(client, "bad-token", "testchannel")
    assert items == []


@pytest.mark.asyncio
async def test_telegram_fetch_http_500() -> None:
    responses = {
        "api.telegram.org": httpx.Response(500, text="Error"),
    }
    async with _make_client(responses) as client:
        items = await telegram.fetch(client, "test-bot-token", "testchannel")
    assert items == []


async def _seed_source(
    db: Database,
    source_type: str = "rss",
    url: str = "https://feed.example.com/rss",
) -> int:
    now = datetime.now(tz=timezone.utc).isoformat()
    await db.execute_write(
        "INSERT INTO source (type, url, name, is_active, added_by, created_at, updated_at) "
        "VALUES (?, ?, ?, 1, 'po_manual', ?, ?)",
        (source_type, url, "Test Source", now, now),
    )
    rows = await db.execute_read("SELECT last_insert_rowid() as id")
    return rows[0]["id"]


@pytest.mark.asyncio
async def test_service_rss_persist_raw_item(db: Database) -> None:
    source_id = await _seed_source(db, "rss", "https://feed.example.com/rss")
    ingester = SourceIngester(db, bot_token="test-token")

    async with _make_client(
        {"feed.example.com": httpx.Response(200, text=SAMPLE_RSS_XML)}
    ) as client:
        fetched = await rss.fetch(client, "https://feed.example.com/rss")
        for item in fetched:
            await ingester._persist_item(source_id, item)

    rows = await db.execute_read(
        "SELECT source_id, external_id, title, body, url, published_at, status FROM raw_item"
    )
    assert len(rows) == 2
    assert rows[0]["source_id"] == source_id
    assert rows[0]["external_id"] == "article-1"
    assert rows[0]["title"] == "Test Article"
    assert rows[0]["body"] == "Article body text"
    assert rows[0]["url"] == "https://example.com/article-1"
    assert rows[0]["status"] == "pending"
    assert rows[0]["published_at"] is not None
    assert rows[0]["published_at"].startswith("2026-04-24T12:00:00+00:00")


@pytest.mark.asyncio
async def test_service_duplicate_skipped(db: Database) -> None:
    source_id = await _seed_source(db, "rss", "https://feed.example.com/rss")
    ingester = SourceIngester(db, bot_token="test-token")

    item = FetchedItem(
        external_id="dup-1",
        title="Title",
        body="Body",
        url="https://example.com/dup",
        image_url=None,
        published_at=None,
    )
    await ingester._persist_item(source_id, item)
    await ingester._persist_item(source_id, item)

    rows = await db.execute_read("SELECT COUNT(*) as cnt FROM raw_item")
    assert rows[0]["cnt"] == 1


@pytest.mark.asyncio
async def test_service_metrics_incremented(db: Database) -> None:
    source_id = await _seed_source(db, "rss", "https://feed.example.com/rss")
    ingester = SourceIngester(db, bot_token="test-token")

    item = FetchedItem(
        external_id="metrics-1",
        title="Title",
        body="Body",
        url="https://example.com/metrics",
        image_url=None,
        published_at=None,
    )
    await ingester._persist_item(source_id, item)

    rows = await db.execute_read(
        "SELECT period, value FROM metrics WHERE name = 'items_ingested' ORDER BY period"
    )
    assert len(rows) == 4
    for row in rows:
        assert row["value"] == 1


@pytest.mark.asyncio
async def test_service_metrics_accumulate(db: Database) -> None:
    source_id = await _seed_source(db, "rss", "https://feed.example.com/rss")
    ingester = SourceIngester(db, bot_token="test-token")

    for i in range(3):
        item = FetchedItem(
            external_id=f"acc-{i}",
            title=f"Title {i}",
            body=f"Body {i}",
            url=f"https://example.com/acc-{i}",
            image_url=None,
            published_at=None,
        )
        await ingester._persist_item(source_id, item)

    rows = await db.execute_read(
        "SELECT period, value FROM metrics WHERE name = 'items_ingested' AND period = 'total'"
    )
    assert len(rows) == 1
    assert rows[0]["value"] == 3


@pytest.mark.asyncio
async def test_service_http_500_source_skipped(db: Database) -> None:
    call_count = 0

    class FailTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(
            self, request: httpx.Request
        ) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(500, text="Internal Server Error")

    async with httpx.AsyncClient(transport=FailTransport()) as client:
        items = await rss.fetch(client, "https://feed.example.com/rss")
    assert items == []

    rows = await db.execute_read("SELECT COUNT(*) as cnt FROM raw_item")
    assert rows[0]["cnt"] == 0


@pytest.mark.asyncio
async def test_service_run_once_no_active_sources(db: Database) -> None:
    ingester = SourceIngester(db, bot_token="test-token")
    await ingester.run_once()

    rows = await db.execute_read("SELECT COUNT(*) as cnt FROM raw_item")
    assert rows[0]["cnt"] == 0


@pytest.mark.asyncio
async def test_service_run_once_rss(db: Database) -> None:
    await _seed_source(db, "rss", "https://feed.example.com/rss")
    ingester = SourceIngester(db, bot_token="test-token")

    _original_async_client = httpx.AsyncClient
    rss_responses = {
        "feed.example.com": httpx.Response(200, text=SAMPLE_RSS_XML),
    }

    def client_factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        transport = MockTransport(rss_responses)
        return _original_async_client(transport=transport)

    with patch.object(httpx, "AsyncClient", client_factory):
        await ingester.run_once()

    rows = await db.execute_read(
        "SELECT source_id, external_id, title, body, url, published_at, status FROM raw_item"
    )
    assert len(rows) == 2
    assert rows[0]["title"] == "Test Article"
    assert rows[0]["body"] == "Article body text"
    assert rows[0]["url"] == "https://example.com/article-1"
    assert rows[0]["status"] == "pending"
    assert rows[0]["published_at"] is not None
    assert rows[0]["published_at"].startswith("2026-04-24")

    m_rows = await db.execute_read(
        "SELECT value FROM metrics WHERE name='items_ingested' AND period='total'"
    )
    assert m_rows[0]["value"] >= 2


@pytest.mark.asyncio
async def test_service_run_once_web(db: Database) -> None:
    await _seed_source(db, "web_page", "https://example.com/page")
    ingester = SourceIngester(db, bot_token="test-token")

    _original_async_client = httpx.AsyncClient
    web_responses = {
        "example.com": httpx.Response(200, text=SAMPLE_HTML),
    }

    def client_factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        transport = MockTransport(web_responses)
        return _original_async_client(transport=transport)

    with patch.object(httpx, "AsyncClient", client_factory):
        await ingester.run_once()

    rows = await db.execute_read(
        "SELECT source_id, external_id, title, body, url, published_at, status FROM raw_item"
    )
    assert len(rows) == 1
    assert rows[0]["title"] == "Article Heading"
    assert "article body" in rows[0]["body"]
    assert rows[0]["url"] == "https://example.com/page"
    assert rows[0]["status"] == "pending"
    assert rows[0]["published_at"] is None

    m_rows = await db.execute_read(
        "SELECT value FROM metrics WHERE name='items_ingested' AND period='total'"
    )
    assert m_rows[0]["value"] >= 1


@pytest.mark.asyncio
async def test_service_run_once_telegram(db: Database) -> None:
    await _seed_source(db, "telegram_channel", "https://t.me/devin_test_chan")
    ingester = SourceIngester(db, bot_token="test-token")

    tg_response = {
        "ok": True,
        "result": [
            {
                "update_id": 1001,
                "channel_post": {
                    "message_id": 5,
                    "date": 1714000000,
                    "text": "Hello from devin_test_chan",
                    "chat": {
                        "id": -100,
                        "username": "devin_test_chan",
                        "type": "channel",
                    },
                },
            },
            {
                "update_id": 1002,
                "channel_post": {
                    "message_id": 6,
                    "date": 1714000100,
                    "text": "Hello from other_channel",
                    "chat": {
                        "id": -101,
                        "username": "other_channel",
                        "type": "channel",
                    },
                },
            },
        ],
    }

    _original_async_client = httpx.AsyncClient
    tg_responses = {
        "api.telegram.org": httpx.Response(200, text=json.dumps(tg_response)),
    }

    def client_factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        transport = MockTransport(tg_responses)
        return _original_async_client(transport=transport)

    with patch.object(httpx, "AsyncClient", client_factory):
        await ingester.run_once()

    rows = await db.execute_read(
        "SELECT source_id, external_id, title, body, url, published_at, status FROM raw_item"
    )
    assert len(rows) == 1
    assert rows[0]["external_id"] == "5"
    assert rows[0]["body"] == "Hello from devin_test_chan"
    assert rows[0]["url"] == "https://t.me/devin_test_chan/5"
    assert rows[0]["title"] is None
    assert rows[0]["published_at"] is not None
    assert rows[0]["published_at"].startswith("2024-04-24")

    m_rows = await db.execute_read(
        "SELECT value FROM metrics WHERE name='items_ingested' AND period='total'"
    )
    assert m_rows[0]["value"] >= 1


@pytest.mark.asyncio
async def test_service_unknown_source_type_skipped(db: Database) -> None:
    original_read = db.execute_read

    async def mock_read(
        sql: str, params: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        if "FROM source" in sql.upper().replace("\n", " "):
            return [
                {
                    "id": 999,
                    "type": "invalid_type",
                    "url": "https://invalid.example.com",
                    "name": "Invalid",
                }
            ]
        return await original_read(sql, params)

    with patch.object(db, "execute_read", side_effect=mock_read):
        ingester = SourceIngester(db, bot_token="test-token")
        await ingester.run_once()

    rows = await original_read("SELECT COUNT(*) as cnt FROM raw_item")
    assert rows[0]["cnt"] == 0


@pytest.mark.asyncio
async def test_rss_entry_without_id_uses_link() -> None:
    xml_no_id = """<?xml version="1.0"?>
<rss version="2.0"><channel><item>
  <title>No ID Article</title>
  <link>https://example.com/no-id</link>
  <description>Body text</description>
</item></channel></rss>"""
    responses = {
        "feed.example.com": httpx.Response(200, text=xml_no_id),
    }
    async with _make_client(responses) as client:
        items = await rss.fetch(client, "https://feed.example.com/rss")
    assert len(items) == 1
    assert items[0].external_id == "https://example.com/no-id"


@pytest.mark.asyncio
async def test_rss_entry_no_id_no_link_skipped() -> None:
    xml_no_id = """<?xml version="1.0"?>
<rss version="2.0"><channel><item>
  <title>No ID Article</title>
  <description>Body text</description>
</item></channel></rss>"""
    responses = {
        "feed.example.com": httpx.Response(200, text=xml_no_id),
    }
    async with _make_client(responses) as client:
        items = await rss.fetch(client, "https://feed.example.com/rss")
    assert len(items) == 0


@pytest.mark.asyncio
async def test_telegram_message_no_text_skipped() -> None:
    tg_response = {
        "ok": True,
        "result": [
            {
                "update_id": 200,
                "channel_post": {
                    "message_id": 99,
                    "chat": {"username": "testchannel"},
                    "date": 1745496000,
                },
            },
        ],
    }

    responses = {
        "api.telegram.org": httpx.Response(200, text=json.dumps(tg_response)),
    }
    async with _make_client(responses) as client:
        items = await telegram.fetch(client, "test-bot-token", "testchannel")
    assert items == []


@pytest.mark.asyncio
async def test_web_fetch_empty_body() -> None:
    empty_html = "<html><body></body></html>"
    responses = {
        "example.com": httpx.Response(200, text=empty_html),
    }
    async with _make_client(responses) as client:
        items = await web.fetch(client, "https://example.com/empty")
    assert items == []


@pytest.mark.asyncio
async def test_service_duplicate_unique_constraint(db: Database) -> None:
    source_id = await _seed_source(db, "rss", "https://feed.example.com/rss")
    now = datetime.now(tz=timezone.utc).isoformat()

    await db.execute_write(
        "INSERT INTO raw_item (source_id, external_id, title, body, url, ingested_at, status) "
        "VALUES (?, ?, ?, ?, ?, ?, 'pending')",
        (source_id, "existing-1", "Old Title", "Old Body", "https://example.com/old", now),
    )

    ingester = SourceIngester(db, bot_token="test-token")
    item = FetchedItem(
        external_id="existing-1",
        title="New Title",
        body="New Body",
        url="https://example.com/new",
        image_url=None,
        published_at=None,
    )
    await ingester._persist_item(source_id, item)

    rows = await db.execute_read("SELECT title, body FROM raw_item WHERE external_id = 'existing-1'")
    assert len(rows) == 1
    assert rows[0]["title"] == "Old Title"


@pytest.mark.asyncio
async def test_telegram_fetch_filters_by_channel() -> None:
    tg_response = {
        "ok": True,
        "result": [
            {
                "update_id": 300,
                "channel_post": {
                    "message_id": 50,
                    "chat": {"username": "targetchannel"},
                    "text": "Target channel message",
                    "date": 1745496000,
                },
            },
            {
                "update_id": 301,
                "channel_post": {
                    "message_id": 60,
                    "chat": {"username": "otherchannel"},
                    "text": "Other channel message",
                    "date": 1745496060,
                },
            },
            {
                "update_id": 302,
                "message": {
                    "message_id": 70,
                    "chat": {"type": "private"},
                    "text": "Private chat message",
                    "date": 1745496120,
                },
            },
        ],
    }

    responses = {
        "api.telegram.org": httpx.Response(200, text=json.dumps(tg_response)),
    }
    async with _make_client(responses) as client:
        items = await telegram.fetch(client, "test-bot-token", "targetchannel")
    assert len(items) == 1
    assert items[0].body == "Target channel message"
    assert items[0].external_id == "50"


@pytest.mark.parametrize(
    "input_url,expected",
    [
        ("https://t.me/channelname", "channelname"),
        ("https://t.me/channelname/", "channelname"),
        ("t.me/channelname/123", "channelname"),
        ("@channelname", "channelname"),
        ("channelname", "channelname"),
    ],
)
def test_extract_telegram_channel_username(input_url: str, expected: str) -> None:
    assert _extract_telegram_channel_username(input_url) == expected
