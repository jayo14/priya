"""Promotion deduplication and multi-source corroboration engine."""

from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import setup_logging
from app.database.models.enums import LinkType, PromotionStatus
from app.database.models.promotion import (
    Promotion,
    PromotionDiscovery,
    PromotionLink,
)
from app.database.repositories.promotion_repo import PromotionRepository
from app.processing.extractor import ExtractedOffer

logger = setup_logging()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PromotionDeduplicator:
    """Matches incoming extracted offers with existing promotions or provisions canonical records."""

    def find_matching_promotion(
        self, db: Session, offer: ExtractedOffer
    ) -> Optional[Promotion]:
        """
        Deterministic multi-factor matching:
        1. Exact provider + promo_code match
        2. Exact provider + normalized redemption URL match
        3. Exact provider + plan + offer_type + destination_domain match
        """
        if not offer.provider_id:
            return None

        # 1. Match by promo code
        if offer.promo_code:
            stmt = select(Promotion).where(
                Promotion.provider_id == offer.provider_id,
                Promotion.promo_code == offer.promo_code,
            )
            match = db.execute(stmt).scalar_one_or_none()
            if match:
                logger.info(
                    f"Deduplication match by promo code: {offer.promo_code} -> Promo #{match.id}"
                )
                return match

        # 2. Match by normalized redemption URL in promotion_links
        if offer.normalized_url:
            link_stmt = (
                select(PromotionLink)
                .join(Promotion, Promotion.id == PromotionLink.promotion_id)
                .where(
                    Promotion.provider_id == offer.provider_id,
                    PromotionLink.normalized_url == offer.normalized_url,
                )
            )
            matching_link = db.execute(link_stmt).scalar_one_or_none()
            if matching_link:
                promo = PromotionRepository.get_by_id(db, matching_link.promotion_id)
                if promo:
                    logger.info(
                        f"Deduplication match by URL: {offer.normalized_url} -> Promo #{promo.id}"
                    )
                    return promo

        # 3. Match by provider + plan + offer_type + destination_domain
        if offer.plan_id and offer.destination_domain:
            cand_stmt = select(Promotion).where(
                Promotion.provider_id == offer.provider_id,
                Promotion.plan_id == offer.plan_id,
                Promotion.offer_type == offer.offer_type,
            )
            candidates = list(db.execute(cand_stmt).scalars().all())
            for cand in candidates:
                for link in cand.links:
                    if link.destination_domain == offer.destination_domain:
                        logger.info(
                            f"Deduplication match by domain/plan: {offer.destination_domain} -> Promo #{cand.id}"
                        )
                        return cand

        return None

    def persist_or_corroborate(
        self, db: Session, discovered_item_id: int, offer: ExtractedOffer
    ) -> Tuple[Promotion, bool]:
        """
        Either links discovery to an existing canonical promotion (source corroboration),
        or creates a new canonical promotion. Returns (promotion, is_new).
        """
        existing = self.find_matching_promotion(db, offer)

        if existing:
            # Source corroboration
            existing.last_discovered_at = utc_now()
            # Reward corroborated multi-source discovery with higher confidence
            existing.confidence_score = min(100, existing.confidence_score + 5)

            # Check if discovery is already associated
            disc_stmt = select(PromotionDiscovery).where(
                PromotionDiscovery.promotion_id == existing.id,
                PromotionDiscovery.discovered_item_id == discovered_item_id,
            )
            already_linked = db.execute(disc_stmt).scalar_one_or_none()
            if not already_linked:
                PromotionRepository.associate_discovery(
                    db, promotion_id=existing.id, discovered_item_id=discovered_item_id
                )
                logger.info(
                    f"Corroborated existing promotion #{existing.id} with discovered item #{discovered_item_id}"
                )

            # Add any novel redemption link
            if offer.redemption_url and offer.normalized_url and offer.destination_domain:
                existing_urls = {lnk.normalized_url for lnk in existing.links}
                if offer.normalized_url not in existing_urls:
                    PromotionRepository.add_link(
                        db=db,
                        promotion_id=existing.id,
                        original_url=offer.redemption_url,
                        normalized_url=offer.normalized_url,
                        destination_domain=offer.destination_domain,
                        link_type=LinkType.REDEMPTION,
                        is_primary=False,
                    )

            db.commit()
            return existing, False

        # Create new canonical promotion
        new_promo = PromotionRepository.create_promotion(
            db=db,
            provider_id=offer.provider_id,  # type: ignore
            plan_id=offer.plan_id,
            title=offer.title,
            description=offer.description,
            offer_type=offer.offer_type,
            discount_percentage=offer.discount_percentage,
            duration_days=offer.duration_days,
            promo_code=offer.promo_code,
            eligible_countries=offer.eligible_countries,
            excluded_countries=offer.excluded_countries,
            account_requirements=offer.account_requirements,
            payment_required=offer.payment_required,
            starts_at=None,
            expires_at=offer.expires_at,
            status=PromotionStatus.UNVERIFIED,
            confidence_score=offer.confidence_score,
        )

        # Associate initial discovery
        PromotionRepository.associate_discovery(
            db=db, promotion_id=new_promo.id, discovered_item_id=discovered_item_id
        )

        # Add primary redemption link if found
        if offer.redemption_url and offer.normalized_url and offer.destination_domain:
            PromotionRepository.add_link(
                db=db,
                promotion_id=new_promo.id,
                original_url=offer.redemption_url,
                normalized_url=offer.normalized_url,
                destination_domain=offer.destination_domain,
                link_type=LinkType.REDEMPTION,
                is_primary=True,
            )

        logger.info(
            f"Created new canonical promotion #{new_promo.id} '{new_promo.title}' from discovery #{discovered_item_id}"
        )
        return new_promo, True
