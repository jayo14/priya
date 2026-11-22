"""Dashboard summary metrics and activity API endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import DbSession
from app.database.models.enums import PromotionStatus
from app.database.models.promotion import Promotion
from app.database.models.provider import Provider
from app.database.models.source import DiscoveredItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- Response Schemas ---


class ProviderMetricItem(BaseModel):
    provider_id: int
    name: str
    slug: str
    promotions_count: int
    verified_count: int
    avg_confidence: float


class RecentPromotionItem(BaseModel):
    id: int
    provider_name: str
    provider_slug: str
    plan_name: Optional[str]
    title: str
    offer_type: str
    status: str
    confidence_score: int
    is_nigeria_eligible: bool
    first_discovered_at: str


class DashboardStatsResponse(BaseModel):
    total_discovered_items: int
    total_promotions: int
    verified_promotions: int
    likely_valid_promotions: int
    expiring_promotions: int
    nigeria_eligible_promotions: int
    providers: List[ProviderMetricItem]
    offer_type_distribution: Dict[str, int]
    recent_discoveries: List[RecentPromotionItem]


class ActivityItemResponse(BaseModel):
    id: int
    source_name: str
    source_type: str
    title: Optional[str]
    processing_status: str
    discovered_at: str


# --- Endpoints ---


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = DbSession):
    """Retrieve top-level discovery KPIs, provider deal distributions, and recent opportunities."""
    now = utc_now()
    two_days_ahead = now + timedelta(hours=48)

    # Global KPI counts
    total_discovered = db.execute(select(func.count(DiscoveredItem.id))).scalar_one()
    total_promos = db.execute(select(func.count(Promotion.id))).scalar_one()

    verified_promos = db.execute(
        select(func.count(Promotion.id)).where(Promotion.status == PromotionStatus.VERIFIED)
    ).scalar_one()

    likely_valid_promos = db.execute(
        select(func.count(Promotion.id)).where(Promotion.status == PromotionStatus.LIKELY_VALID)
    ).scalar_one()

    # Expiring soon (within next 48h)
    expiring_count = db.execute(
        select(func.count(Promotion.id)).where(
            Promotion.expires_at.is_not(None),
            Promotion.expires_at > now,
            Promotion.expires_at <= two_days_ahead,
        )
    ).scalar_one()

    # Query all active promotions to compute regional & offer-type breakdowns
    all_promos = list(db.execute(select(Promotion)).scalars().all())

    nigeria_eligible_count = 0
    offer_types: Dict[str, int] = {}

    for promo in all_promos:
        upper_el = [c.upper() for c in promo.eligible_countries]
        upper_ex = [c.upper() for c in promo.excluded_countries]

        if "NG" not in upper_ex and ("NG" in upper_el or "GLOBAL" in upper_el or not upper_el):
            nigeria_eligible_count += 1

        otype = promo.offer_type.value
        offer_types[otype] = offer_types.get(otype, 0) + 1

    # Provider breakdown
    providers = list(db.execute(select(Provider).order_by(Provider.name)).scalars().all())
    provider_metrics: List[ProviderMetricItem] = []

    for prov in providers:
        prov_promos = [p for p in all_promos if p.provider_id == prov.id]
        verified_prov = [p for p in prov_promos if p.status == PromotionStatus.VERIFIED]
        avg_score = (
            sum(p.confidence_score for p in prov_promos) / len(prov_promos) if prov_promos else 0.0
        )

        provider_metrics.append(
            ProviderMetricItem(
                provider_id=prov.id,
                name=prov.name,
                slug=prov.slug,
                promotions_count=len(prov_promos),
                verified_count=len(verified_prov),
                avg_confidence=round(avg_score, 1),
            )
        )

    # Recent 6 discoveries
    recent_query = (
        select(Promotion).order_by(Promotion.first_discovered_at.desc()).limit(6)
    )
    recent_promos = list(db.execute(recent_query).scalars().all())

    recent_items: List[RecentPromotionItem] = []
    for p in recent_promos:
        upper_el = [c.upper() for c in p.eligible_countries]
        upper_ex = [c.upper() for c in p.excluded_countries]
        is_ng = "NG" not in upper_ex and ("NG" in upper_el or "GLOBAL" in upper_el or not upper_el)

        recent_items.append(
            RecentPromotionItem(
                id=p.id,
                provider_name=p.provider.name if p.provider else "Unknown",
                provider_slug=p.provider.slug if p.provider else "unknown",
                plan_name=p.plan.name if p.plan else None,
                title=p.title,
                offer_type=p.offer_type.value,
                status=p.status.value,
                confidence_score=p.confidence_score,
                is_nigeria_eligible=is_ng,
                first_discovered_at=p.first_discovered_at.isoformat(),
            )
        )

    return DashboardStatsResponse(
        total_discovered_items=total_discovered,
        total_promotions=total_promos,
        verified_promotions=verified_promos,
        likely_valid_promotions=likely_valid_promos,
        expiring_promotions=expiring_count,
        nigeria_eligible_promotions=nigeria_eligible_count,
        providers=provider_metrics,
        offer_type_distribution=offer_types,
        recent_discoveries=recent_items,
    )


@router.get("/activity", response_model=List[ActivityItemResponse])
def get_dashboard_activity(limit: int = 10, db: Session = DbSession):
    """Retrieve latest ingestion and discovery activity feed."""
    items = list(
        db.execute(
            select(DiscoveredItem)
            .order_by(DiscoveredItem.discovered_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    return [
        ActivityItemResponse(
            id=item.id,
            source_name=item.source.name if item.source else "Unknown Source",
            source_type=item.source.source_type.value if item.source else "unknown",
            title=item.title,
            processing_status=item.processing_status.value,
            discovered_at=item.discovered_at.isoformat(),
        )
        for item in items
    ]
