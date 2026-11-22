"""API endpoints for canonical promotions and extraction pipeline execution."""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import DbSession
from app.database.models.enums import OfferType, ProcessingStatus, PromotionStatus
from app.database.models.promotion import Promotion
from app.database.models.source import DiscoveredItem
from app.database.repositories.promotion_repo import PromotionRepository
from app.intelligence.engine import IntelligenceEngine
from app.processing.pipeline import PipelineStats, ProcessingPipeline

router = APIRouter(tags=["Promotions & Pipeline"])
pipeline = ProcessingPipeline()
intelligence_engine = IntelligenceEngine()


# --- Pydantic Schemas ---


class PromotionLinkResponse(BaseModel):
    id: int
    original_url: str
    normalized_url: str
    destination_domain: str
    link_type: str
    is_primary: bool

    model_config = {"from_attributes": True}


class PromotionResponse(BaseModel):
    id: int
    provider_id: int
    provider_slug: Optional[str] = None
    provider_name: Optional[str] = None
    plan_id: Optional[int]
    plan_slug: Optional[str] = None
    plan_name: Optional[str] = None
    title: str
    description: Optional[str]
    offer_type: str
    discount_percentage: Optional[Decimal]
    duration_days: Optional[int]
    promo_code: Optional[str]
    eligible_countries: List[str]
    excluded_countries: List[str]
    account_requirements: Dict[str, Any]
    payment_required: Optional[bool]
    status: str
    confidence_score: int
    first_discovered_at: str
    last_discovered_at: str
    discoveries_count: int
    links: List[PromotionLinkResponse]

    model_config = {"from_attributes": True}


class PipelineRunResponse(BaseModel):
    items_processed: int
    promotions_created: int
    promotions_corroborated: int
    irrelevant_count: int
    failed_count: int


class ProcessingStatsResponse(BaseModel):
    pending_items: int
    processing_items: int
    processed_items: int
    irrelevant_items: int
    failed_items: int
    total_canonical_promotions: int


class VerificationCheckResponse(BaseModel):
    id: int
    check_type: str
    result: str
    status: str
    details: Dict[str, Any]
    checked_at: str

    model_config = {"from_attributes": True}


class EligibilityRuleResponse(BaseModel):
    id: int
    rule_type: str
    country_code: Optional[str]
    description: str
    evidence_url: Optional[str]

    model_config = {"from_attributes": True}


class PromotionVerifyResponse(BaseModel):
    promotion_id: int
    confidence_score: int
    status: str
    is_safe: bool
    summary_reasons: Dict[str, str]
    verification_checks: List[VerificationCheckResponse]


class PromotionEligibilityResponse(BaseModel):
    promotion_id: int
    status: str
    is_nigeria_eligible: bool
    payment_card_guidance: str
    summary_notes: str
    rules: List[EligibilityRuleResponse]


# --- Endpoints ---


@router.post("/processing/run", response_model=PipelineRunResponse)
def run_processing_pipeline(
    limit: int = Query(50, ge=1, le=200),
    db: Session = DbSession,
):
    """Run deterministic extraction pipeline on pending discovered items."""
    stats: PipelineStats = pipeline.process_pending_items(db, limit=limit)
    return PipelineRunResponse(
        items_processed=stats.items_processed,
        promotions_created=stats.promotions_created,
        promotions_corroborated=stats.promotions_corroborated,
        irrelevant_count=stats.irrelevant_count,
        failed_count=stats.failed_count,
    )


@router.get("/processing/stats", response_model=ProcessingStatsResponse)
def get_processing_stats(
    db: Session = DbSession,
):
    """Retrieve counts of items across processing lifecycle stages."""
    counts = dict(
        db.execute(
            select(DiscoveredItem.processing_status, func.count(DiscoveredItem.id)).group_by(
                DiscoveredItem.processing_status
            )
        ).all()
    )

    promo_count = db.execute(select(func.count(Promotion.id))).scalar_one()

    return ProcessingStatsResponse(
        pending_items=counts.get(ProcessingStatus.PENDING, 0),
        processing_items=counts.get(ProcessingStatus.PROCESSING, 0),
        processed_items=counts.get(ProcessingStatus.PROCESSED, 0),
        irrelevant_items=counts.get(ProcessingStatus.IRRELEVANT, 0),
        failed_items=counts.get(ProcessingStatus.FAILED, 0),
        total_canonical_promotions=promo_count,
    )


