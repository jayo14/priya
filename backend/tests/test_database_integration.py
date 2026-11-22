"""Comprehensive PostgreSQL database integration tests."""

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models.enums import (
    EligibilityRuleType,
    LinkType,
    NotificationStatus,
    NotificationType,
    OfferType,
    ProcessingStatus,
    PromotionStatus,
    SourceType,
)
from app.database.models.notification import Notification
from app.database.models.promotion import (
    Promotion,
    PromotionDiscovery,
)
from app.database.models.provider import Plan, Provider
from app.database.models.source import Source
from app.database.repositories.discovery_repo import DiscoveryRepository
from app.database.repositories.promotion_repo import PromotionRepository
from app.database.repositories.provider_repo import ProviderRepository
from app.database.repositories.source_repo import SourceRepository


def test_seeded_providers_and_plans(db_session: Session):
    """Verify that all seven canonical providers and their initial plans are present."""
    expected_providers = [
        "anthropic",
        "openai",
        "xai",
        "google",
        "perplexity",
        "cursor",
        "github",
    ]
    for slug in expected_providers:
        provider = ProviderRepository.get_by_slug(db_session, slug)
        assert provider is not None, f"Provider {slug} not found"
        assert provider.is_active is True
        plans = ProviderRepository.list_plans_by_provider(db_session, provider.id)
        assert len(plans) > 0, f"Provider {slug} has no seeded plans"


