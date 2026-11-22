"""Comprehensive tests for Promotion Intelligence, link verification, Nigeria eligibility, and confidence scoring."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.enums import (
    EligibilityRuleType,
    LinkType,
    OfferType,
    PromotionStatus,
    SourceType,
)
from app.database.models.promotion import Promotion, PromotionLink
from app.database.models.provider import Plan, Provider
from app.database.models.source import DiscoveredItem, Source
from app.intelligence.authenticity import AuthenticityAssessor
from app.intelligence.eligibility import NigeriaEligibilityAssessor
from app.intelligence.engine import IntelligenceEngine
from app.intelligence.expiry import ExpiryAssessor
from app.intelligence.link_validator import SafeLinkValidator
from app.intelligence.scoring import ConfidenceScorer


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =====================================================================
# 1. SafeLinkValidator & SSRF Prevention Tests
# =====================================================================


def test_ssrf_prevention():
    validator = SafeLinkValidator()

    # Private and loopback IPv4
    assert validator.is_private_ip("127.0.0.1") is True
    assert validator.is_private_ip("10.0.0.1") is True
    assert validator.is_private_ip("192.168.1.50") is True
    assert validator.is_private_ip("172.16.0.5") is True
    assert validator.is_private_ip("169.254.169.254") is True

    # IPv6 loopback
    assert validator.is_private_ip("::1") is True

    # Public IP
    assert validator.is_private_ip("8.8.8.8") is False
    assert validator.is_private_ip("1.1.1.1") is False

    # SSRF check on hostname
    safe, err = validator.check_ssrf("127.0.0.1")
    assert safe is False
    assert "private" in err.lower() or "loopback" in err.lower()

    safe_local, _ = validator.check_ssrf("localhost")
    assert safe_local is False


def test_url_scheme_and_domain_safety():
    validator = SafeLinkValidator()

    # Disallow invalid schemes
    res_bad_scheme = validator.inspect_url("ftp://example.com/file.zip", perform_network_check=False)
    assert res_bad_scheme.is_safe is False
    assert "Unsupported URL scheme" in res_bad_scheme.risk_reasons[0]

    # Official Claude domain check
    res_claude = validator.inspect_url(
        "https://claude.ai/redeem/code123",
        provider_slug="anthropic",
        perform_network_check=False,
    )
    assert res_claude.is_safe is True
    assert res_claude.is_provider_domain is True
    assert res_claude.is_suspicious is False

    # Authorized partner domain (SheerID)
    res_sheer = validator.inspect_url(
        "https://services.sheerid.com/verify/student",
        provider_slug="openai",
        perform_network_check=False,
    )
    assert res_sheer.is_safe is True
    assert res_sheer.is_partner_domain is True

    # Phishing brand impersonation
    res_phish = validator.inspect_url(
        "https://claude-free-tokens.xyz/claim",
        provider_slug="anthropic",
        perform_network_check=False,
    )
    assert res_phish.is_suspicious is True
    assert any("impersonation" in r for r in res_phish.risk_reasons)

    # URL shortener detection
    res_short = validator.inspect_url(
        "https://bit.ly/claude-deal",
        provider_slug="anthropic",
        perform_network_check=False,
    )
    assert res_short.is_url_shortener is True


def test_safe_redirect_resolution_mocked():
    validator = SafeLinkValidator()

    mock_resp1 = MagicMock()
    mock_resp1.is_redirect = True
    mock_resp1.status_code = 302
    mock_resp1.headers = {"location": "https://claude.ai/pro-offer"}

    mock_resp2 = MagicMock()
    mock_resp2.is_redirect = False
    mock_resp2.status_code = 200
    mock_resp2.headers = {"content-type": "text/html"}

    with patch("httpx.Client.head", side_effect=[mock_resp1, mock_resp2]):
        result = validator.inspect_url(
            "https://tinyurl.com/claude3",
            provider_slug="anthropic",
            perform_network_check=True,
        )

        assert result.is_safe is True
        assert result.is_accessible is True
        assert result.final_domain == "claude.ai"
        assert result.is_provider_domain is True
        assert len(result.redirect_chain) == 1


# =====================================================================
# 2. AuthenticityAssessor Tests
# =====================================================================


def test_authenticity_evaluation():
    assessor = AuthenticityAssessor()

    # Legitimate official post
    legit_res = assessor.evaluate(
        title="Official Anthropic Student Grant for Claude Pro",
        content="Anthropic is offering students free Claude Pro access through sheerid.com verification.",
        source_type="rss",
        source_identifier="https://anthropic.com/news/feed",
        is_provider_domain=True,
    )
    assert legit_res.is_authentic is True
    assert legit_res.is_scam is False
    assert legit_res.authenticity_score >= 25
    assert len(legit_res.trust_signals) > 0

    # Scam with illicit pattern
    scam_res = assessor.evaluate(
        title="Free Claude Pro cracked accounts list",
        content="Shared account password login, download modded apk and bypass paywall via bin method.",
        source_type="telegram",
        source_identifier="@free_ai_logins",
    )
    assert scam_res.is_scam is True
    assert scam_res.is_authentic is False
    assert scam_res.authenticity_score == 0
    assert any("Illicit pattern" in r for r in scam_res.risk_signals)


# =====================================================================
# 3. NigeriaEligibilityAssessor Tests
# =====================================================================


def test_nigeria_eligibility_scenarios():
    assessor = NigeriaEligibilityAssessor()

    # Scenario A: Explicit exclusion of Nigeria
    res_excl = assessor.evaluate(
        provider_slug="xai",
        eligible_countries=["US", "CA"],
        excluded_countries=["NG"],
        account_requirements={},
        payment_required=False,
        raw_text="Offer only for North American residents, excludes Nigeria.",
    )
    assert res_excl.status == "ineligible"
    assert res_excl.is_nigeria_eligible is False
    assert any(r.rule_type == EligibilityRuleType.EXCLUDED_COUNTRY for r in res_excl.rules)

    # Scenario B: Global / Nigeria included with payment required
    res_ng_paid = assessor.evaluate(
        provider_slug="anthropic",
        eligible_countries=["GLOBAL"],
        excluded_countries=[],
        account_requirements={},
        payment_required=True,
        raw_text="Get 1 month free Claude Pro trial worldwide with valid credit card.",
    )
    assert res_ng_paid.status == "eligible"
    assert res_ng_paid.is_nigeria_eligible is True
    assert "Virtual USD Card" in res_ng_paid.payment_card_guidance
    assert any(r.rule_type == EligibilityRuleType.PAYMENT_METHOD_REQUIRED for r in res_ng_paid.rules)

    # Scenario C: Student verification
    res_student = assessor.evaluate(
        provider_slug="github",
        eligible_countries=["NG"],
        excluded_countries=[],
        account_requirements={"student_status": True},
        payment_required=False,
        raw_text="GitHub Student Developer Pack with free Copilot Pro for verified college students.",
    )
    assert res_student.status == "restricted"
    assert any(r.rule_type == EligibilityRuleType.STUDENT_VERIFICATION for r in res_student.rules)
    assert "SheerID" in res_student.risk_factors[0] or "student" in res_student.risk_factors[0].lower()


# =====================================================================
# 4. ExpiryAssessor Tests
# =====================================================================


def test_expiry_assessment():
    assessor = ExpiryAssessor()
    now = utc_now()

    # Active offer
    future_date = now + timedelta(days=10)
    res_active = assessor.evaluate(expires_at=future_date, first_discovered_at=now)
    assert res_active.is_expired is False
    assert res_active.urgency == "active"
    assert res_active.days_remaining == 9 or res_active.days_remaining == 10

    # Urgent offer (< 48 hours)
    urgent_date = now + timedelta(hours=24)
    res_urgent = assessor.evaluate(expires_at=urgent_date, first_discovered_at=now)
    assert res_urgent.is_expired is False
    assert res_urgent.urgency == "urgent"

    # Expired offer
    past_date = now - timedelta(hours=5)
    res_expired = assessor.evaluate(expires_at=past_date, first_discovered_at=now)
    assert res_expired.is_expired is True
    assert res_expired.urgency == "expired"

    # Inferred from text
    res_text = assessor.evaluate(
        expires_at=None,
        first_discovered_at=now,
        text_content="Sorry guys this deal is dead and code exhausted.",
    )
    assert res_text.is_expired is True
    assert res_text.urgency == "expired"


# =====================================================================
# 5. ConfidenceScorer Tests
# =====================================================================


def test_confidence_scorer_rubric():
    scorer = ConfidenceScorer()

    auth_good = MagicMock(authenticity_score=25, is_authentic=True, is_scam=False, trust_signals=["Official source"])
    link_good = MagicMock(
        is_safe=True,
        is_accessible=True,
        is_provider_domain=True,
        is_partner_domain=False,
        is_suspicious=False,
        final_domain="claude.ai",
        risk_reasons=[],
    )
    elig_good = MagicMock(is_nigeria_eligible=True, rules=[MagicMock()])
    expiry_active = MagicMock(is_expired=False, urgency="active")

    breakdown = scorer.calculate(
        authenticity=auth_good,
        link_inspection=link_good,
        eligibility=elig_good,
        expiry=expiry_active,
        discoveries_count=3,
        promo_code="STUDENT2026",
        duration_days=30,
        account_requirements={"new_accounts_only": True},
        first_discovered_at=utc_now(),
    )

    # Validate 100-point rubric breakdown
    assert breakdown.source_credibility == 25
    assert breakdown.redemption_destination == 25
    assert breakdown.terms_and_conditions >= 16
    assert breakdown.independent_corroboration == 15
    assert breakdown.freshness == 10
    assert breakdown.total_score >= 80
    assert breakdown.recommended_status == PromotionStatus.VERIFIED
    assert len(breakdown.reasons) == 5

    # Scam test drops score to invalid
    auth_scam = MagicMock(authenticity_score=0, is_authentic=False, is_scam=True, trust_signals=[])
    breakdown_scam = scorer.calculate(
        authenticity=auth_scam,
        link_inspection=link_good,
        eligibility=elig_good,
        expiry=expiry_active,
    )
    assert breakdown_scam.recommended_status == PromotionStatus.INVALID


# =====================================================================
# 6. Full IntelligenceEngine Integration Tests
# =====================================================================


def test_intelligence_engine_full_evaluation(db_session: Session):
    engine = IntelligenceEngine()

    provider = db_session.query(Provider).filter_by(slug="anthropic").first()
    plan = db_session.query(Plan).filter_by(slug="claude-pro").first()

    # Create a test promotion
    promo = Promotion(
        provider_id=provider.id,
        plan_id=plan.id,
        title="Claude Pro 1-Month Free Access for Students",
        description="Official student promotion for accredited students worldwide via Claude portal.",
        offer_type=OfferType.FREE_TRIAL,
        duration_days=30,
        promo_code="CLAUDE_CAMPUS_2026",
        eligible_countries=["GLOBAL", "NG"],
        excluded_countries=[],
        account_requirements={"student_status": True},
        payment_required=True,
        confidence_score=0,
        status=PromotionStatus.UNVERIFIED,
    )
    db_session.add(promo)
    db_session.flush()

    # Add promotion link
    link = PromotionLink(
        promotion_id=promo.id,
        original_url="https://claude.ai/promo/campus",
        normalized_url="https://claude.ai/promo/campus",
        destination_domain="claude.ai",
        link_type=LinkType.REDEMPTION,
        is_primary=True,
        is_active=True,
    )
    db_session.add(link)
    db_session.flush()

    # Execute intelligence evaluation (offline inspection for determinism)
    result = engine.evaluate_promotion(db=db_session, promotion=promo, perform_network_check=False)

    assert result.confidence_score >= 70
    assert promo.confidence_score == result.confidence_score
    assert promo.last_checked_at is not None

    # Verify VerificationCheck audit entries
    checks = promo.verification_checks
    check_types = {c.check_type for c in checks}
    assert "url_safety" in check_types
    assert "authenticity" in check_types
    assert "nigeria_eligibility" in check_types
    assert "expiry" in check_types
    assert "confidence_scoring" in check_types

    # Verify EligibilityRule persisted entries
    rule_types = {r.rule_type for r in promo.eligibility_rules}
    assert EligibilityRuleType.INCLUDED_COUNTRY in rule_types
    assert EligibilityRuleType.PAYMENT_METHOD_REQUIRED in rule_types


# =====================================================================
# 7. Promotions Intelligence API Endpoints Tests
# =====================================================================


def test_promotions_intelligence_api_endpoints(client: TestClient, db_session: Session):
    provider = db_session.query(Provider).filter_by(slug="openai").first()

    promo = Promotion(
        provider_id=provider.id,
        title="ChatGPT Plus 20% Discount",
        description="Special end-of-year discount for ChatGPT Plus subscribers worldwide.",
        offer_type=OfferType.DISCOUNT,
        discount_percentage=Decimal("20.00"),
        promo_code="GPT_PLUS_20",
        eligible_countries=["GLOBAL"],
        excluded_countries=[],
        account_requirements={},
        payment_required=True,
        confidence_score=40,
        status=PromotionStatus.UNVERIFIED,
    )
    db_session.add(promo)
    db_session.flush()

    link = PromotionLink(
        promotion_id=promo.id,
        original_url="https://chatgpt.com/promotions/eoy",
        normalized_url="https://chatgpt.com/promotions/eoy",
        destination_domain="chatgpt.com",
        link_type=LinkType.REDEMPTION,
        is_primary=True,
    )
    db_session.add(link)
    db_session.commit()

    # 1. Trigger verification check endpoint
    verify_resp = client.post(f"/api/v1/promotions/{promo.id}/verify?perform_network_check=false")
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["promotion_id"] == promo.id
    assert data["confidence_score"] > 50
    assert len(data["verification_checks"]) >= 4

    # 2. Get Nigerian eligibility details endpoint
    elig_resp = client.get(f"/api/v1/promotions/{promo.id}/eligibility")
    assert elig_resp.status_code == 200
    elig_data = elig_resp.json()
    assert elig_data["promotion_id"] == promo.id
    assert elig_data["is_nigeria_eligible"] is True
    assert "Virtual USD Card" in elig_data["payment_card_guidance"]

    # 3. List verification checks endpoint
    checks_resp = client.get(f"/api/v1/promotions/{promo.id}/verification-checks")
    assert checks_resp.status_code == 200
    checks_data = checks_resp.json()
    assert len(checks_data) >= 4
    assert checks_data[0]["status"] == "completed"

    # 4. List promotions with min_confidence filter
    list_filtered = client.get(f"/api/v1/promotions?min_confidence={data['confidence_score']}")
    assert list_filtered.status_code == 200
    promos = list_filtered.json()
    assert any(p["id"] == promo.id for p in promos)
