"""Deterministic 100-point confidence scoring algorithm and status evaluation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from app.database.models.enums import PromotionStatus
from app.intelligence.authenticity import AuthenticityResult
from app.intelligence.eligibility import NigeriaEligibilityResult
from app.intelligence.expiry import ExpiryResult
from app.intelligence.link_validator import LinkInspectionResult


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of the 100-point confidence score with reasoning."""

    source_credibility: int = 0  # 0 - 30
    redemption_destination: int = 0  # 0 - 25
    terms_and_conditions: int = 0  # 0 - 20
    independent_corroboration: int = 0  # 0 - 15
    freshness: int = 0  # 0 - 10
    total_score: int = 0  # 0 - 100
    recommended_status: PromotionStatus = PromotionStatus.UNVERIFIED
    reasons: Dict[str, str] = field(default_factory=dict)


class ConfidenceScorer:
    """Scores evidence quality and authenticity on a transparent 100-point rubric."""

    def calculate(
        self,
        authenticity: AuthenticityResult,
        link_inspection: Optional[LinkInspectionResult],
        eligibility: NigeriaEligibilityResult,
        expiry: ExpiryResult,
        discoveries_count: int = 1,
        promo_code: Optional[str] = None,
        duration_days: Optional[int] = None,
        discount_percentage: Optional[float] = None,
        account_requirements: Optional[dict] = None,
        first_discovered_at: Optional[datetime] = None,
    ) -> ScoreBreakdown:
        """Compute the 100-point score and determine the appropriate lifecycle status."""
        reasons: Dict[str, str] = {}

        # 1. Source Credibility (0 to 30)
        source_pts = authenticity.authenticity_score
        if authenticity.is_scam:
            source_pts = 0
            reasons["source_credibility"] = "Illicit / scam patterns detected; credibility reduced to zero."
        elif authenticity.trust_signals:
            reasons["source_credibility"] = "; ".join(authenticity.trust_signals)
        else:
            reasons["source_credibility"] = "Standard community source; baseline credibility."

        # 2. Redemption Destination (0 to 25)
        dest_pts = 0
        if link_inspection:
            if not link_inspection.is_safe:
                dest_pts = 0
                reasons["redemption_destination"] = f"Unsafe destination: {'; '.join(link_inspection.risk_reasons)}"
            elif link_inspection.is_provider_domain:
                dest_pts = 25
                reasons["redemption_destination"] = (
                    f"Destination '{link_inspection.final_domain}' is an official AI provider domain."
                )
            elif link_inspection.is_partner_domain:
                dest_pts = 20
                reasons["redemption_destination"] = (
                    f"Destination '{link_inspection.final_domain}' is an authorized educational / partner portal."
                )
            elif link_inspection.is_suspicious:
                dest_pts = 0
                reasons["redemption_destination"] = (
                    f"Suspicious destination domain: {'; '.join(link_inspection.risk_reasons)}"
                )
            elif link_inspection.is_accessible:
                dest_pts = 10
                reasons["redemption_destination"] = (
                    f"Destination '{link_inspection.final_domain}' is accessible but not an official provider domain."
                )
            else:
                dest_pts = 5
                reasons["redemption_destination"] = "Destination URL could not be confirmed as active."
        else:
            dest_pts = 0
            reasons["redemption_destination"] = "No redemption URL provided."

        # 3. Terms & Conditions Clarity (0 to 20)
        terms_pts = 0
        terms_notes = []

        if promo_code:
            terms_pts += 6
            terms_notes.append("Explicit promotional code provided")

        if duration_days:
            terms_pts += 6
            terms_notes.append(f"Clear duration specified ({duration_days} days)")
        elif discount_percentage is not None:
            terms_pts += 6
            terms_notes.append(f"Clear discount percentage specified ({discount_percentage}%)")

        if account_requirements:
            terms_pts += 4
            terms_notes.append("Structured account requirements detailed")

        if eligibility.rules:
            terms_pts += 4
            terms_notes.append(f"{len(eligibility.rules)} eligibility rules documented")

        # Clamp terms points to 20
        terms_pts = min(20, terms_pts)
        if not terms_notes:
            terms_pts = 3
            terms_notes.append("Basic promotional text without explicit parameters")
        reasons["terms_and_conditions"] = "; ".join(terms_notes)

        # 4. Independent Corroboration (0 to 15)
        if discoveries_count >= 3:
            corrob_pts = 15
            reasons["independent_corroboration"] = (
                f"Strong corroboration across {discoveries_count} independent sources."
            )
        elif discoveries_count == 2:
            corrob_pts = 10
            reasons["independent_corroboration"] = "Corroborated across 2 separate sources."
        else:
            corrob_pts = 5
            reasons["independent_corroboration"] = "Single source discovery."

        # 5. Freshness (0 to 10)
        now = utc_now()
        disc_at = first_discovered_at or now
        if disc_at.tzinfo is None:
            disc_at = disc_at.replace(tzinfo=timezone.utc)
        age_hours = (now - disc_at).total_seconds() / 3600.0

        if age_hours <= 24:
            fresh_pts = 10
            reasons["freshness"] = "Discovered within the last 24 hours."
        elif age_hours <= 72:
            fresh_pts = 7
            reasons["freshness"] = "Discovered within the last 3 days."
        elif age_hours <= 168:
            fresh_pts = 5
            reasons["freshness"] = "Discovered within the past week."
        elif age_hours <= 720:
            fresh_pts = 3
            reasons["freshness"] = "Discovered within the past month."
        else:
            fresh_pts = 1
            reasons["freshness"] = "Offer is over one month old."

        # Total Calculation
        total = source_pts + dest_pts + terms_pts + corrob_pts + fresh_pts
        total = max(0, min(100, total))

        # Status determination
        if authenticity.is_scam or (link_inspection and not link_inspection.is_safe):
            rec_status = PromotionStatus.INVALID
        elif expiry.is_expired:
            rec_status = PromotionStatus.EXPIRED
        elif not eligibility.is_nigeria_eligible:
            rec_status = PromotionStatus.RESTRICTED
        elif total >= 75 and (link_inspection and link_inspection.is_provider_domain):
            rec_status = PromotionStatus.VERIFIED
        elif total >= 50:
            rec_status = PromotionStatus.LIKELY_VALID
        else:
            rec_status = PromotionStatus.UNVERIFIED

        return ScoreBreakdown(
            source_credibility=source_pts,
            redemption_destination=dest_pts,
            terms_and_conditions=terms_pts,
            independent_corroboration=corrob_pts,
            freshness=fresh_pts,
            total_score=total,
            recommended_status=rec_status,
            reasons=reasons,
        )
