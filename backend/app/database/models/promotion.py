"""Promotion and associated relationship domain models."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.enums import (
    EligibilityRuleType,
    LinkType,
    OfferType,
    PromotionStatus,
)
from app.database.session import Base

if TYPE_CHECKING:
    from app.database.models.notification import Notification
    from app.database.models.provider import Plan, Provider
    from app.database.models.source import DiscoveredItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Promotion(Base):
    """Canonical AI subscription promotion entity."""

    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("providers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    offer_type: Mapped[OfferType] = mapped_column(
        Enum(OfferType, name="offer_type_enum"),
        default=OfferType.UNKNOWN,
        nullable=False,
        index=True,
    )
    discount_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    promo_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    eligible_countries: Mapped[list] = mapped_column(
        JSONB, default=list, nullable=False
    )  # List of ISO alpha-2 codes (e.g. ["NG", "US"])
    excluded_countries: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    account_requirements: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    payment_required: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    status: Mapped[PromotionStatus] = mapped_column(
        Enum(PromotionStatus, name="promotion_status_enum"),
        default=PromotionStatus.UNVERIFIED,
        nullable=False,
        index=True,
    )
    confidence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    first_discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )
    last_discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 100",
            name="check_confidence_score_range",
        ),
    )

    # Relationships
    provider: Mapped["Provider"] = relationship("Provider", back_populates="promotions")
    plan: Mapped[Optional["Plan"]] = relationship("Plan", back_populates="promotions")
    discoveries: Mapped[List["PromotionDiscovery"]] = relationship(
        "PromotionDiscovery", back_populates="promotion", cascade="all, delete-orphan"
    )
    links: Mapped[List["PromotionLink"]] = relationship(
        "PromotionLink", back_populates="promotion", cascade="all, delete-orphan"
    )
    verification_checks: Mapped[List["VerificationCheck"]] = relationship(
        "VerificationCheck", back_populates="promotion", cascade="all, delete-orphan"
    )
    eligibility_rules: Mapped[List["EligibilityRule"]] = relationship(
        "EligibilityRule", back_populates="promotion", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="promotion", cascade="all, delete-orphan"
    )


class PromotionDiscovery(Base):
    """Many-to-many relationship linking a Promotion to one or more DiscoveredItems."""

    __tablename__ = "promotion_discoveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    discovered_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("discovered_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "promotion_id", "discovered_item_id", name="uq_promotion_discovered_item"
        ),
    )

    # Relationships
    promotion: Mapped["Promotion"] = relationship("Promotion", back_populates="discoveries")
    discovered_item: Mapped["DiscoveredItem"] = relationship(
        "DiscoveredItem", back_populates="discoveries"
    )


class PromotionLink(Base):
    """External URLs and redemption links associated with a promotion."""

    __tablename__ = "promotion_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    destination_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    link_type: Mapped[LinkType] = mapped_column(
        Enum(LinkType, name="link_type_enum"),
        default=LinkType.OTHER,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    promotion: Mapped["Promotion"] = relationship("Promotion", back_populates="links")


class VerificationCheck(Base):
    """Historical record of verification runs against a promotion."""

    __tablename__ = "verification_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    check_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # url_accessibility, redirect_inspection, domain_verification, expiry, eligibility, authenticity
    result: Mapped[str] = mapped_column(String(50), nullable=False)  # pass, fail, warning
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # completed, failed, pending
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )

    # Relationships
    promotion: Mapped["Promotion"] = relationship(
        "Promotion", back_populates="verification_checks"
    )


class EligibilityRule(Base):
    """Structured eligibility condition or restriction for a promotion."""

    __tablename__ = "eligibility_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_type: Mapped[EligibilityRuleType] = mapped_column(
        Enum(EligibilityRuleType, name="eligibility_rule_type_enum"),
        nullable=False,
    )
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)  # ISO alpha-2
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    promotion: Mapped["Promotion"] = relationship("Promotion", back_populates="eligibility_rules")
