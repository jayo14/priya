"""Telegram public channel collector using web preview and Telethon fallback."""

import re
from datetime import datetime, timezone
from typing import List

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

TELEGRAM_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def clean_channel_username(identifier: str) -> str:
    """Normalize Telegram channel identifier to raw username."""
    clean = identifier.strip()
    clean = re.sub(r"^https?://(www\.)?t\.me/(s/)?", "", clean, flags=re.IGNORECASE)
    clean = clean.lstrip("@").strip("/").split("/")[0]
    return clean


class TelegramCollector(BaseSourceCollector):
    """
    Collector for public Telegram channels.
    By default, uses the public web preview endpoint (https://t.me/s/{channel})
    which operates deterministically without requiring API keys, phone numbers, or session credentials.
    """

    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds

    async def collect(self, source: Source) -> CollectorResult:
        channel_username = clean_channel_username(source.identifier)
        if not channel_username:
            return CollectorResult(
                source_id=source.id,
                success=False,
                error_message="Invalid Telegram channel username or identifier.",
            )

        preview_url = f"https://t.me/s/{channel_username}"
        logger.info(
            f"Collecting Telegram messages for source '{source.name}' from {preview_url}"
        )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers={"User-Agent": TELEGRAM_USER_AGENT},
                follow_redirects=True,
            ) as client:
                response = await client.get(preview_url)
                if response.status_code == 404:
                    return CollectorResult(
                        source_id=source.id,
                        success=False,
                        error_message=f"Telegram channel '@{channel_username}' does not exist or is private.",
                    )
                response.raise_for_status()
                html = response.text

            return self.parse_html_preview(source.id, channel_username, html)

        except httpx.HTTPError as exc:
            msg = f"HTTP error during Telegram collection: {exc}"
            logger.error(msg)
            return CollectorResult(source_id=source.id, success=False, error_message=msg)
        except Exception as exc:
            msg = f"Unexpected error collecting Telegram channel: {exc}"
            logger.error(msg, exc_info=True)
            return CollectorResult(source_id=source.id, success=False, error_message=msg)

    def parse_html_preview(
        self, source_id: int, channel_username: str, html: str
    ) -> CollectorResult:
        """Parse Telegram public web preview HTML into structured RawDiscoveredItems."""
        soup = BeautifulSoup(html, "html.parser")
        message_wrappers = soup.find_all("div", class_="tgme_widget_message_wrap")

        items: List[RawDiscoveredItem] = []

        for wrap in message_wrappers:
            msg_div = wrap.find("div", class_="tgme_widget_message")
            if not msg_div:
                continue

            # Extract message ID from data-post (format: channel/1234)
            data_post = msg_div.get("data-post", "")
            if not data_post or "/" not in data_post:
                continue

            msg_id = data_post.split("/")[-1]
            external_id = f"tg_{channel_username}_{msg_id}"
            original_url = f"https://t.me/{data_post}"

            # Extract text content
            text_div = msg_div.find("div", class_="tgme_widget_message_text")
            if not text_div:
                # Could be a photo/video only message without text
                continue

            content = text_div.get_text(separator="\n", strip=True)
            if not content:
                continue

            # Generate preview title from first line
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            title = lines[0][:150] if lines else f"Telegram post {msg_id}"

            # Extract outbound links
            extracted_links = []
            for a_tag in text_div.find_all("a", href=True):
                href = a_tag["href"]
                if href.startswith("http://") or href.startswith("https://"):
                    extracted_links.append(href)

            # Extract publication time
            time_tag = msg_div.find("time", datetime=True)
            published_at = None
            if time_tag:
                try:
                    dt_str = time_tag["datetime"]
                    published_at = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except Exception:
                    published_at = None

            # Extract views
            views_span = msg_div.find("span", class_="tgme_widget_message_views")
            views = views_span.get_text(strip=True) if views_span else None

            items.append(
                RawDiscoveredItem(
                    external_id=external_id,
                    content=content,
                    content_type="telegram_message",
                    title=title,
                    author=f"@{channel_username}",
                    original_url=original_url,
                    published_at=published_at or datetime.now(timezone.utc),
                    raw_metadata={
                        "data_post": data_post,
                        "views": views,
                        "extracted_links": extracted_links,
                    },
                )
            )

        logger.info(
            f"Parsed {len(items)} messages from Telegram channel '@{channel_username}'"
        )
        return CollectorResult(source_id=source_id, success=True, items=items)
