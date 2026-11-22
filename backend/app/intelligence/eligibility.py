"""Nigeria and regional eligibility assessment module for AI subscription deals."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.database.models.enums import EligibilityRuleType


@dataclass
class StructuredEligibilityRule:
    """Representation of an eligibility rule ready for database persistence."""

    rule_type: EligibilityRuleType
    country_code: Optional[str]
    description: str
    evidence_url: Optional[str] = None


@dataclass
class NigeriaEligibilityResult:
    """Outcome of evaluating regional usability and Nigerian banking compatibility."""

    status: str  # "eligible", "ineligible", "restricted", "unknown"
    is_nigeria_eligible: bool
    summary_notes: str
    payment_card_guidance: str
    rules: List[StructuredEligibilityRule] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)


# Providers with known specific policies regarding Nigerian billing or access
KNOWN_PROVIDER_NIGERIA_POLICIES = {
    "openai": {
        "access": "Full access in Nigeria.",
        "billing": "Requires international payment card. Local Naira debit cards fail CBN foreign limits; use a virtual USD card (Geegpay, Chipper, Payday) or Apple/Google Pay.",
    },
    "anthropic": {
        "access": "Claude Pro is officially supported in Nigeria.",
        "billing": "Requires an international credit/debit card enabled for USD transactions. Funded virtual dollar cards are recommended.",
    },
    "xai": {
        "access": "Grok available with X Premium globally.",
        "billing": "Subscription works via in-app purchase (Apple App Store / Google Play Store in NGN) or international card. Note: X Creator revenue/referral programs exclude Nigeria.",
    },
    "google": {
        "access": "Google One AI Premium supported in Nigeria.",
        "billing": "Can be billed directly in NGN via Google Play Store using domestic Nigerian bank cards, or via web using virtual USD card.",
    },
    "perplexity": {
        "access": "Perplexity Pro supported in Nigeria.",
        "billing": "Stripe checkout requires international payment card or PayPal; virtual USD cards work reliably.",
    },
    "cursor": {
        "access": "Cursor Pro accessible in Nigeria.",
        "billing": "Stripe payment requires an international USD card; virtual USD cards recommended.",
    },
    "github": {
        "access": "GitHub Copilot accessible globally.",
        "billing": "Student Developer Pack grants free Copilot Pro to enrolled students globally, including accredited Nigerian tertiary institutions.",
    },
}


class NigeriaEligibilityAssessor:
    """Assesses geographic and financial eligibility specifically for users in Nigeria."""

    def evaluate(
        self,
        provider_slug: str,
        eligible_countries: List[str],
        excluded_countries: List[str],
        account_requirements: dict,
        payment_required: Optional[bool],
        raw_text: str,
    ) -> NigeriaEligibilityResult:
        """Evaluate Nigerian eligibility and return structured assessment and rules."""
        raw_lower = raw_text.lower()
        rules: List[StructuredEligibilityRule] = []
        risk_factors: List[str] = []

        # 1. Geographic restriction analysis
        status = "unknown"

        upper_eligible = [c.upper() for c in eligible_countries]
        upper_excluded = [c.upper() for c in excluded_countries]

        # Check explicit exclusion
        if "NG" in upper_excluded or "NIGERIA" in upper_excluded:
            status = "ineligible"
            rules.append(
                StructuredEligibilityRule(
                    rule_type=EligibilityRuleType.EXCLUDED_COUNTRY,
                    country_code="NG",
                    description="Nigeria is explicitly listed as an excluded country for this promotion.",
                )
            )
            risk_factors.append("Promotion explicitly excludes users in Nigeria.")

        # Check explicit inclusion
        elif "NG" in upper_eligible or "NIGERIA" in upper_eligible or "GLOBAL" in upper_eligible:
            status = "eligible"
            rules.append(
                StructuredEligibilityRule(
                    rule_type=EligibilityRuleType.INCLUDED_COUNTRY,
                    country_code="NG",
                    description="Nigeria (or Global) is explicitly included in the promotional scope.",
                )
            )

        # Restrictive list omitting Nigeria
        elif upper_eligible and "NG" not in upper_eligible and "GLOBAL" not in upper_eligible:
            # If explicit countries like ["US", "CA", "UK"] are listed without NG
            status = "ineligible"
            allowed_str = ", ".join(upper_eligible)
            rules.append(
                StructuredEligibilityRule(
                    rule_type=EligibilityRuleType.EXCLUDED_COUNTRY,
                    country_code="NG",
                    description=f"Promotion is restricted only to {allowed_str}; Nigeria is not listed.",
                )
            )
            risk_factors.append(f"Geo-restricted to {allowed_str}.")

        else:
            # Check text indicators
            if re.search(r"\b(us\s+only|united\s+states\s+only|north\s+america\s+only|eu\s+only)\b", raw_lower):
                status = "ineligible"
                rules.append(
                    StructuredEligibilityRule(
                        rule_type=EligibilityRuleType.EXCLUDED_COUNTRY,
                        country_code="NG",
                        description="Offer terms mention regional restriction (e.g. US or EU only).",
                    )
                )
                risk_factors.append("Offer mentions US/EU only restriction.")
            elif re.search(r"\b(worldwide|globally|all\s+countries|anywhere)\b", raw_lower):
                status = "eligible"
                rules.append(
                    StructuredEligibilityRule(
                        rule_type=EligibilityRuleType.INCLUDED_COUNTRY,
                        country_code="NG",
                        description="Promotion text indicates worldwide/global availability.",
                    )
                )
            else:
                status = "unknown"

        # Special case: Grok referral programs often exclude Nigeria
        if provider_slug == "xai" and "referral" in raw_lower:
            status = "restricted"
            risk_factors.append("xAI referral/credit programs historically exclude Nigerian residents.")
            rules.append(
                StructuredEligibilityRule(
                    rule_type=EligibilityRuleType.OTHER,
                    country_code="NG",
                    description="xAI referral and affiliate compensation terms exclude participants in Nigeria.",
                )
            )

        # 2. Student Verification check
        if account_requirements.get("student_status") or re.search(r"\b(student|sheerid|unidays|\.edu)\b", raw_lower):
            if status == "eligible" or status == "unknown":
                status = "restricted"
            rules.append(
                StructuredEligibilityRule(
                    rule_type=EligibilityRuleType.STUDENT_VERIFICATION,
                    country_code=None,
                    description="Requires student identity verification (SheerID/UNiDAYS/.edu email). Nigerian university students may require manual student ID card validation.",
                )
            )
            risk_factors.append("Requires accredited student status; SheerID manual review may be needed for Nigerian universities.")

        # 3. New accounts requirement
        if account_requirements.get("new_accounts_only") or re.search(r"\b(new\s+(users?|accounts?|subscribers?)|first-time)\b", raw_lower):
            rules.append(
                StructuredEligibilityRule(
                    rule_type=EligibilityRuleType.NEW_ACCOUNTS_ONLY,
                    country_code=None,
                    description="Offer valid exclusively for newly registered accounts with no previous active subscription.",
                )
            )

        # 4. Payment card and banking feasibility for Nigeria
        provider_policy = KNOWN_PROVIDER_NIGERIA_POLICIES.get(provider_slug, {})
        base_billing_info = provider_policy.get(
            "billing",
            "International transaction capability required for USD checkouts.",
        )

        if payment_required is True:
            payment_guidance = (
                f"Credit/debit card required to activate offer. Local Nigerian Naira debit cards "
                f"(Verve/Mastercard/Visa) frequently fail on foreign USD payment gateways due to bank limits. "
                f"Use a funded Virtual USD Card (e.g., Geegpay, Chipper Cash, Payday, Eversend). {base_billing_info}"
            )
            rules.append(
                StructuredEligibilityRule(
                    rule_type=EligibilityRuleType.PAYMENT_METHOD_REQUIRED,
                    country_code="NG",
                    description="Payment card required for activation. Virtual USD card recommended for Nigerian users.",
                )
            )
        elif payment_required is False:
            payment_guidance = "No credit card or payment method required. Can be claimed directly without banking restrictions."
        else:
            payment_guidance = (
                f"Payment method requirement unconfirmed. If required: {base_billing_info}"
            )

        # Summary construction
        summary_notes = (
            f"Status: {status.upper()}. "
            + (f"Policy: {provider_policy.get('access', '')} " if provider_policy else "")
            + (f"Warnings: {'; '.join(risk_factors)}" if risk_factors else "No major regional blockers identified.")
        )

        return NigeriaEligibilityResult(
            status=status,
            is_nigeria_eligible=(status in ("eligible", "restricted", "unknown")),
            summary_notes=summary_notes,
            payment_card_guidance=payment_guidance,
            rules=rules,
            risk_factors=risk_factors,
        )
