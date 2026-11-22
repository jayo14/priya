"""Promotion Intelligence Engine coordinating verification, eligibility, and scoring."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.logging import setup_logging
from app.database.models.enums import LinkType, PromotionStatus
from app.database.models.promotion import (
    EligibilityRule,
    Promotion,
    PromotionLink,
    VerificationCheck,
)
from app.intelligence.authenticity import AuthenticityAssessor, AuthenticityResult
from app.intelligence.eligibility import (
    NigeriaEligibilityAssessor,
    NigeriaEligibilityResult,
)
from app.intelligence.expiry import ExpiryAssessor, ExpiryResult
from app.intelligence.link_validator import LinkInspectionResult, SafeLinkValidator
from app.intelligence.scoring import ConfidenceScorer, ScoreBreakdown

logger = setup_logging()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class IntelligenceEvaluationResult:
    """Consolidated result of running the intelligence engine on a promotion."""

    promotion_id: int
    confidence_score: int
    status: PromotionStatus
    breakdown: ScoreBreakdown
    authenticity: AuthenticityResult
    eligibility: NigeriaEligibilityResult
    expiry: ExpiryResult
    link_inspections: List[LinkInspectionResult] = field(default_factory=list)


class IntelligenceEngine:
    """Evaluates promotions against safety, authenticity, Nigerian usability, and confidence."""

    def __init__(
        self,
        link_validator: Optional[SafeLinkValidator] = None,
        authenticity_assessor: Optional[AuthenticityAssessor] = None,
        eligibility_assessor: Optional[NigeriaEligibilityAssessor] = None,
        expiry_assessor: Optional[ExpiryAssessor] = None,
        scorer: Optional[ConfidenceScorer] = None,
    ):
        self.link_validator = link_validator or SafeLinkValidator()
        self.authenticity_assessor = authenticity_assessor or AuthenticityAssessor()
        self.eligibility_assessor = eligibility_assessor or NigeriaEligibilityAssessor()
        self.expiry_assessor = expiry_assessor or ExpiryAssessor()
        self.scorer = scorer or ConfidenceScorer()

    def evaluate_promotion(
        self,
        db: Session,
        promotion: Promotion,
        perform_network_check: bool = True,
    ) -> IntelligenceEvaluationResult:
        """Run all evaluation stages on a promotion and persist verification audits."""
        provider_slug = promotion.provider.slug if promotion.provider else "unknown"

        # 1. URL Safety & Destination Inspection
        primary_link: Optional[PromotionLink] = None
        for link in promotion.links:
            if link.is_primary or link.link_type == LinkType.REDEMPTION:
                primary_link = link
                break
        if not primary_link and promotion.links:
            primary_link = promotion.links[0]

        link_inspections: List[LinkInspectionResult] = []
        primary_inspection: Optional[LinkInspectionResult] = None

        if primary_link:
            inspection = self.link_validator.inspect_url(
                url=primary_link.original_url,
                provider_slug=provider_slug,
                perform_network_check=perform_network_check,
            )
            link_inspections.append(inspection)
            primary_inspection = inspection

            # Update link record attributes
            primary_link.normalized_url = inspection.final_url
            primary_link.destination_domain = inspection.final_domain
            primary_link.is_active = inspection.is_accessible

            # Record VerificationCheck for link safety
            link_result_status = "pass" if inspection.is_safe and inspection.is_accessible else "warning"
            if not inspection.is_safe or inspection.is_suspicious:
                link_result_status = "fail"

            db.add(
                VerificationCheck(
                    promotion_id=promotion.id,
                    check_type="url_safety",
                    result=link_result_status,
                    status="completed",
                    details={
                        "original_url": inspection.original_url,
                        "final_url": inspection.final_url,
                        "final_domain": inspection.final_domain,
                        "is_safe": inspection.is_safe,
                        "is_accessible": inspection.is_accessible,
                        "is_provider_domain": inspection.is_provider_domain,
                        "is_partner_domain": inspection.is_partner_domain,
                        "is_suspicious": inspection.is_suspicious,
                        "redirect_chain": inspection.redirect_chain,
                        "risk_reasons": inspection.risk_reasons,
                    },
                    checked_at=utc_now(),
                )
            )

        # 2. Authenticity Assessment
        # Collect text from discoveries or promotion description
        text_samples = [promotion.title, promotion.description or ""]
        source_type = None
        source_ident = None

        if promotion.discoveries:
            first_disc = promotion.discoveries[0].discovered_item
            if first_disc:
                text_samples.append(first_disc.content)
                if first_disc.source:
                    source_type = first_disc.source.source_type.value
                    source_ident = first_disc.source.identifier

        full_text = "\n".join(text_samples)

        authenticity_res = self.authenticity_assessor.evaluate(
            title=promotion.title,
            content=full_text,
            source_type=source_type,
            source_identifier=source_ident,
            link_inspection=primary_inspection,
        )

        db.add(
            VerificationCheck(
                promotion_id=promotion.id,
                check_type="authenticity",
                result="fail" if authenticity_res.is_scam else ("pass" if authenticity_res.is_authentic else "warning"),
                status="completed",
                details={
                    "is_authentic": authenticity_res.is_authentic,
                    "is_scam": authenticity_res.is_scam,
                    "authenticity_score": authenticity_res.authenticity_score,
                    "trust_signals": authenticity_res.trust_signals,
                    "risk_signals": authenticity_res.risk_signals,
                },
                checked_at=utc_now(),
            )
        )

        # 3. Nigerian Regional & Banking Eligibility
        eligibility_res = self.eligibility_assessor.evaluate(
            provider_slug=provider_slug,
            eligible_countries=promotion.eligible_countries,
            excluded_countries=promotion.excluded_countries,
            account_requirements=promotion.account_requirements,
            payment_required=promotion.payment_required,
            raw_text=full_text,
        )

        # Clear existing rules and persist new evaluated rules
        for rule_data in eligibility_res.rules:
            # Check if matching rule already exists
            exists = any(
                r.rule_type == rule_data.rule_type
                and r.country_code == rule_data.country_code
                and r.description == rule_data.description
                for r in promotion.eligibility_rules
            )
            if not exists:
                promotion.eligibility_rules.append(
                    EligibilityRule(
                        promotion_id=promotion.id,
                        rule_type=rule_data.rule_type,
                        country_code=rule_data.country_code,
                        description=rule_data.description,
                        evidence_url=rule_data.evidence_url,
                        created_at=utc_now(),
                    )
                )

        db.add(
            VerificationCheck(
                promotion_id=promotion.id,
                check_type="nigeria_eligibility",
                result="pass" if eligibility_res.is_nigeria_eligible else "fail",
                status="completed",
                details={
                    "status": eligibility_res.status,
                    "is_nigeria_eligible": eligibility_res.is_nigeria_eligible,
                    "payment_card_guidance": eligibility_res.payment_card_guidance,
                    "summary_notes": eligibility_res.summary_notes,
                    "risk_factors": eligibility_res.risk_factors,
                },
                checked_at=utc_now(),
            )
        )

        # 4. Expiry Assessment
        expiry_res = self.expiry_assessor.evaluate(
            expires_at=promotion.expires_at,
            first_discovered_at=promotion.first_discovered_at,
            text_content=full_text,
        )

        if expiry_res.expires_at and not promotion.expires_at:
            promotion.expires_at = expiry_res.expires_at

        db.add(
            VerificationCheck(
                promotion_id=promotion.id,
                check_type="expiry",
                result="fail" if expiry_res.is_expired else "pass",
                status="completed",
                details={
                    "is_expired": expiry_res.is_expired,
                    "urgency": expiry_res.urgency,
                    "days_remaining": expiry_res.days_remaining,
                    "explanation": expiry_res.explanation,
                },
                checked_at=utc_now(),
            )
        )

        # 5. Dynamic Confidence Scoring & Status Recommendation
        score_breakdown = self.scorer.calculate(
            authenticity=authenticity_res,
            link_inspection=primary_inspection,
            eligibility=eligibility_res,
            expiry=expiry_res,
            discoveries_count=len(promotion.discoveries) or 1,
            promo_code=promotion.promo_code,
            duration_days=promotion.duration_days,
            discount_percentage=float(promotion.discount_percentage) if promotion.discount_percentage else None,
            account_requirements=promotion.account_requirements,
            first_discovered_at=promotion.first_discovered_at,
        )

        # Update Promotion state
        promotion.confidence_score = score_breakdown.total_score
        promotion.status = score_breakdown.recommended_status
        promotion.last_checked_at = utc_now()

        db.add(
            VerificationCheck(
                promotion_id=promotion.id,
                check_type="confidence_scoring",
                result="pass" if score_breakdown.total_score >= 50 else "warning",
                status="completed",
                details={
                    "total_score": score_breakdown.total_score,
                    "recommended_status": score_breakdown.recommended_status.value,
                    "source_credibility": score_breakdown.source_credibility,
                    "redemption_destination": score_breakdown.redemption_destination,
                    "terms_and_conditions": score_breakdown.terms_and_conditions,
                    "independent_corroboration": score_breakdown.independent_corroboration,
                    "freshness": score_breakdown.freshness,
                    "reasons": score_breakdown.reasons,
                },
                checked_at=utc_now(),
            )
        )

        db.flush()

        logger.info(
            f"Promotion #{promotion.id} evaluated: Score={score_breakdown.total_score}, Status={score_breakdown.recommended_status.value}"
        )

        return IntelligenceEvaluationResult(
            promotion_id=promotion.id,
            confidence_score=score_breakdown.total_score,
            status=score_breakdown.recommended_status,
            breakdown=score_breakdown,
            authenticity=authenticity_res,
            eligibility=eligibility_res,
            expiry=expiry_res,
            link_inspections=link_inspections,
        )
