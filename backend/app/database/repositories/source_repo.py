"""Discovery Source repository."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.enums import SourceType
from app.database.models.source import Source


class SourceRepository:
    """Explicit database access for Discovery Sources."""

    @staticmethod
    def get_by_id(db: Session, source_id: int) -> Optional[Source]:
        return db.get(Source, source_id)

    @staticmethod
    def get_by_identifier(
        db: Session, source_type: SourceType, identifier: str
    ) -> Optional[Source]:
        stmt = select(Source).where(
            Source.source_type == source_type,
            Source.identifier == identifier,
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_active(
        db: Session, source_type: Optional[SourceType] = None, skip: int = 0, limit: int = 100
    ) -> List[Source]:
        stmt = select(Source).where(Source.is_active.is_(True))
        if source_type:
            stmt = stmt.where(Source.source_type == source_type)
        stmt = stmt.order_by(Source.name).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def create(
        db: Session,
        name: str,
        source_type: SourceType,
        identifier: str,
        url: Optional[str] = None,
        description: Optional[str] = None,
        collection_interval_seconds: int = 3600,
    ) -> Source:
        source = Source(
            name=name,
            source_type=source_type,
            identifier=identifier,
            url=url,
            description=description,
            collection_interval_seconds=collection_interval_seconds,
            is_active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source
