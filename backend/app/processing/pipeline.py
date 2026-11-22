"""Processing pipeline connecting normalization, filtering, extraction, and deduplication."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import setup_logging
from app.database.models.enums import ProcessingStatus
from app.database.models.promotion import Promotion
from app.database.models.source import DiscoveredItem
from app.database.repositories.discovery_repo import DiscoveryRepository
from app.intelligence.engine import IntelligenceEngine
from app.processing.deduplicator import PromotionDeduplicator
from app.processing.extractor import OfferExtractor
from app.processing.filters import ContentFilter
from app.processing.normalizer import normalize_text

logger = setup_logging()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ProcessingItemResult:
    """Outcome of processing an individual discovered item."""

    item_id: int
    status: ProcessingStatus
    promotion_id: Optional[int] = None
    is_new_promotion: bool = False
    message: Optional[str] = None


@dataclass
class PipelineStats:
    """Aggregated outcome of a pipeline execution run."""

    items_processed: int = 0
    promotions_created: int = 0
    promotions_corroborated: int = 0
    irrelevant_count: int = 0
    failed_count: int = 0


class ProcessingPipeline:
    """Deterministic promotional extraction and classification pipeline."""

    def __init__(self):
        self.filter = ContentFilter()
        self.extractor = OfferExtractor()
        self.deduplicator = PromotionDeduplicator()
        self.intelligence = IntelligenceEngine()

    def process_item(self, db: Session, item: DiscoveredItem) -> ProcessingItemResult:
        """Process a single DiscoveredItem through all pipeline stages."""
        item.processing_status = ProcessingStatus.PROCESSING
        db.flush()

        # Stage 1: Normalization
        clean_title = normalize_text(item.title) if item.title else None
        clean_content = normalize_text(item.content)

        # Stage 2: Filtering & Spam Detection
        filter_res = self.filter.evaluate(clean_title, clean_content)
        if not filter_res.is_relevant:
            item.processing_status = ProcessingStatus.IRRELEVANT
            item.processed_at = utc_now()
            item.processing_error = filter_res.rejection_reason
            db.commit()
            return ProcessingItemResult(
                item_id=item.id,
                status=ProcessingStatus.IRRELEVANT,
                message=filter_res.rejection_reason,
            )

        # Stage 3: Extraction & Classification
        extracted = self.extractor.extract(db, item)
        if not extracted or not extracted.provider_id:
            msg = "Could not identify a target AI provider in promotional content."
            item.processing_status = ProcessingStatus.IRRELEVANT
            item.processed_at = utc_now()
            item.processing_error = msg
            db.commit()
            return ProcessingItemResult(
                item_id=item.id,
                status=ProcessingStatus.IRRELEVANT,
                message=msg,
            )

        # Stage 4: Deduplication & Canonical Linking
        try:
            promo: Promotion
            is_new: bool
            promo, is_new = self.deduplicator.persist_or_corroborate(
                db=db, discovered_item_id=item.id, offer=extracted
            )

            # Stage 5: Promotion Intelligence & Scoring
            try:
                self.intelligence.evaluate_promotion(
                    db=db, promotion=promo, perform_network_check=False
                )
            except Exception as intel_err:
                logger.warning(
                    f"Intelligence evaluation non-fatal warning on promo #{promo.id}: {intel_err}"
                )

            item.processing_status = ProcessingStatus.PROCESSED
            item.processed_at = utc_now()
            item.processing_error = None
            db.commit()

            return ProcessingItemResult(
                item_id=item.id,
                status=ProcessingStatus.PROCESSED,
                promotion_id=promo.id,
                is_new_promotion=is_new,
                message=f"{'Created' if is_new else 'Corroborated'} promotion #{promo.id}",
            )

        except Exception as exc:
            db.rollback()
            err_msg = f"Error during deduplication/persistence: {exc}"
            logger.error(err_msg, exc_info=True)
            item.processing_status = ProcessingStatus.FAILED
            item.processed_at = utc_now()
            item.processing_error = err_msg
            db.commit()
            return ProcessingItemResult(
                item_id=item.id,
                status=ProcessingStatus.FAILED,
                message=err_msg,
            )

    def process_pending_items(self, db: Session, limit: int = 50) -> PipelineStats:
        """Fetch pending items and execute extraction pipeline."""
        pending_items = DiscoveryRepository.list_pending(db, limit=limit)
        stats = PipelineStats()

        logger.info(f"Pipeline running for {len(pending_items)} pending discovered items")

        for item in pending_items:
            stats.items_processed += 1
            res = self.process_item(db, item)
            if res.status == ProcessingStatus.PROCESSED:
                if res.is_new_promotion:
                    stats.promotions_created += 1
                else:
                    stats.promotions_corroborated += 1
            elif res.status == ProcessingStatus.IRRELEVANT:
                stats.irrelevant_count += 1
            elif res.status == ProcessingStatus.FAILED:
                stats.failed_count += 1

        logger.info(
            f"Pipeline finished. Processed: {stats.items_processed}, New: {stats.promotions_created}, Corroborated: {stats.promotions_corroborated}, Irrelevant: {stats.irrelevant_count}, Failed: {stats.failed_count}"
        )
        return stats
