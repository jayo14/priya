"""Discovery module for multi-source ingestion in Priya."""

from app.discovery.base import (
    BaseSourceCollector,
    CollectorResult,
    RawDiscoveredItem,
    compute_content_hash,
)
from app.discovery.orchestrator import DiscoveryOrchestrator, OrchestrationStats
from app.discovery.reddit import RedditCollector
from app.discovery.telegram import TelegramCollector
from app.discovery.web import RssCollector, WebPageCollector

__all__ = [
    "BaseSourceCollector",
    "CollectorResult",
    "RawDiscoveredItem",
    "compute_content_hash",
    "DiscoveryOrchestrator",
    "OrchestrationStats",
    "TelegramCollector",
    "RedditCollector",
    "RssCollector",
    "WebPageCollector",
]
