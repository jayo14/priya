"""Promotion repository."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.enums import (
    EligibilityRuleType,
    LinkType,
    OfferType,
    PromotionStatus,
)
from app.database.models.promotion import (
    EligibilityRule,
    Promotion,
    PromotionDiscovery,
    PromotionLink,
    VerificationCheck,
)


class PromotionRepository:
    """Explicit database access for Promotions and associated structures."""

    @staticmethod
    def get_by_id(db: Session, promotion_id: int) -> Optional[Promotion]:
        return db.get(Promotion, promotion_id)

    @staticmethod
    def list_promotions(
        db: Session,
        provider_id: Optional[int] = None,
        status: Optional[PromotionStatus] = None,
        offer_type: Optional[OfferType] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Promotion]:
        stmt = select(Promotion)
        if provider_id:
            stmt = stmt.where(Promotion.provider_id == provider_id)
        if status:
            stmt = stmt.where(Promotion.status == status)
        if offer_type:
            stmt = stmt.where(Promotion.offer_type == offer_type)
        stmt = stmt.order_by(Promotion.first_discovered_at.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def create_promotion(
        db: Session,
        provider_id: int,
        title: str,
        offer_type: OfferType = OfferType.UNKNOWN,
        plan_id: Optional[int] = None,
        description: Optional[str] = None,
        discount_percentage: Optional[Decimal] = None,
        duration_days: Optional[int] = None,
        promo_code: Optional[str] = None,
        eligible_countries: Optional[list] = None,
        excluded_countries: Optional[list] = None,
        account_requirements: Optional[dict] = None,
        payment_required: Optional[bool] = None,
        starts_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        status: PromotionStatus = PromotionStatus.UNVERIFIED,
        confidence_score: int = 0,
    ) -> Promotion:
        promotion = Promotion(
            provider_id=provider_id,
            plan_id=plan_id,
            title=title,
            description=description,
            offer_type=offer_type,
            discount_percentage=discount_percentage,
            duration_days=duration_days,
            promo_code=promo_code,
            eligible_countries=eligible_countries or [],
            excluded_countries=excluded_countries or [],
            account_requirements=account_requirements or {},
            payment_required=payment_required,
            starts_at=starts_at,
            expires_at=expires_at,
            status=status,
            confidence_score=confidence_score,
        )
        db.add(promotion)
        db.commit()
        db.refresh(promotion)
        return promotion

    @staticmethod
    def associate_discovery(
        db: Session, promotion_id: int, discovered_item_id: int
    ) -> PromotionDiscovery:
        assoc = PromotionDiscovery(
            promotion_id=promotion_id,
            discovered_item_id=discovered_item_id,
        )
        db.add(assoc)
        db.commit()
        db.refresh(assoc)
        return assoc

    @staticmethod
    def add_link(
        db: Session,
        promotion_id: int,
        original_url: str,
        normalized_url: str,
        destination_domain: str,
        link_type: LinkType = LinkType.OTHER,
        is_primary: bool = False,
    ) -> PromotionLink:
        link = PromotionLink(
            promotion_id=promotion_id,
            original_url=original_url,
            normalized_url=normalized_url,
            destination_domain=destination_domain,
            link_type=link_type,
            is_primary=is_primary,
            is_active=True,
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def add_verification_check(
        db: Session,
        promotion_id: int,
        check_type: str,
        result: str,
        status: str,
        details: Optional[dict] = None,
    ) -> VerificationCheck:
        check = VerificationCheck(
            promotion_id=promotion_id,
            check_type=check_type,
            result=result,
            status=status,
            details=details or {},
        )
        db.add(check)
        db.commit()
        db.refresh(check)
        return check

    @staticmethod
    def add_eligibility_rule(
        db: Session,
        promotion_id: int,
        rule_type: EligibilityRuleType,
        description: str,
        country_code: Optional[str] = None,
        evidence_url: Optional[str] = None,
    ) -> EligibilityRule:
        rule = EligibilityRule(
            promotion_id=promotion_id,
            rule_type=rule_type,
            description=description,
            country_code=country_code,
            evidence_url=evidence_url,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule
