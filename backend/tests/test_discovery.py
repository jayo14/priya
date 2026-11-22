"""Comprehensive unit and integration tests for Phase 2 Discovery Infrastructure."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.enums import SourceType
from app.database.models.source import Source
from app.database.repositories.source_repo import SourceRepository
from app.discovery.base import (
    RawDiscoveredItem,
    compute_content_hash,
)
from app.discovery.orchestrator import DiscoveryOrchestrator
from app.discovery.reddit import RedditCollector, clean_subreddit_name
from app.discovery.scheduler import DiscoveryScheduler
from app.discovery.telegram import TelegramCollector, clean_channel_username
from app.discovery.web import RssCollector, WebPageCollector


def test_content_hash_normalization():
    """Verify that compute_content_hash normalizes whitespace and casing."""
    text1 = "Claude Pro   promotion for 3 months free!"
    text2 = "claude pro promotion for 3 months free!  "
    text3 = "Different text entirely"

    hash1 = compute_content_hash(text1)
    hash2 = compute_content_hash(text2)
    hash3 = compute_content_hash(text3)

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64  # SHA-256 length


def test_raw_discovered_item_properties():
    """Verify RawDiscoveredItem computes content_hash from title and content."""
    item = RawDiscoveredItem(
        external_id="ext_123",
        title="OpenAI Deal",
        content="Free ChatGPT Plus for Students",
    )
    expected_hash = compute_content_hash("OpenAI Deal Free ChatGPT Plus for Students")
    assert item.content_hash == expected_hash


def test_clean_identifiers():
    """Verify normalization helpers for subreddit and telegram channel names."""
    assert clean_subreddit_name("r/ClaudeAI") == "ClaudeAI"
    assert clean_subreddit_name("/r/ChatGPT/") == "ChatGPT"
    assert clean_subreddit_name("https://www.reddit.com/r/Grok/") == "Grok"

    assert clean_channel_username("@ai_deals") == "ai_deals"
    assert clean_channel_username("https://t.me/s/free_promos") == "free_promos"
    assert clean_channel_username("https://t.me/my_channel/123") == "my_channel"


@pytest.mark.asyncio
async def test_rss_collector_success():
    """Verify RssCollector successfully parses RSS feeds into RawDiscoveredItems."""
    sample_rss = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>AI News</title>
            <link>https://example.com</link>
            <item>
                <guid>item-101</guid>
                <title>Claude 3.5 Sonnet Promo</title>
                <link>https://example.com/promo1</link>
                <description>&lt;p&gt;Get Claude Pro discounted today.&lt;/p&gt;</description>
                <author>editorial@example.com</author>
            </item>
        </channel>
    </rss>
    """
    source = Source(
        id=1,
        name="Test RSS Source",
        source_type=SourceType.RSS,
        identifier="https://example.com/rss",
        url="https://example.com/rss",
    )

    collector = RssCollector()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = sample_rss
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await collector.collect(source)

        assert result.success is True
        assert len(result.items) == 1
        item = result.items[0]
        assert item.external_id == "item-101"
        assert item.title == "Claude 3.5 Sonnet Promo"
        assert "Get Claude Pro discounted today." in item.content
        assert item.original_url == "https://example.com/promo1"


@pytest.mark.asyncio
async def test_web_page_collector_success():
    """Verify WebPageCollector extracts title, clean text, and outbound links."""
    sample_html = """<!DOCTYPE html>
    <html>
        <head><title>Anthropic Announcements</title></head>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Claude Pro Free Trial</h1>
                <p>Anthropic is partnering with universities to offer 6 months free Claude Pro.</p>
                <a href="https://claude.ai/claim">Claim Here</a>
            </article>
            <footer>Footer</footer>
        </body>
    </html>
    """
    source = Source(
        id=2,
        name="Anthropic News",
        source_type=SourceType.WEBSITE,
        identifier="https://anthropic.com/news",
        url="https://anthropic.com/news",
    )

    collector = WebPageCollector()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await collector.collect(source)

        assert result.success is True
        assert len(result.items) == 1
        item = result.items[0]
        assert item.title == "Anthropic Announcements"
        assert "Claude Pro Free Trial" in item.content
        assert "Navigation" not in item.content  # <nav> stripped
        assert "https://claude.ai/claim" in item.raw_metadata["extracted_links"]


@pytest.mark.asyncio
async def test_telegram_collector_html_parsing():
    """Verify TelegramCollector parses public web preview messages, links, and dates."""
    sample_tg_html = """
    <div class="tgme_widget_message_wrap">
        <div class="tgme_widget_message" data-post="deal_channel/456">
            <div class="tgme_widget_message_text">
                Special Offer: Get 3 Months ChatGPT Plus free with code SUMMERAI
                <br>
                <a href="https://chatgpt.com/redeem?code=SUMMERAI">Redeem Link</a>
            </div>
            <time datetime="2026-11-20T10:00:00+00:00">Nov 20, 2026</time>
            <span class="tgme_widget_message_views">1.2K</span>
        </div>
    </div>
    """
    source = Source(
        id=3,
        name="Telegram Deals",
        source_type=SourceType.TELEGRAM,
        identifier="@deal_channel",
        url="https://t.me/s/deal_channel",
    )

    collector = TelegramCollector()
    result = collector.parse_html_preview(source.id, "deal_channel", sample_tg_html)

    assert result.success is True
    assert len(result.items) == 1
    item = result.items[0]
    assert item.external_id == "tg_deal_channel_456"
    assert "ChatGPT Plus free" in item.content
    assert item.original_url == "https://t.me/deal_channel/456"
    assert "https://chatgpt.com/redeem?code=SUMMERAI" in item.raw_metadata["extracted_links"]
    assert item.raw_metadata["views"] == "1.2K"


