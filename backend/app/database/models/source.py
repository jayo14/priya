"""Discovery Source and Discovered Item models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.enums import ProcessingStatus, SourceType
from app.database.session import Base

if TYPE_CHECKING:
    from app.database.models.promotion import PromotionDiscovery


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Source(Base):
    """External source to monitor (Telegram channel, Subreddit, Website, RSS feed)."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum"), nullable=False, index=True
    )
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    collection_interval_seconds: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    last_collected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_successful_collection_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("source_type", "identifier", name="uq_source_type_identifier"),
    )

    # Relationships
    discovered_items: Mapped[List["DiscoveredItem"]] = relationship(
        "DiscoveredItem", back_populates="source", cascade="all, delete-orphan"
    )


class DiscoveredItem(Base):
    """Raw content collected from an external source before or after processing."""

    __tablename__ = "discovered_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(
        String(50), default="post", nullable=False
    )  # e.g. telegram_message, reddit_post, reddit_comment, web_page, rss_item
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    original_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    raw_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status_enum"),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_source_external_id"),)

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="discovered_items")
    discoveries: Mapped[List["PromotionDiscovery"]] = relationship(
        "PromotionDiscovery", back_populates="discovered_item", cascade="all, delete-orphan"
    )