@router.get("/promotions", response_model=List[PromotionResponse])
def list_promotions(
    provider_id: Optional[int] = None,
    status: Optional[PromotionStatus] = None,
    offer_type: Optional[OfferType] = None,
    min_confidence: Optional[int] = Query(None, ge=0, le=100),
    nigeria_eligible: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = DbSession,
):
    """List canonical promotions with optional provider, status, or regional filters."""
    stmt = select(Promotion)
    if provider_id:
        stmt = stmt.where(Promotion.provider_id == provider_id)
    if status:
        stmt = stmt.where(Promotion.status == status)
    if offer_type:
        stmt = stmt.where(Promotion.offer_type == offer_type)
    if min_confidence is not None:
        stmt = stmt.where(Promotion.confidence_score >= min_confidence)

    stmt = stmt.order_by(Promotion.first_discovered_at.desc()).offset(skip).limit(limit)
    promotions = list(db.execute(stmt).scalars().all())

    # Build response objects with relationships and Nigerian filter
    result: List[PromotionResponse] = []
    for promo in promotions:
        upper_el = [c.upper() for c in promo.eligible_countries]
        upper_ex = [c.upper() for c in promo.excluded_countries]
        has_ng = ("NG" not in upper_ex) and ("NG" in upper_el or "GLOBAL" in upper_el or not upper_el)
        if nigeria_eligible is not None and has_ng != nigeria_eligible:
            continue

        result.append(
            PromotionResponse(
                id=promo.id,
                provider_id=promo.provider_id,
                provider_slug=promo.provider.slug if promo.provider else None,
                provider_name=promo.provider.name if promo.provider else None,
                plan_id=promo.plan_id,
                plan_slug=promo.plan.slug if promo.plan else None,
                plan_name=promo.plan.name if promo.plan else None,
                title=promo.title,
                description=promo.description,
                offer_type=promo.offer_type.value,
                discount_percentage=promo.discount_percentage,
                duration_days=promo.duration_days,
                promo_code=promo.promo_code,
                eligible_countries=promo.eligible_countries,
                excluded_countries=promo.excluded_countries,
                account_requirements=promo.account_requirements,
                payment_required=promo.payment_required,
                status=promo.status.value,
                confidence_score=promo.confidence_score,
                first_discovered_at=promo.first_discovered_at.isoformat(),
                last_discovered_at=promo.last_discovered_at.isoformat(),
                discoveries_count=len(promo.discoveries),
                links=[
                    PromotionLinkResponse(
                        id=lnk.id,
                        original_url=lnk.original_url,
                        normalized_url=lnk.normalized_url,
                        destination_domain=lnk.destination_domain,
                        link_type=lnk.link_type.value,
                        is_primary=lnk.is_primary,
                    )
                    for lnk in promo.links
                ],
            )
        )
    return result


