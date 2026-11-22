"""End-to-End Pipeline & System Integration Test for Priya.

Simulates the complete deterministic lifecycle:
1. Discovery from multiple sources (Telegram, Reddit, Web)
2. Normalization, content filtering, classification, offer extraction, deduplication
3. Security inspection, authenticity scoring, Nigerian eligibility, confidence scoring
4. Real-time alert dispatching with single-delivery semantics
5. Consumption by frontend APIs (Dashboard, Watchlist, Deals Catalogue)
"""

import hashlib

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.enums import (
    NotificationStatus,
    ProcessingStatus,
    PromotionStatus,
    SourceType,
)
from app.database.models.notification import Notification
from app.database.models.promotion import Promotion, PromotionDiscovery
from app.database.models.provider import Provider
from app.database.models.source import DiscoveredItem, Source
from app.notifications.dispatcher import NotificationDispatcher
from app.processing.pipeline import ProcessingPipeline


def test_full_e2e_lifecycle(db_session: Session, client: TestClient):
    """Test the entire Priya workflow from raw discovery to notification and dashboard reporting."""
    # -------------------------------------------------------------
    # Step 1: Set up sources
    # -------------------------------------------------------------
    telegram_source = Source(
        name="Telegram Deals Hub",
        identifier="telegram-deals-hub-e2e",
        source_type=SourceType.TELEGRAM,
        url="https://t.me/s/aidealshub",
        is_active=True,
    )
    reddit_source = Source(
        name="Reddit AI Promos",
        identifier="reddit-ai-promos-e2e",
        source_type=SourceType.REDDIT,
        url="https://www.reddit.com/r/AIPromos.json",
        is_active=True,
    )
    db_session.add_all([telegram_source, reddit_source])
    db_session.commit()

    # -------------------------------------------------------------
    # Step 2: Ingest 4 raw items (1 legitimate Claude, 1 Claude duplicate, 1 legitimate Perplexity, 1 scam)
    # -------------------------------------------------------------
    raw_claude_text = (
        "Anthropic just announced 50% off Claude Pro for 3 months! "
        "Use promo code CLAUDE50 on checkout at https://claude.ai/upgrade. Limited time."
    )
    item_claude = DiscoveredItem(
        source_id=telegram_source.id,
        external_id="tg_msg_1001",
        title="50% off Claude Pro",
        content=raw_claude_text,
        original_url="https://t.me/s/aidealshub/1001",
        content_hash=hashlib.sha256(raw_claude_text.encode()).hexdigest(),
        processing_status=ProcessingStatus.PENDING,
    )

    # Second item from Reddit corroborating the exact same promotion
    raw_claude_reddit = (
        "Huge discount: get Claude Pro subscription at 50% off using code CLAUDE50! "
        "Official Anthropic promotion link: https://claude.ai/upgrade."
    )
    item_claude_corrob = DiscoveredItem(
        source_id=reddit_source.id,
        external_id="reddit_post_2001",
        title="Claude Pro Promo Code Working",
        content=raw_claude_reddit,
        original_url="https://www.reddit.com/r/AIPromos/comments/2001",
        content_hash=hashlib.sha256(raw_claude_reddit.encode()).hexdigest(),
        processing_status=ProcessingStatus.PENDING,
    )

    # Third item: Perplexity Pro 1 month free trial
    raw_pplx_text = (
        "Get 1 month free Perplexity Pro with this referral link: "
        "https://perplexity.ai/pro?referral=FREEPERP30. Works globally including Africa and Nigeria!"
    )
    item_perplexity = DiscoveredItem(
        source_id=telegram_source.id,
        external_id="tg_msg_1002",
        title="1 Month Free Perplexity Pro",
        content=raw_pplx_text,
        original_url="https://t.me/s/aidealshub/1002",
        content_hash=hashlib.sha256(raw_pplx_text.encode()).hexdigest(),
        processing_status=ProcessingStatus.PENDING,
    )

    # Fourth item: Obvious scam / fraud content
    raw_scam_text = (
        "Free cracked ChatGPT Plus accounts! BIN method working 2026! "
        "Join telegram for shared accounts and cookies. DM for password."
    )
    item_scam = DiscoveredItem(
        source_id=telegram_source.id,
        external_id="tg_msg_1003",
        title="Free Cracked ChatGPT",
        content=raw_scam_text,
        original_url="https://t.me/s/aidealshub/1003",
        content_hash=hashlib.sha256(raw_scam_text.encode()).hexdigest(),
        processing_status=ProcessingStatus.PENDING,
    )

    db_session.add_all([item_claude, item_claude_corrob, item_perplexity, item_scam])
    db_session.commit()

    # -------------------------------------------------------------
    # Step 3: Run Processing Pipeline
    # -------------------------------------------------------------
    pipeline = ProcessingPipeline()

    # Process first Claude deal
    res1 = pipeline.process_item(db_session, item_claude)
    assert res1.status == ProcessingStatus.PROCESSED
    assert res1.is_new_promotion is True
    claude_promo_id = res1.promotion_id
    assert claude_promo_id is not None

    # Process scam item -> should be marked irrelevant and no promo created
    res_scam = pipeline.process_item(db_session, item_scam)
    assert res_scam.status == ProcessingStatus.IRRELEVANT
    assert res_scam.is_new_promotion is False
    assert res_scam.promotion_id is None
    db_session.refresh(item_scam)
    assert item_scam.processing_status == ProcessingStatus.IRRELEVANT

    # Process Perplexity deal -> should create second promo
    res2 = pipeline.process_item(db_session, item_perplexity)
    assert res2.status == ProcessingStatus.PROCESSED
    assert res2.is_new_promotion is True
    pplx_promo_id = res2.promotion_id
    assert pplx_promo_id is not None
    assert pplx_promo_id != claude_promo_id

    # Process second Claude deal -> deduplication should link to existing promo as corroboration
    res_corrob = pipeline.process_item(db_session, item_claude_corrob)
    assert res_corrob.status == ProcessingStatus.PROCESSED
    assert res_corrob.is_new_promotion is False
    assert res_corrob.promotion_id == claude_promo_id

    # Verify corroboration record exists in database
    discoveries = (
        db_session.query(PromotionDiscovery)
        .filter(PromotionDiscovery.promotion_id == claude_promo_id)
        .all()
    )
    assert len(discoveries) == 2  # Telegram + Reddit

    # -------------------------------------------------------------
    # Step 4: Run Intelligence Engine (Verification & Scoring)
    # -------------------------------------------------------------
    claude_promo = db_session.query(Promotion).filter(Promotion.id == claude_promo_id).one()
    pplx_promo = db_session.query(Promotion).filter(Promotion.id == pplx_promo_id).one()

    # Claude promo was automatically evaluated by pipeline
    assert claude_promo.confidence_score >= 70
    assert claude_promo.status in [PromotionStatus.VERIFIED, PromotionStatus.LIKELY_VALID]
    claude_checks = {c.check_type for c in claude_promo.verification_checks}
    assert "nigeria_eligibility" in claude_checks
    assert "confidence_scoring" in claude_checks

    # Perplexity promo was automatically evaluated by pipeline
    assert pplx_promo.confidence_score >= 50
    pplx_checks = {c.check_type for c in pplx_promo.verification_checks}
    assert "nigeria_eligibility" in pplx_checks

    # -------------------------------------------------------------
    # Step 5: Real-time Alert Dispatching via Telegram & Deduplication
    # -------------------------------------------------------------
    # Notice that pipeline.process_item automatically invoked dispatcher for Claude & Perplexity!
    # A subsequent call to dispatch_promotion_alert on Claude should be suppressed as a duplicate (return None)
    dispatcher = NotificationDispatcher()
    duplicate_result = dispatcher.dispatch_promotion_alert(db_session, claude_promo)
    assert duplicate_result is None, "Expected duplicate alert to be suppressed"

    # Verify notifications table has exactly 2 records (1 for Claude, 1 for Perplexity)
    notifs = (
        db_session.query(Notification)
        .filter(Notification.status == NotificationStatus.SENT)
        .all()
    )
    assert len(notifs) == 2
    promo_ids_notified = {n.promotion_id for n in notifs}
    assert claude_promo.id in promo_ids_notified
    assert pplx_promo.id in promo_ids_notified

    # -------------------------------------------------------------
    # Step 6: Frontend API Endpoints Verification
    # -------------------------------------------------------------
    # 1. Health check
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. Dashboard KPIs
    res_stats = client.get("/api/v1/dashboard/stats")
    assert res_stats.status_code == 200
    stats_data = res_stats.json()
    assert stats_data["total_promotions"] >= 2
    assert stats_data["verified_promotions"] + stats_data["likely_valid_promotions"] >= 2
    assert stats_data["total_discovered_items"] >= 3
    assert stats_data["nigeria_eligible_promotions"] >= 2
    assert len(stats_data["providers"]) > 0

    # 3. Dashboard Activity Feed
    res_act = client.get("/api/v1/dashboard/activity")
    assert res_act.status_code == 200
    assert len(res_act.json()) > 0

    # 4. Promotions catalogue with filters
    res_promos = client.get("/api/v1/promotions?nigeria_eligible=true&min_confidence=50")
    assert res_promos.status_code == 200
    promos_list = res_promos.json()
    assert len(promos_list) >= 2

    # 5. Watchlist workflow: Add provider & promotion to user watchlist
    claude_provider = db_session.query(Provider).filter(Provider.slug == "anthropic").one()

    # Watch provider
    res_watch_provider = client.post(f"/api/v1/watchlist/providers/{claude_provider.id}")
    assert res_watch_provider.status_code in [200, 201]

    # Watch specific promotion
    res_watch_promo = client.post(f"/api/v1/watchlist/promotions/{claude_promo.id}")
    assert res_watch_promo.status_code in [200, 201]

    # Retrieve watchlist IDs
    res_watchlist = client.get("/api/v1/watchlist")
    assert res_watchlist.status_code == 200
    wl_data = res_watchlist.json()
    assert claude_provider.id in wl_data["provider_ids"]
    assert claude_promo.id in wl_data["promotion_ids"]
    assert wl_data["total_watched_providers"] >= 1
    assert wl_data["total_saved_promotions"] >= 1

    # Retrieve expanded watchlist items (returns saved promotions)
    res_items = client.get("/api/v1/watchlist/items")
    assert res_items.status_code == 200
    items_data = res_items.json()
    assert len(items_data) >= 1
    assert any(pr["id"] == claude_promo.id for pr in items_data)

    # 6. Notifications feed
    res_notifs = client.get("/api/v1/notifications")
    assert res_notifs.status_code == 200
    assert len(res_notifs.json()) >= 2
