"""Comprehensive unit and integration tests for Phase 3 Extraction & Classification Engine."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.enums import OfferType, ProcessingStatus, SourceType
from app.database.repositories.discovery_repo import DiscoveryRepository
from app.database.repositories.source_repo import SourceRepository
from app.processing.classifier import EntityClassifier
from app.processing.extractor import OfferExtractor
from app.processing.filters import ContentFilter
from app.processing.normalizer import (
    extract_domain,
    extract_urls,
    normalize_text,
    normalize_url,
)
from app.processing.pipeline import ProcessingPipeline


def test_normalizer_text_and_urls():
    """Verify text entity decoding, unicode cleanup, and URL tracking removal."""
    raw_text = "Get &amp;quot;Claude Pro&amp;quot; 50% off! Visit https://claude.ai/redeem?utm_source=twitter&fbclid=12345"
    cleaned = normalize_text(raw_text)
    assert 'Get "Claude Pro" 50% off!' in cleaned

    urls = extract_urls(cleaned)
    assert len(urls) == 1
    raw_url = urls[0]
    assert "utm_source" in raw_url

    norm_url = normalize_url(raw_url)
    assert "utm_source" not in norm_url
    assert "fbclid" not in norm_url
    assert norm_url == "https://claude.ai/redeem"

    domain = extract_domain(norm_url)
    assert domain == "claude.ai"


def test_content_filter_positive_and_negative():
    """Verify promotional keyword detection and illicit account trading rejection."""
    content_filter = ContentFilter()

    # 1. Genuine promotional post
    deal_text = "Anthropic announces special offer: 3 months free Claude Pro for developers!"
    res1 = content_filter.evaluate("Claude Deal", deal_text)
    assert res1.is_relevant is True
    assert res1.is_spam_or_illicit is False
    assert res1.relevance_score >= 0.5
    assert len(res1.matched_keywords) > 0

    # 2. General non-deal chatter
    chat_text = "I really enjoy writing python code with Claude 3.5 Sonnet. How do you format prompts?"
    res2 = content_filter.evaluate("Question about prompt formatting", chat_text)
    assert res2.is_relevant is False
    assert res2.is_spam_or_illicit is False
    assert res2.rejection_reason is not None

    # 3. Illicit account trading / scam attempt
    scam_text = "DM to buy cheap Claude accounts! Selling shared chatgpt accounts with email:pass instant delivery."
    res3 = content_filter.evaluate("Accounts for sale", scam_text)
    assert res3.is_relevant is False
    assert res3.is_spam_or_illicit is True
    assert "illicit account trading" in res3.rejection_reason.lower()


def test_entity_classifier(db_session: Session):
    """Verify deterministic provider, plan, and offer type identification."""
    classifier = EntityClassifier()

    # Anthropic + Claude Pro
    res_claude = classifier.classify(
        db_session, "Claude Pro Offer", "Get 3 months free Claude Pro subscription!"
    )
    assert res_claude.provider_slug == "anthropic"
    assert res_claude.plan_slug == "claude-pro"
    assert res_claude.offer_type == OfferType.FREE_SUBSCRIPTION

    # OpenAI + ChatGPT Plus
    res_openai = classifier.classify(
        db_session, "OpenAI Promo", "Use promo code to get 50% discount on ChatGPT Plus."
    )
    assert res_openai.provider_slug == "openai"
    assert res_openai.plan_slug == "chatgpt-plus"
    assert res_openai.offer_type == OfferType.DISCOUNT

    # Perplexity Student Offer
    res_pplx = classifier.classify(
        db_session, "Perplexity Deal", "Free 1 year Perplexity Pro for students with university email."
    )
    assert res_pplx.provider_slug == "perplexity"
    assert res_pplx.plan_slug == "perplexity-pro"
    assert res_pplx.offer_type == OfferType.STUDENT_OFFER

    # Cursor Pro Free Trial
    res_cursor = classifier.classify(
        db_session, "Cursor Trial", "New 14 days free trial available on Cursor Pro editor!"
    )
    assert res_cursor.provider_slug == "cursor"
    assert res_cursor.plan_slug == "cursor-pro"
    assert res_cursor.offer_type == OfferType.FREE_TRIAL


def test_offer_extractor(db_session: Session):
    """Verify extraction of promo codes, discounts, duration, and countries."""
    source = SourceRepository.create(
        db=db_session,
        name="Test Extraction Source",
        source_type=SourceType.TELEGRAM,
        identifier="@test_extraction",
    )

    item = DiscoveryRepository.create_item(
        db=db_session,
        source_id=source.id,
        external_id="tg_ext_1",
        title="OpenAI Spring Partner Promo",
        content="""
        Exclusive partner offer: Get 3 months free ChatGPT Plus!
        Use code: SPRINGAI2026
        Link: https://chatgpt.com/redeem?code=SPRINGAI2026&utm_campaign=partner
        Eligible countries include Nigeria, United States, and Canada.
        No credit card required for activation. New accounts only.
        """,
    )

    extractor = OfferExtractor()
    extracted = extractor.extract(db_session, item)

    assert extracted is not None
    assert extracted.promo_code == "SPRINGAI2026"
    assert extracted.duration_days == 90  # 3 months * 30
    assert extracted.payment_required is False
    assert "NG" in extracted.eligible_countries
    assert "US" in extracted.eligible_countries
    assert extracted.account_requirements.get("new_accounts_only") is True
    assert extracted.destination_domain == "chatgpt.com"
    assert extracted.normalized_url == "https://chatgpt.com/redeem?code=SPRINGAI2026"
    assert extracted.confidence_score >= 70


def test_pipeline_deduplication_and_corroboration(db_session: Session):
    """Verify that multiple independent discoveries corroborate a single canonical promotion."""
    source_tg = SourceRepository.create(
        db=db_session,
        name="Telegram Deals Channel",
        source_type=SourceType.TELEGRAM,
        identifier="@tg_deals_test",
    )
    source_reddit = SourceRepository.create(
        db=db_session,
        name="Reddit Community Deals",
        source_type=SourceType.REDDIT,
        identifier="r/ClaudeAI_TestDeduplication",
    )

    # Item 1: Discovered on Telegram
    item1 = DiscoveryRepository.create_item(
        db=db_session,
        source_id=source_tg.id,
        external_id="tg_msg_777",
        title="Claude Pro Partner Discount",
        content="Get 50% discount on Claude Pro with promo code: CLAUDE50 at https://claude.ai/coupon?code=CLAUDE50",
    )

    # Item 2: Same deal discovered on Reddit with different text
    item2 = DiscoveryRepository.create_item(
        db=db_session,
        source_id=source_reddit.id,
        external_id="reddit_post_888",
        title="Anthropic Claude Pro 50% off promo code",
        content="Verified working: use code CLAUDE50 for 50% off Claude Pro subscription at https://claude.ai/coupon?code=CLAUDE50",
    )

    pipeline = ProcessingPipeline()

    # Process item 1 -> should create new canonical promotion
    res1 = pipeline.process_item(db_session, item1)
    assert res1.status == ProcessingStatus.PROCESSED
    assert res1.is_new_promotion is True
    promo_id_1 = res1.promotion_id
    assert promo_id_1 is not None

    # Process item 2 -> should corroborate the SAME canonical promotion!
    res2 = pipeline.process_item(db_session, item2)
    assert res2.status == ProcessingStatus.PROCESSED
    assert res2.is_new_promotion is False
    assert res2.promotion_id == promo_id_1  # Exact same promotion!

    # Verify canonical promotion record
    promo = db_session.get(item1.discoveries[0].promotion.__class__, promo_id_1)
    assert promo is not None
    assert len(promo.discoveries) == 2  # Corroborated by 2 distinct sources!
    assert promo.promo_code == "CLAUDE50"
    assert promo.discount_percentage == Decimal("50")


def test_pipeline_irrelevant_marking(db_session: Session):
    """Verify non-deal items are marked as IRRELEVANT without crashing."""
    source = SourceRepository.create(
        db=db_session,
        name="Random Chat Source",
        source_type=SourceType.REDDIT,
        identifier="r/RandomTechChat",
    )

    item = DiscoveryRepository.create_item(
        db=db_session,
        source_id=source.id,
        external_id="reddit_chat_111",
        title="How does attention mechanism work?",
        content="I was reading the original transformer paper and wondered how multihead attention is computed.",
    )

    pipeline = ProcessingPipeline()
    res = pipeline.process_item(db_session, item)
    assert res.status == ProcessingStatus.IRRELEVANT
    assert item.processing_status == ProcessingStatus.IRRELEVANT
    assert item.processing_error is not None


def test_promotions_and_pipeline_api_endpoints(client: TestClient, db_session: Session):
    """Verify API routes for running the pipeline, fetching stats, and listing promotions."""
    # 1. Run pipeline via API
    run_resp = client.post("/api/v1/processing/run?limit=10")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert "items_processed" in run_data
    assert "promotions_created" in run_data

    # 2. Get processing stats
    stats_resp = client.get("/api/v1/processing/stats")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert "pending_items" in stats_data
    assert "total_canonical_promotions" in stats_data

    # 3. List promotions
    promos_resp = client.get("/api/v1/promotions")
    assert promos_resp.status_code == 200
    assert isinstance(promos_resp.json(), list)

    # 4. Regional filter (nigeria_eligible)
    ng_resp = client.get("/api/v1/promotions?nigeria_eligible=true")
    assert ng_resp.status_code == 200
    assert isinstance(ng_resp.json(), list)