def test_unique_provider_slug_constraint(db_session: Session):
    """Attempting to create duplicate provider slug must raise IntegrityError."""
    duplicate = Provider(
        name="Anthropic Duplicate",
        slug="anthropic",  # Already exists
        is_active=True,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_plan_provider_relationship_and_cascade(db_session: Session):
    """Creating a custom provider and plan, verifying relationship and unique slug per provider."""
    provider = Provider(
        name="Test Labs",
        slug="test-labs",
        is_active=True,
    )
    db_session.add(provider)
    db_session.flush()

    plan1 = Plan(
        provider_id=provider.id,
        name="Test Pro",
        slug="pro",
        is_active=True,
    )
    db_session.add(plan1)
    db_session.flush()

    # Unique constraint within same provider: (provider_id, slug)
    plan_dup = Plan(
        provider_id=provider.id,
        name="Test Pro Again",
        slug="pro",
        is_active=True,
    )
    db_session.add(plan_dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_source_creation_and_uniqueness(db_session: Session):
    """Verify source creation and uniqueness on (source_type, identifier)."""
    source = SourceRepository.create(
        db=db_session,
        name="Claude AI Announcements",
        source_type=SourceType.TELEGRAM,
        identifier="@claude_ai_deals",
        url="https://t.me/claude_ai_deals",
        description="Public telegram channel",
    )
    assert source.id is not None
    assert source.identifier == "@claude_ai_deals"

    # Attempt duplicate identifier in same source_type
    with pytest.raises(IntegrityError):
        duplicate = Source(
            name="Another Duplicate Channel",
            source_type=SourceType.TELEGRAM,
            identifier="@claude_ai_deals",
            is_active=True,
        )
        db_session.add(duplicate)
        db_session.flush()
    db_session.rollback()


def test_discovered_item_persistence_and_duplicate_rejection(db_session: Session):
    """Verify discovered item persistence and rejection of duplicate external_id for same source."""
    source = SourceRepository.create(
        db=db_session,
        name="Reddit AI Deals",
        source_type=SourceType.REDDIT,
        identifier="r/ChatGPT",
    )

    item = DiscoveryRepository.create_item(
        db=db_session,
        source_id=source.id,
        external_id="post_9999",
        content="Free 3 months ChatGPT Plus promotion code link",
        content_type="reddit_post",
        title="ChatGPT Plus deal",
        author="deal_hunter",
        content_hash="abc123hash",
    )
    assert item.id is not None
    assert item.processing_status == ProcessingStatus.PENDING

    # Duplicate external_id on same source must fail
    with pytest.raises(IntegrityError):
        DiscoveryRepository.create_item(
            db=db_session,
            source_id=source.id,
            external_id="post_9999",
            content="Duplicate post content",
        )
    db_session.rollback()


def test_promotion_creation_and_confidence_constraint(db_session: Session):
    """Verify promotion persistence, relationships, and check constraint on confidence score [0, 100]."""
    openai = ProviderRepository.get_by_slug(db_session, "openai")
    assert openai is not None
    plus_plan = ProviderRepository.get_plan_by_slug(db_session, openai.id, "chatgpt-plus")
    assert plus_plan is not None

    promo = PromotionRepository.create_promotion(
        db=db_session,
        provider_id=openai.id,
        plan_id=plus_plan.id,
        title="OpenAI Spring Partner 1-Month Free Plus",
        offer_type=OfferType.FREE_TRIAL,
        duration_days=30,
        eligible_countries=["NG", "US", "GB"],
        confidence_score=85,
        status=PromotionStatus.LIKELY_VALID,
    )
    assert promo.id is not None
    assert promo.provider.slug == "openai"
    assert promo.plan.slug == "chatgpt-plus"
    assert "NG" in promo.eligible_countries

    # Confidence score > 100 violates CheckConstraint
    with pytest.raises(IntegrityError):
        invalid_promo = Promotion(
            provider_id=openai.id,
            title="Invalid Confidence Promo",
            confidence_score=150,  # Invalid!
        )
        db_session.add(invalid_promo)
        db_session.flush()
    db_session.rollback()


def test_promotion_multiple_discoveries_corroboration(db_session: Session):
    """Verify that multiple discovered items can associate with a single canonical promotion."""
    anthropic = ProviderRepository.get_by_slug(db_session, "anthropic")
    assert anthropic is not None

    source1 = SourceRepository.create(
        db=db_session,
        name="Telegram Channel A",
        source_type=SourceType.TELEGRAM,
        identifier="@deal_channel_a",
    )
    source2 = SourceRepository.create(
        db=db_session,
        name="Reddit Community B",
        source_type=SourceType.REDDIT,
        identifier="r/ClaudeAI",
    )

    item1 = DiscoveryRepository.create_item(
        db=db_session,
        source_id=source1.id,
        external_id="msg_101",
        content="Claude Pro discount announced on partner website",
    )
    item2 = DiscoveryRepository.create_item(
        db=db_session,
        source_id=source2.id,
        external_id="post_202",
        content="Corroborated: Claude Pro discount verified working",
    )

    promo = PromotionRepository.create_promotion(
        db=db_session,
        provider_id=anthropic.id,
        title="Claude Pro Partner Promo",
        offer_type=OfferType.DISCOUNT,
        discount_percentage=Decimal("50.00"),
    )

    # Associate both items to the same promotion
    assoc1 = PromotionRepository.associate_discovery(db_session, promo.id, item1.id)
    assoc2 = PromotionRepository.associate_discovery(db_session, promo.id, item2.id)

    assert assoc1.id is not None
    assert assoc2.id is not None

    # Retrieve and verify discoveries count
    retrieved = PromotionRepository.get_by_id(db_session, promo.id)
    assert retrieved is not None
    assert len(retrieved.discoveries) == 2

    # Prevent duplicate pairing
    with pytest.raises(IntegrityError):
        duplicate_assoc = PromotionDiscovery(
            promotion_id=promo.id,
            discovered_item_id=item1.id,
        )
        db_session.add(duplicate_assoc)
        db_session.flush()
    db_session.rollback()


def test_promotion_links_verification_checks_and_eligibility(db_session: Session):
    """Verify promotion links, historical verification checks, and eligibility rules."""
    perplexity = ProviderRepository.get_by_slug(db_session, "perplexity")
    assert perplexity is not None

    promo = PromotionRepository.create_promotion(
        db=db_session,
        provider_id=perplexity.id,
        title="Perplexity Pro 1-Year Student Offer",
        offer_type=OfferType.STUDENT_OFFER,
        duration_days=365,
    )

    # Add redemption and official links
    link1 = PromotionRepository.add_link(
        db=db_session,
        promotion_id=promo.id,
        original_url="https://perplexity.ai/backtoschool?ref=campus",
        normalized_url="https://perplexity.ai/backtoschool",
        destination_domain="perplexity.ai",
        link_type=LinkType.REDEMPTION,
        is_primary=True,
    )
    link2 = PromotionRepository.add_link(
        db=db_session,
        promotion_id=promo.id,
        original_url="https://x.com/perplexity_ai/status/12345",
        normalized_url="https://x.com/perplexity_ai/status/12345",
        destination_domain="x.com",
        link_type=LinkType.OFFICIAL_ANNOUNCEMENT,
        is_primary=False,
    )
    assert link1.is_primary is True
    assert link2.destination_domain == "x.com"

    # Add verification check history
    check = PromotionRepository.add_verification_check(
        db=db_session,
        promotion_id=promo.id,
        check_type="url_accessibility",
        result="pass",
        status="completed",
        details={"http_status": 200, "ssl_valid": True},
    )
    assert check.id is not None
    assert check.details["http_status"] == 200

    # Add eligibility rule
    rule = PromotionRepository.add_eligibility_rule(
        db=db_session,
        promotion_id=promo.id,
        rule_type=EligibilityRuleType.STUDENT_VERIFICATION,
        description="Requires active .edu email address or SheerID verification",
        country_code=None,
    )
    assert rule.id is not None
    assert rule.rule_type == EligibilityRuleType.STUDENT_VERIFICATION

    # Check notification record
    notif = Notification(
        promotion_id=promo.id,
        channel="telegram",
        notification_type=NotificationType.NEW_PROMOTION,
        status=NotificationStatus.PENDING,
        message="New 1-year Perplexity Pro student offer discovered!",
    )
    db_session.add(notif)
    db_session.flush()
    assert notif.id is not None

    # Verify everything reloads on promotion
    reloaded = PromotionRepository.get_by_id(db_session, promo.id)
    assert len(reloaded.links) == 2
    assert len(reloaded.verification_checks) == 1
    assert len(reloaded.eligibility_rules) == 1
    assert len(reloaded.notifications) == 1


def test_foreign_key_protection_on_provider_deletion(db_session: Session):
    """Deleting a provider with active promotions must be blocked by RESTRICT constraint."""
    cursor_prov = ProviderRepository.get_by_slug(db_session, "cursor")
    assert cursor_prov is not None

    promo = PromotionRepository.create_promotion(
        db=db_session,
        provider_id=cursor_prov.id,
        title="Cursor Pro 14-Day Free Trial",
        offer_type=OfferType.FREE_TRIAL,
    )
    assert promo.id is not None

    with pytest.raises(IntegrityError):
        db_session.delete(cursor_prov)
        db_session.flush()
    db_session.rollback()