@pytest.mark.asyncio
async def test_reddit_collector_json_parsing():
    """Verify RedditCollector parses public JSON listing into RawDiscoveredItems."""
    sample_reddit_json = {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "abc1234",
                        "name": "t3_abc1234",
                        "title": "Perplexity Pro free for 1 year student promo",
                        "selftext": "Verified working student link with GitHub Student Pack.",
                        "author": "student_user",
                        "permalink": "/r/PerplexityAI/comments/abc1234/perplexity_pro_free/",
                        "url": "https://perplexity.ai/student",
                        "created_utc": 1700000000,
                        "score": 42,
                        "num_comments": 15,
                        "subreddit": "PerplexityAI",
                    }
                }
            ]
        }
    }
    source = Source(
        id=4,
        name="Reddit Perplexity",
        source_type=SourceType.REDDIT,
        identifier="r/PerplexityAI",
    )

    collector = RedditCollector()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_reddit_json
        mock_get.return_value = mock_response

        result = await collector.collect(source)

        assert result.success is True
        assert len(result.items) == 1
        item = result.items[0]
        assert item.external_id == "reddit_t3_abc1234"
        assert item.title == "Perplexity Pro free for 1 year student promo"
        assert item.author == "student_user"
        assert "Verified working" in item.content


@pytest.mark.asyncio
async def test_orchestrator_persistence_and_duplicate_prevention(db_session: Session):
    """Verify DiscoveryOrchestrator ingests items, updates source metadata, and skips duplicates."""
    source = SourceRepository.create(
        db=db_session,
        name="Test Ingestion Channel",
        source_type=SourceType.TELEGRAM,
        identifier="@test_ingestion_channel",
    )

    orchestrator = DiscoveryOrchestrator()

    # Mock collector returning two items
    mock_collector = MagicMock()
    mock_collector.collect = AsyncMock(
        return_value=MagicMock(
            source_id=source.id,
            success=True,
            items=[
                RawDiscoveredItem(
                    external_id="tg_test_1",
                    title="Grok Subscription Discount",
                    content="Grok SuperGrok 50% discount for annual subscribers",
                ),
                RawDiscoveredItem(
                    external_id="tg_test_2",
                    title="Cursor Pro Trial",
                    content="New 14-day free trial on Cursor Pro",
                ),
            ],
            error_message=None,
        )
    )

    orchestrator._collectors[SourceType.TELEGRAM] = mock_collector

    # First run: should persist 2 items
    res1 = await orchestrator.collect_source(db_session, source)
    assert res1.success is True
    assert source.last_collected_at is not None
    assert source.last_successful_collection_at is not None
    assert source.last_error_message is None

    # Verify items are in DB
    assert len(source.discovered_items) == 2

    # Second run with same items: duplicates should be safely skipped without error
    res2 = await orchestrator.collect_source(db_session, source)
    assert res2.success is True
    # Still 2 items in database
    assert len(source.discovered_items) == 2


def test_scheduler_is_source_due():
    """Verify scheduler correctly evaluates if a source is due for collection."""
    scheduler = DiscoveryScheduler()
    now = datetime(2026, 11, 22, 12, 0, 0, tzinfo=timezone.utc)

    # Inactive source: never due
    inactive_src = Source(is_active=False)
    assert scheduler.is_source_due(inactive_src, now) is False

    # Source never collected: always due
    new_src = Source(is_active=True, last_collected_at=None)
    assert scheduler.is_source_due(new_src, now) is True

    # Source collected 100s ago, interval 300s: not due
    recent_src = Source(
        is_active=True,
        collection_interval_seconds=300,
        last_collected_at=datetime(2026, 11, 22, 11, 59, 0, tzinfo=timezone.utc),  # 60s ago
    )
    assert scheduler.is_source_due(recent_src, now) is False

    # Source collected 400s ago, interval 300s: is due
    due_src = Source(
        is_active=True,
        collection_interval_seconds=300,
        last_collected_at=datetime(2026, 11, 22, 11, 50, 0, tzinfo=timezone.utc),  # 600s ago
    )
    assert scheduler.is_source_due(due_src, now) is True


def test_sources_api_endpoints(client: TestClient, db_session: Session):
    """Test API endpoints for listing sources, creating sources, and querying discovered items."""
    # 1. List sources
    resp = client.get("/api/v1/sources")
    assert resp.status_code == 200
    sources_data = resp.json()
    assert isinstance(sources_data, list)
    assert len(sources_data) >= 1  # From seeded curated sources

    # 2. Create new source
    create_payload = {
        "name": "API Created RSS Feed",
        "source_type": "rss",
        "identifier": "https://custom-deal-blog.com/feed.xml",
        "url": "https://custom-deal-blog.com/feed.xml",
        "description": "User created feed",
        "collection_interval_seconds": 600,
    }
    create_resp = client.post("/api/v1/sources", json=create_payload)
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]

    # 3. Retrieve single source
    get_resp = client.get(f"/api/v1/sources/{created_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "API Created RSS Feed"

    # 4. Duplicate identifier creation should return 409 Conflict
    dup_resp = client.post("/api/v1/sources", json=create_payload)
    assert dup_resp.status_code == 409

    # 5. Query discovered items endpoint
    items_resp = client.get("/api/v1/discovery/items")
    assert items_resp.status_code == 200
    assert isinstance(items_resp.json(), list)
