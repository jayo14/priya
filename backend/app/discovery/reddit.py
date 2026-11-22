"""Reddit community and search collector using public endpoints."""

import re
from datetime import datetime, timezone

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

REDDIT_USER_AGENT = "Priya-Scout/0.1 (by /u/priya_deal_scout; personal deal finder)"


def clean_subreddit_name(identifier: str) -> str:
    """Normalize subreddit identifier to clean name without r/ or url prefixes."""
    clean = identifier.strip()
    clean = re.sub(r"^https?://(www\.)?reddit\.com/r/", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^/?r/", "", clean, flags=re.IGNORECASE)
    return clean.strip("/").split("/")[0]


class RedditCollector(BaseSourceCollector):
    """
    Collector for public Reddit subreddits and search queries.
    Operates without requiring paid OAuth or API keys via public JSON endpoints,
    with an automatic fallback to public Reddit RSS feeds when JSON is rate-limited.
    """

    def __init__(self, timeout_seconds: float = 15.0, post_limit: int = 25):
        self.timeout_seconds = timeout_seconds
        self.post_limit = post_limit

    async def collect(self, source: Source) -> CollectorResult:
        sub_name = clean_subreddit_name(source.identifier)
        logger.info(f"Collecting Reddit items for source '{source.name}' (r/{sub_name})")

        headers = {
            "User-Agent": REDDIT_USER_AGENT,
            "Accept": "application/json",
        }

        # Determine target URL: search query vs subreddit new posts
        if "search:" in source.identifier.lower() or "q=" in source.identifier.lower():
            query = re.sub(r"^search:\s*", "", source.identifier, flags=re.IGNORECASE)
            json_url = f"https://www.reddit.com/search.json?q={query}&sort=new&limit={self.post_limit}"
            rss_url = f"https://www.reddit.com/search.rss?q={query}&sort=new"
        else:
            json_url = f"https://www.reddit.com/r/{sub_name}/new.json?limit={self.post_limit}"
            rss_url = f"https://www.reddit.com/r/{sub_name}/new.rss"

        # Try JSON endpoint first
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = await client.get(json_url)

                if response.status_code == 200:
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    items: list[RawDiscoveredItem] = []

                    for child in children:
                        post = child.get("data", {})
                        post_id = post.get("id")
                        if not post_id:
                            continue

                        external_id = f"reddit_{post.get('name', f't3_{post_id}')}"
                        title = post.get("title", "").strip()
                        selftext = post.get("selftext", "").strip()
                        url = post.get("url", "")
                        permalink = f"https://www.reddit.com{post.get('permalink', '')}"

                        content = selftext if selftext else f"{title}\nLink: {url}"

                        created_utc = post.get("created_utc")
                        published_at = (
                            datetime.fromtimestamp(created_utc, tz=timezone.utc)
                            if created_utc
                            else None
                        )

                        items.append(
                            RawDiscoveredItem(
                                external_id=external_id,
                                content=content,
                                content_type="reddit_post",
                                title=title,
                                author=post.get("author"),
                                original_url=permalink,
                                published_at=published_at,
                                raw_metadata={
                                    "subreddit": post.get("subreddit"),
                                    "score": post.get("score"),
                                    "upvote_ratio": post.get("upvote_ratio"),
                                    "num_comments": post.get("num_comments"),
                                    "link_flair_text": post.get("link_flair_text"),
                                    "outbound_url": url,
                                    "is_self": post.get("is_self"),
                                },
                            )
                        )

                    logger.info(f"Collected {len(items)} posts from Reddit r/{sub_name} via JSON")
                    return CollectorResult(source_id=source.id, success=True, items=items)

                elif response.status_code == 429:
                    logger.warning(
                        f"Reddit JSON endpoint rate limited (429) for r/{sub_name}, falling back to RSS"
                    )
                else:
                    logger.warning(
                        f"Reddit JSON returned status {response.status_code} for r/{sub_name}, falling back to RSS"
                    )

        except Exception as exc:
            logger.warning(f"Reddit JSON request failed ({exc}), attempting RSS fallback")

        # Fallback to public RSS
        return await self._collect_via_rss(source, rss_url)

    async def _collect_via_rss(self, source: Source, rss_url: str) -> CollectorResult:
        """Fallback RSS collection when Reddit JSON endpoint is throttled."""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers={"User-Agent": REDDIT_USER_AGENT},
                follow_redirects=True,
            ) as client:
                response = await client.get(rss_url)
                response.raise_for_status()

            feed = feedparser.parse(response.content)
            items: list[RawDiscoveredItem] = []

            for entry in feed.entries:
                external_id = entry.get("id") or entry.get("link")
                title = entry.get("title", "").strip()
                raw_content = entry.get("content", [{}])[0].get("value", "") or entry.get(
                    "summary", ""
                )

                # Clean Reddit HTML
                soup = BeautifulSoup(raw_content, "html.parser")
                clean_text = soup.get_text(separator=" ", strip=True)

                items.append(
                    RawDiscoveredItem(
                        external_id=external_id,
                        content=clean_text or title,
                        content_type="reddit_post",
                        title=title,
                        author=entry.get("author"),
                        original_url=entry.get("link"),
                        published_at=datetime.now(timezone.utc),
                        raw_metadata={"source": "reddit_rss_fallback"},
                    )
                )

            logger.info(f"Collected {len(items)} posts from Reddit via RSS fallback")
            return CollectorResult(source_id=source.id, success=True, items=items)

        except Exception as exc:
            msg = f"Failed to collect Reddit data via RSS fallback: {exc}"
            logger.error(msg)
            return CollectorResult(source_id=source.id, success=False, error_message=msg)
