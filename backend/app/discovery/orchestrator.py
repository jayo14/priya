"""Discovery orchestrator for routing, executing, and persisting source items."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import setup_logging
from app.database.models.enums import SourceType
from app.database.models.source import DiscoveredItem, Source
from app.database.repositories.discovery_repo import DiscoveryRepository
from app.database.repositories.source_repo import SourceRepository
from app.discovery.base import (
    BaseSourceCollector,
    CollectorResult,
    RawDiscoveredItem,
)
from app.discovery.reddit import RedditCollector
from app.discovery.telegram import TelegramCollector
from app.discovery.web import RssCollector, WebPageCollector

logger = setup_logging()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class OrchestrationStats:
    """Summary metrics of an orchestration run."""

    sources_processed: int = 0
    items_collected: int = 0
    duplicates_skipped: int = 0
    errors: List[str] = field(default_factory=list)


class DiscoveryOrchestrator:
    """Orchestrates source collection execution, deduplication, and persistence."""

    def __init__(self):
        self._collectors: Dict[SourceType, BaseSourceCollector] = {
            SourceType.TELEGRAM: TelegramCollector(),
            SourceType.REDDIT: RedditCollector(),
            SourceType.RSS: RssCollector(),
            SourceType.WEBSITE: WebPageCollector(),
        }

    def get_collector(self, source_type: SourceType) -> Optional[BaseSourceCollector]:
        return self._collectors.get(source_type)

    async def collect_source(
        self, db: Session, source: Source
    ) -> CollectorResult:
        """Execute collection for a single source and persist new items."""
        collector = self.get_collector(source.source_type)
        if not collector:
            error_msg = f"No collector adapter registered for source type: {source.source_type}"
            logger.error(error_msg)
            source.last_collected_at = utc_now()
            source.last_error_at = utc_now()
            source.last_error_message = error_msg
            db.commit()
            return CollectorResult(source_id=source.id, success=False, error_message=error_msg)

        # Run collection
        result = await collector.collect(source)

        source.last_collected_at = utc_now()
        if result.success:
            source.last_successful_collection_at = utc_now()
            source.last_error_message = None

            # Persist items with duplicate detection
            persisted_count = 0
            for raw_item in result.items:
                if self._persist_item(db, source.id, raw_item):
                    persisted_count += 1

            logger.info(
                f"Source '{source.name}': {len(result.items)} collected, {persisted_count} newly persisted"
            )
        else:
            source.last_error_at = utc_now()
            source.last_error_message = result.error_message
            logger.warning(
                f"Collection failed for source '{source.name}': {result.error_message}"
            )

        db.commit()
        return result

    async def collect_all_active_sources(self, db: Session) -> OrchestrationStats:
        """Run collection across all active registered sources in the database."""
        sources = SourceRepository.list_active(db)
        stats = OrchestrationStats()

        logger.info(f"Starting discovery run across {len(sources)} active sources")

        for source in sources:
            stats.sources_processed += 1
            try:
                res = await self.collect_source(db, source)
                if res.success:
                    stats.items_collected += len(res.items)
                else:
                    stats.errors.append(f"{source.name}: {res.error_message}")
            except Exception as exc:
                err = f"Unexpected exception collecting {source.name}: {exc}"
                logger.error(err, exc_info=True)
                stats.errors.append(err)

        logger.info(
            f"Discovery run finished. Processed {stats.sources_processed} sources, collected {stats.items_collected} items, errors: {len(stats.errors)}"
        )
        return stats

    def _persist_item(
        self, db: Session, source_id: int, raw_item: RawDiscoveredItem
    ) -> Optional[DiscoveredItem]:
        """Check uniqueness by external_id and content_hash before persisting."""
        # 1. Check if external_id already exists for this source
        existing = DiscoveryRepository.get_by_external_id(
            db, source_id=source_id, external_id=raw_item.external_id
        )
        if existing:
            return None

        # 2. Check content hash duplicate detection
        item_hash = raw_item.content_hash
        existing_hash = DiscoveryRepository.get_by_content_hash(db, content_hash=item_hash)
        if existing_hash and existing_hash.source_id == source_id:
            return None

        # 3. Persist new item
        try:
            return DiscoveryRepository.create_item(
                db=db,
                source_id=source_id,
                external_id=raw_item.external_id,
                content=raw_item.content,
                content_type=raw_item.content_type,
                title=raw_item.title,
                author=raw_item.author,
                original_url=raw_item.original_url,
                raw_metadata=raw_item.raw_metadata,
                content_hash=item_hash,
            )
        except Exception as exc:
            logger.warning(
                f"Failed to persist discovered item {raw_item.external_id}: {exc}"
            )
            db.rollback()
            return None
