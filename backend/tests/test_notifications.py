"""Comprehensive tests for Phase 7 Notifications, Telegram bot dispatch, and duplicate prevention."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.enums import NotificationStatus, NotificationType, OfferType, PromotionStatus
from app.database.models.notification import Notification
from app.database.models.promotion import Promotion, PromotionLink
from app.database.models.provider import Provider
from app.database.models.setting import AppSetting
from app.notifications.dispatcher import NotificationDispatcher
from app.notifications.formatter import format_expiring_alert, format_promotion_alert
from app.notifications.telegram import TelegramNotifier


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =====================================================================
# 1. Message Formatter Tests
# =====================================================================


def test_format_promotion_alert():
    promo = MagicMock(
        title="Claude Pro 1-Month Free Access",
        duration_days=30,
        discount_percentage=None,
        promo_code="CAMPUS2026",
        confidence_score=85,
        status=MagicMock(value="verified"),
        eligible_countries=["NG", "GLOBAL"],
        excluded_countries=[],
        payment_required=True,
        provider=MagicMock(name="Anthropic"),
        plan=MagicMock(name="Claude Pro"),
        links=[MagicMock(original_url="https://claude.ai/redeem", is_primary=True, link_type=MagicMock(value="redemption"))],
    )
    promo.provider.name = "Anthropic"
    promo.plan.name = "Claude Pro"

    msg = format_promotion_alert(promo, NotificationType.NEW_PROMOTION)

    assert "Priya Alert: New AI Deal Discovered!" in msg
    assert "Anthropic" in msg
    assert "Claude Pro" in msg
    assert "30 Days Free" in msg
    assert "<code>CAMPUS2026</code>" in msg
    assert "85/100" in msg
    assert "Eligible in Nigeria" in msg
    assert "Virtual USD Card" in msg
    assert "https://claude.ai/redeem" in msg


def test_format_expiring_alert():
    promo = MagicMock(
        title="ChatGPT Plus 20% Discount",
        duration_days=None,
        discount_percentage=Decimal("20.00"),
        promo_code=None,
        confidence_score=75,
        status=MagicMock(value="likely_valid"),
        eligible_countries=["GLOBAL"],
        excluded_countries=[],
        payment_required=False,
        provider=MagicMock(name="OpenAI"),
        plan=MagicMock(name="ChatGPT Plus"),
        links=[],
    )
    promo.provider.name = "OpenAI"
    promo.plan.name = "ChatGPT Plus"

    msg = format_expiring_alert(promo, hours_remaining=24)
    assert "Deal Expiring in ~24 Hours!" in msg
    assert "20.00% Off" in msg


# =====================================================================
# 2. TelegramNotifier Tests
# =====================================================================


def test_telegram_notifier_unconfigured_fallback():
    notifier = TelegramNotifier(bot_token=None, default_chat_id=None)
    assert notifier.is_configured is False

    success, detail = notifier.send_message("Test Alert")
    assert success is True
    assert "Simulated delivery" in detail


def test_telegram_notifier_http_success_mocked():
    notifier = TelegramNotifier(bot_token="test_token", default_chat_id="123456789")
    assert notifier.is_configured is True

    mock_resp = MagicMock(status_code=200)

    with patch("httpx.Client.post", return_value=mock_resp):
        success, err = notifier.send_message("<b>Hello World</b>")
        assert success is True
        assert err is None


def test_telegram_notifier_html_fallback_on_400():
    notifier = TelegramNotifier(bot_token="test_token", default_chat_id="123456789")

    # First call fails with 400 (bad entity), second call succeeds as plain text
    mock_bad_resp = MagicMock(status_code=400, text="Bad Request: can't parse entities")
    mock_ok_resp = MagicMock(status_code=200)

    with patch("httpx.Client.post", side_effect=[mock_bad_resp, mock_ok_resp]) as mock_post:
        success, err = notifier.send_message("<invalid>Unclosed tag")
        assert success is True
        assert mock_post.call_count == 2


# =====================================================================
# 3. NotificationDispatcher & Duplicate Prevention Tests
# =====================================================================


def test_notification_dispatcher_rules_and_duplicate_prevention(db_session: Session):
    dispatcher = NotificationDispatcher(notifier=TelegramNotifier(bot_token=None, default_chat_id=None))

    provider = db_session.query(Provider).first()

    promo = Promotion(
        provider_id=provider.id,
        title="Dispatcher Test Promotion",
        offer_type=OfferType.FREE_TRIAL,
        confidence_score=75,
        status=PromotionStatus.VERIFIED,
        eligible_countries=["GLOBAL"],
        excluded_countries=[],
        account_requirements={},
    )
    db_session.add(promo)
    db_session.commit()
    db_session.refresh(promo)

    # 1. First dispatch succeeds and persists a Notification record
    notif1 = dispatcher.dispatch_promotion_alert(db=db_session, promotion=promo)
    assert notif1 is not None
    assert notif1.status == NotificationStatus.SENT
    assert notif1.promotion_id == promo.id

    # 2. Second dispatch for the same promotion and notification type is blocked as duplicate!
    notif2 = dispatcher.dispatch_promotion_alert(db=db_session, promotion=promo)
    assert notif2 is None  # Blocked by duplicate prevention!

    # 3. Test confidence threshold filtering
    promo_low = Promotion(
        provider_id=provider.id,
        title="Low Confidence Promotion",
        offer_type=OfferType.UNKNOWN,
        confidence_score=40,  # Below default 60
        status=PromotionStatus.UNVERIFIED,
        eligible_countries=["GLOBAL"],
        excluded_countries=[],
        account_requirements={},
    )
    db_session.add(promo_low)
    db_session.commit()
    db_session.refresh(promo_low)

    notif_low = dispatcher.dispatch_promotion_alert(db=db_session, promotion=promo_low)
    assert notif_low is None  # Skipped because confidence < 60


def test_dispatch_expiring_promotions(db_session: Session):
    dispatcher = NotificationDispatcher(notifier=TelegramNotifier(bot_token=None, default_chat_id=None))
    provider = db_session.query(Provider).first()

    now = utc_now()
    expiring_soon = Promotion(
        provider_id=provider.id,
        title="Expiring Deal Test",
        offer_type=OfferType.DISCOUNT,
        confidence_score=80,
        status=PromotionStatus.VERIFIED,
        expires_at=now + timedelta(hours=12),  # Expiring in 12 hours
        eligible_countries=["GLOBAL"],
        excluded_countries=[],
        account_requirements={},
    )
    db_session.add(expiring_soon)
    db_session.commit()
    db_session.refresh(expiring_soon)

    count = dispatcher.dispatch_expiring_promotions(db=db_session, hours_threshold=48)
    assert count >= 1

    # Verify notification recorded with PROMOTION_EXPIRING type
    notif = (
        db_session.query(Notification)
        .filter_by(promotion_id=expiring_soon.id, notification_type=NotificationType.PROMOTION_EXPIRING)
        .first()
    )
    assert notif is not None
    assert notif.status == NotificationStatus.SENT


# =====================================================================
# 4. Notifications API Endpoints Tests
# =====================================================================


def test_notifications_api_endpoints(client: TestClient, db_session: Session):
    # 1. Test POST /notifications/test
    test_resp = client.post("/api/v1/notifications/test", json={"custom_message": "Hello Priya Test"})
    assert test_resp.status_code == 200
    test_data = test_resp.json()
    assert test_data["success"] is True
    assert test_data["channel"] == "telegram"

    # 2. Test GET /notifications
    list_resp = client.get("/api/v1/notifications")
    assert list_resp.status_code == 200
    notifs = list_resp.json()
    assert isinstance(notifs, list)

    # 3. Test POST /notifications/dispatch-expiring
    exp_resp = client.post("/api/v1/notifications/dispatch-expiring?hours_threshold=48")
    assert exp_resp.status_code == 200
    assert "alerts_dispatched" in exp_resp.json()
