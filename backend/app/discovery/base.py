"""Common source adapter interface and data contracts for discovery collectors."""

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.models.source import Source


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def compute_content_hash(text: str) -> str:
    """Compute a SHA-256 hash over normalized whitespace-collapsed text for deduplication."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class RawDiscoveredItem:
    """A raw content item collected from an external source prior to database persistence."""

    external_id: str
    content: str
    content_type: str = "post"
    title: Optional[str] = None
    author: Optional[str] = None
    original_url: Optional[str] = None
    published_at: Optional[datetime] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return compute_content_hash(f"{self.title or ''} {self.content}")


@dataclass
class CollectorResult:
    """Outcome of a single collector execution run for a given Source."""

    source_id: int
    success: bool
    items: List[RawDiscoveredItem] = field(default_factory=list)
    error_message: Optional[str] = None
    collected_at: datetime = field(default_factory=utc_now)


class BaseSourceCollector(ABC):
    """Abstract base class for all external source collectors."""

    @abstractmethod
    async def collect(self, source: Source) -> CollectorResult:
        """
        Collect latest items from the external source.
        Must handle its own transport errors, rate limits, and timeouts,
        returning a CollectorResult without letting unhandled network exceptions crash the application.
        """
        pass
