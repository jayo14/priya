"""API endpoints for user watchlist (bookmarked promotions and priority providers)."""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import DbSession
from app.api.routes.promotions import PromotionResponse
from app.database.models.promotion import Promotion
from app.database.models.provider import Provider
from app.database.models.setting import AppSetting

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

WATCHLIST_KEY = "user_watchlist"


class WatchlistResponse(BaseModel):
    promotion_ids: List[int]
    provider_ids: List[int]
    total_saved_promotions: int
    total_watched_providers: int


def _get_or_create_watchlist(db: Session) -> AppSetting:
    setting = db.execute(select(AppSetting).where(AppSetting.key == WATCHLIST_KEY)).scalar_one_or_none()
    if not setting:
        setting = AppSetting(
            key=WATCHLIST_KEY,
            value={"promotion_ids": [], "provider_ids": []},
            description="User saved promotions and watched AI providers",
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.get("", response_model=WatchlistResponse)
def get_watchlist(db: Session = DbSession):
    """Retrieve current watchlist IDs for promotions and providers."""
    setting = _get_or_create_watchlist(db)
    val = setting.value or {}
    promos = val.get("promotion_ids", [])
    provs = val.get("provider_ids", [])

    return WatchlistResponse(
        promotion_ids=promos,
        provider_ids=provs,
        total_saved_promotions=len(promos),
        total_watched_providers=len(provs),
    )


@router.post("/promotions/{promotion_id}", response_model=WatchlistResponse)
def toggle_promotion_watchlist(promotion_id: int, db: Session = DbSession):
    """Toggle a promotion's bookmark status in the watchlist."""
    promo = db.execute(select(Promotion).where(Promotion.id == promotion_id)).scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    setting = _get_or_create_watchlist(db)
    val = dict(setting.value or {"promotion_ids": [], "provider_ids": []})
    promos: List[int] = list(val.get("promotion_ids", []))

    if promotion_id in promos:
        promos.remove(promotion_id)
    else:
        promos.append(promotion_id)

    val["promotion_ids"] = promos
    setting.value = val
    db.commit()
    db.refresh(setting)

    provs = val.get("provider_ids", [])
    return WatchlistResponse(
        promotion_ids=promos,
        provider_ids=provs,
        total_saved_promotions=len(promos),
        total_watched_providers=len(provs),
    )


@router.delete("/promotions/{promotion_id}", response_model=WatchlistResponse)
def remove_promotion_watchlist(promotion_id: int, db: Session = DbSession):
    """Explicitly remove a promotion from the watchlist."""
    setting = _get_or_create_watchlist(db)
    val = dict(setting.value or {"promotion_ids": [], "provider_ids": []})
    promos: List[int] = list(val.get("promotion_ids", []))

    if promotion_id in promos:
        promos.remove(promotion_id)
        val["promotion_ids"] = promos
        setting.value = val
        db.commit()
        db.refresh(setting)

    provs = val.get("provider_ids", [])
    return WatchlistResponse(
        promotion_ids=promos,
        provider_ids=provs,
        total_saved_promotions=len(promos),
        total_watched_providers=len(provs),
    )


@router.post("/providers/{provider_id}", response_model=WatchlistResponse)
def toggle_provider_watchlist(provider_id: int, db: Session = DbSession):
    """Toggle watching a specific AI provider."""
    prov = db.execute(select(Provider).where(Provider.id == provider_id)).scalar_one_or_none()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")

    setting = _get_or_create_watchlist(db)
    val = dict(setting.value or {"promotion_ids": [], "provider_ids": []})
    provs: List[int] = list(val.get("provider_ids", []))

    if provider_id in provs:
        provs.remove(provider_id)
    else:
        provs.append(provider_id)

    val["provider_ids"] = provs
    setting.value = val
    db.commit()
    db.refresh(setting)

    promos = val.get("promotion_ids", [])
    return WatchlistResponse(
        promotion_ids=promos,
        provider_ids=provs,
        total_saved_promotions=len(promos),
        total_watched_providers=len(provs),
    )


@router.get("/items", response_model=List[PromotionResponse])
def get_watchlist_items(db: Session = DbSession):
    """List full details for all promotions currently bookmarked in user watchlist."""
    setting = _get_or_create_watchlist(db)
    promo_ids = setting.value.get("promotion_ids", []) if setting.value else []

    if not promo_ids:
        return []

    promos = list(
        db.execute(select(Promotion).where(Promotion.id.in_(promo_ids))).scalars().all()
    )

    from app.api.routes.promotions import PromotionLinkResponse

    return [
        PromotionResponse(
            id=p.id,
            provider_id=p.provider_id,
            provider_slug=p.provider.slug if p.provider else None,
            provider_name=p.provider.name if p.provider else None,
            plan_id=p.plan_id,
            plan_slug=p.plan.slug if p.plan else None,
            plan_name=p.plan.name if p.plan else None,
            title=p.title,
            description=p.description,
            offer_type=p.offer_type.value,
            discount_percentage=p.discount_percentage,
            duration_days=p.duration_days,
            promo_code=p.promo_code,
            eligible_countries=p.eligible_countries,
            excluded_countries=p.excluded_countries,
            account_requirements=p.account_requirements,
            payment_required=p.payment_required,
            status=p.status.value,
            confidence_score=p.confidence_score,
            first_discovered_at=p.first_discovered_at.isoformat(),
            last_discovered_at=p.last_discovered_at.isoformat(),
            discoveries_count=len(p.discoveries),
            links=[
                PromotionLinkResponse(
                    id=lnk.id,
                    original_url=lnk.original_url,
                    normalized_url=lnk.normalized_url,
                    destination_domain=lnk.destination_domain,
                    link_type=lnk.link_type.value,
                    is_primary=lnk.is_primary,
                )
                for lnk in p.links
            ],
        )
        for p in promos
    ]
