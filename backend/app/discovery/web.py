"""RSS and Web Page collectors for public feeds and announcements."""

import time
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.core.logging import setup_logging
from app.database.models.source import Source
from app.discovery.base import (
    BaseSourceCollector,
    CollectorResult,
    RawDiscoveredItem,
)

logger = setup_logging()

DEFAULT_USER_AGENT = "Priya-Scout/0.1 (+https://github.com/jayo14/priya; personal deal monitor)"


def parse_parsed_time(time_struct: Optional[time.struct_time]) -> Optional[datetime]:
    """Convert feedparser struct_time to a timezone-aware UTC datetime."""
    if not time_struct:
        return None
    try:
        ts = time.mktime(time_struct)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        return None


class RssCollector(BaseSourceCollector):
    """Collector for RSS and Atom feeds (e.g. OpenAI blog, Google updates, Reddit RSS)."""

    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds

    async def collect(self, source: Source) -> CollectorResult:
        feed_url = source.url or source.identifier
        if not feed_url:
            return CollectorResult(
                source_id=source.id,
                success=False,
                error_message="Source has no valid URL or identifier for RSS collection.",
            )

        logger.info(f"Collecting RSS feed for source '{source.name}' from {feed_url}")
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers={"User-Agent": DEFAULT_USER_AGENT},
                follow_redirects=True,
            ) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
                content_bytes = response.content

            # Parse with feedparser
            feed = feedparser.parse(content_bytes)

            if feed.bozo and not feed.entries:
                bozo_msg = getattr(feed, "bozo_exception", "Unknown feed parsing error")
                logger.warning(f"Feed '{source.name}' parsing warning: {bozo_msg}")
                return CollectorResult(
                    source_id=source.id,
                    success=False,
                    error_message=f"Failed to parse RSS feed: {bozo_msg}",
                )

            items: list[RawDiscoveredItem] = []
            for entry in feed.entries:
                external_id = (
                    entry.get("id")
                    or entry.get("link")
                    or f"{source.identifier}_{entry.get('title', '')}"
                )

                # Extract content
                content = ""
                if "content" in entry and entry["content"]:
                    content = entry["content"][0].get("value", "")
                if not content:
                    content = entry.get("summary") or entry.get("description") or ""

                # Strip HTML tags for clean text content if present
                if "<" in content and ">" in content:
                    soup = BeautifulSoup(content, "html.parser")
                    clean_content = soup.get_text(separator=" ", strip=True)
                else:
                    clean_content = content.strip()

                title = entry.get("title", "").strip() or None
                original_url = entry.get("link")
                author = entry.get("author")
                published_at = parse_parsed_time(
                    entry.get("published_parsed") or entry.get("updated_parsed")
                )

                items.append(
                    RawDiscoveredItem(
                        external_id=external_id,
                        content=clean_content or (title or "No content"),
                        content_type="rss_item",
                        title=title,
                        author=author,
                        original_url=original_url,
                        published_at=published_at,
                        raw_metadata={
                            "feed_title": feed.feed.get("title"),
                            "feed_link": feed.feed.get("link"),
                            "tags": [t.get("term") for t in entry.get("tags", []) if t.get("term")],
                        },
                    )
                )

            logger.info(f"Collected {len(items)} items from RSS source '{source.name}'")
            return CollectorResult(
                source_id=source.id,
                success=True,
                items=items,
            )

        except httpx.HTTPError as exc:
            msg = f"HTTP error during RSS collection: {exc}"
            logger.error(msg)
            return CollectorResult(source_id=source.id, success=False, error_message=msg)
        except Exception as exc:
            msg = f"Unexpected error collecting RSS feed: {exc}"
            logger.error(msg, exc_info=True)
            return CollectorResult(source_id=source.id, success=False, error_message=msg)


class WebPageCollector(BaseSourceCollector):
    """Collector for public web announcement pages and deal sites."""

    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds

    async def collect(self, source: Source) -> CollectorResult:
        page_url = source.url or source.identifier
        if not page_url:
            return CollectorResult(
                source_id=source.id,
                success=False,
                error_message="Source has no valid URL or identifier for web collection.",
            )

        logger.info(f"Collecting web page for source '{source.name}' from {page_url}")
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers={"User-Agent": DEFAULT_USER_AGENT},
                follow_redirects=True,
            ) as client:
                response = await client.get(page_url)
                response.raise_for_status()
                html = response.text

            soup = BeautifulSoup(html, "html.parser")

            # Remove noisy elements
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else source.name

            # Look for article or main content container
            article = soup.find("article") or soup.find("main") or soup.body
            text_content = article.get_text(separator="\n", strip=True) if article else ""

            # Extract outbound links
            extracted_links = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.startswith("http://") or href.startswith("https://"):
                    extracted_links.append(href)

            item = RawDiscoveredItem(
                external_id=page_url,
                content=text_content[:20000],  # Bound length
                content_type="web_page",
                title=title,
                original_url=page_url,
                published_at=datetime.now(timezone.utc),
                raw_metadata={
                    "status_code": response.status_code,
                    "extracted_links_count": len(extracted_links),
                    "extracted_links": extracted_links[:50],
                },
            )

            logger.info(f"Collected web page from '{source.name}' ({len(text_content)} chars)")
            return CollectorResult(
                source_id=source.id,
                success=True,
                items=[item],
            )

        except httpx.HTTPError as exc:
            msg = f"HTTP error during web collection: {exc}"
            logger.error(msg)
            return CollectorResult(source_id=source.id, success=False, error_message=msg)
        except Exception as exc:
            msg = f"Unexpected error collecting web page: {exc}"
            logger.error(msg, exc_info=True)
            return CollectorResult(source_id=source.id, success=False, error_message=msg)
