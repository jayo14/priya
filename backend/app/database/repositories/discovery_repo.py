"""Discovered item repository."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.enums import ProcessingStatus
from app.database.models.source import DiscoveredItem


class DiscoveryRepository:
    """Explicit database access for raw collected items."""

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[DiscoveredItem]:
        return db.get(DiscoveredItem, item_id)

    @staticmethod
    def get_by_external_id(
        db: Session, source_id: int, external_id: str
    ) -> Optional[DiscoveredItem]:
        stmt = select(DiscoveredItem).where(
            DiscoveredItem.source_id == source_id,
            DiscoveredItem.external_id == external_id,
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_content_hash(db: Session, content_hash: str) -> Optional[DiscoveredItem]:
        stmt = select(DiscoveredItem).where(DiscoveredItem.content_hash == content_hash)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_item(
        db: Session,
        source_id: int,
        external_id: str,
        content: str,
        content_type: str = "post",
        title: Optional[str] = None,
        author: Optional[str] = None,
        original_url: Optional[str] = None,
        raw_metadata: Optional[dict] = None,
        content_hash: Optional[str] = None,
    ) -> DiscoveredItem:
        item = DiscoveredItem(
            source_id=source_id,
            external_id=external_id,
            content_type=content_type,
            title=title,
            content=content,
            author=author,
            original_url=original_url,
            raw_metadata=raw_metadata or {},
            content_hash=content_hash,
            processing_status=ProcessingStatus.PENDING,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def list_pending(db: Session, limit: int = 50) -> List[DiscoveredItem]:
        stmt = (
            select(DiscoveredItem)
            .where(DiscoveredItem.processing_status == ProcessingStatus.PENDING)
            .order_by(DiscoveredItem.discovered_at.asc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())