@router.get("/promotions/{promotion_id}", response_model=PromotionResponse)
def get_promotion(
    promotion_id: int,
    db: Session = DbSession,
):
    """Get single canonical promotion details by ID."""
    promo = PromotionRepository.get_by_id(db, promotion_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    return PromotionResponse(
        id=promo.id,
        provider_id=promo.provider_id,
        provider_slug=promo.provider.slug if promo.provider else None,
        provider_name=promo.provider.name if promo.provider else None,
        plan_id=promo.plan_id,
        plan_slug=promo.plan.slug if promo.plan else None,
        plan_name=promo.plan.name if promo.plan else None,
        title=promo.title,
        description=promo.description,
        offer_type=promo.offer_type.value,
        discount_percentage=promo.discount_percentage,
        duration_days=promo.duration_days,
        promo_code=promo.promo_code,
        eligible_countries=promo.eligible_countries,
        excluded_countries=promo.excluded_countries,
        account_requirements=promo.account_requirements,
        payment_required=promo.payment_required,
        status=promo.status.value,
        confidence_score=promo.confidence_score,
        first_discovered_at=promo.first_discovered_at.isoformat(),
        last_discovered_at=promo.last_discovered_at.isoformat(),
        discoveries_count=len(promo.discoveries),
        links=[
            PromotionLinkResponse(
                id=lnk.id,
                original_url=lnk.original_url,
                normalized_url=lnk.normalized_url,
                destination_domain=lnk.destination_domain,
                link_type=lnk.link_type.value,
                is_primary=lnk.is_primary,
            )
            for lnk in promo.links
        ],
    )


@router.post("/promotions/{promotion_id}/verify", response_model=PromotionVerifyResponse)
def verify_promotion(
    promotion_id: int,
    perform_network_check: bool = Query(
        False, description="Perform live HTTP redirect and network validation"
    ),
    db: Session = DbSession,
):
    """Run full promotion intelligence verification checks, update scoring and audit trail."""
    promo = PromotionRepository.get_by_id(db, promotion_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    res = intelligence_engine.evaluate_promotion(
        db=db, promotion=promo, perform_network_check=perform_network_check
    )
    db.commit()
    db.refresh(promo)

    return PromotionVerifyResponse(
        promotion_id=promo.id,
        confidence_score=res.confidence_score,
        status=res.status.value,
        is_safe=not res.authenticity.is_scam
        and (not res.link_inspections or res.link_inspections[0].is_safe),
        summary_reasons=res.breakdown.reasons,
        verification_checks=[
            VerificationCheckResponse(
                id=c.id,
                check_type=c.check_type,
                result=c.result,
                status=c.status,
                details=c.details,
                checked_at=c.checked_at.isoformat(),
            )
            for c in promo.verification_checks
        ],
    )


@router.get(
    "/promotions/{promotion_id}/eligibility",
    response_model=PromotionEligibilityResponse,
)
def get_promotion_eligibility(
    promotion_id: int,
    db: Session = DbSession,
):
    """Retrieve detailed regional and Nigerian banking usability rules for a promotion."""
    promo = PromotionRepository.get_by_id(db, promotion_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    provider_slug = promo.provider.slug if promo.provider else "unknown"
    full_text = f"{promo.title}\n{promo.description or ''}"
    res = intelligence_engine.eligibility_assessor.evaluate(
        provider_slug=provider_slug,
        eligible_countries=promo.eligible_countries,
        excluded_countries=promo.excluded_countries,
        account_requirements=promo.account_requirements,
        payment_required=promo.payment_required,
        raw_text=full_text,
    )

    return PromotionEligibilityResponse(
        promotion_id=promo.id,
        status=res.status,
        is_nigeria_eligible=res.is_nigeria_eligible,
        payment_card_guidance=res.payment_card_guidance,
        summary_notes=res.summary_notes,
        rules=[
            EligibilityRuleResponse(
                id=r.id,
                rule_type=r.rule_type.value,
                country_code=r.country_code,
                description=r.description,
                evidence_url=r.evidence_url,
            )
            for r in promo.eligibility_rules
        ],
    )


@router.get(
    "/promotions/{promotion_id}/verification-checks",
    response_model=List[VerificationCheckResponse],
)
def list_promotion_verification_checks(
    promotion_id: int,
    db: Session = DbSession,
):
    """Retrieve historical verification audit checks for a promotion."""
    promo = PromotionRepository.get_by_id(db, promotion_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    checks = sorted(promo.verification_checks, key=lambda x: x.checked_at, reverse=True)
    return [
        VerificationCheckResponse(
            id=c.id,
            check_type=c.check_type,
            result=c.result,
            status=c.status,
            details=c.details,
            checked_at=c.checked_at.isoformat(),
        )
        for c in checks
    ]
