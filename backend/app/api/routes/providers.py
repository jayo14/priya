"""API endpoints for managing and inspecting AI subscription providers and plans."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import DbSession
from app.database.models.promotion import Promotion
from app.database.models.provider import Plan, Provider

router = APIRouter(prefix="/providers", tags=["Providers"])


# --- Schemas ---


class PlanResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class ProviderResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    website_url: Optional[str]
    is_active: bool
    plans_count: int
    promotions_count: int
    plans: List[PlanResponse]

    model_config = {"from_attributes": True}


# --- Endpoints ---


@router.get("", response_model=List[ProviderResponse])
def list_providers(db: Session = DbSession):
    """List all AI subscription providers with supported plans and active deal counts."""
    providers = list(db.execute(select(Provider).order_by(Provider.name)).scalars().all())

    result: List[ProviderResponse] = []
    for prov in providers:
        promo_count = db.execute(
            select(func.count(Promotion.id)).where(Promotion.provider_id == prov.id)
        ).scalar_one()

        plans_list = [
            PlanResponse(
                id=p.id,
                name=p.name,
                slug=p.slug,
                description=p.description,
                is_active=p.is_active,
            )
            for p in prov.plans
        ]

        result.append(
            ProviderResponse(
                id=prov.id,
                name=prov.name,
                slug=prov.slug,
                description=prov.description,
                website_url=prov.website_url,
                is_active=prov.is_active,
                plans_count=len(plans_list),
                promotions_count=promo_count,
                plans=plans_list,
            )
        )

    return result


@router.get("/{provider_id}", response_model=ProviderResponse)
def get_provider(provider_id: int, db: Session = DbSession):
    """Retrieve details for a specific AI provider."""
    prov = db.execute(select(Provider).where(Provider.id == provider_id)).scalar_one_or_none()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")

    promo_count = db.execute(
        select(func.count(Promotion.id)).where(Promotion.provider_id == prov.id)
    ).scalar_one()

    plans_list = [
        PlanResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            description=p.description,
            is_active=p.is_active,
        )
        for p in prov.plans
    ]

    return ProviderResponse(
        id=prov.id,
        name=prov.name,
        slug=prov.slug,
        description=prov.description,
        website_url=prov.website_url,
        is_active=prov.is_active,
        plans_count=len(plans_list),
        promotions_count=promo_count,
        plans=plans_list,
    )
