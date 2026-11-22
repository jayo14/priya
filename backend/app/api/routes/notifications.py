"""API endpoints for managing and inspecting notification alerts and Telegram dispatch."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import DbSession
from app.database.models.enums import NotificationStatus, NotificationType
from app.database.models.notification import Notification
from app.database.models.promotion import Promotion
from app.notifications.dispatcher import NotificationDispatcher
from app.notifications.telegram import TelegramNotifier

router = APIRouter(prefix="/notifications", tags=["Notifications"])
dispatcher = NotificationDispatcher()
telegram_notifier = TelegramNotifier()


# --- Schemas ---


class NotificationResponse(BaseModel):
    id: int
    promotion_id: Optional[int]
    channel: str
    notification_type: str
    status: str
    message: str
    sent_at: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class TestNotificationRequest(BaseModel):
    chat_id: Optional[str] = None
    custom_message: Optional[str] = None


class TestNotificationResponse(BaseModel):
    success: bool
    is_configured: bool
    channel: str
    detail: Optional[str] = None


class DispatchExpiringResponse(BaseModel):
    alerts_dispatched: int
    hours_threshold: int


# --- Endpoints ---


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    status: Optional[NotificationStatus] = None,
    notification_type: Optional[NotificationType] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = DbSession,
):
    """List historical alert notifications with delivery status."""
    stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Notification.status == status)
    if notification_type:
        stmt = stmt.where(Notification.notification_type == notification_type)

    notifs = list(db.execute(stmt).scalars().all())

    return [
        NotificationResponse(
            id=n.id,
            promotion_id=n.promotion_id,
            channel=n.channel,
            notification_type=n.notification_type.value,
            status=n.status.value,
            message=n.message,
            sent_at=n.sent_at.isoformat() if n.sent_at else None,
            created_at=n.created_at.isoformat(),
        )
        for n in notifs
    ]


@router.post("/test", response_model=TestNotificationResponse)
def send_test_notification(payload: TestNotificationRequest = TestNotificationRequest()):
    """Send a test message to verify Telegram bot credentials and channel connectivity."""
    msg = (
        payload.custom_message
        or "<b>🔔 Priya Deal Finder Test Notification</b>\n\nYour Telegram alerting channel is successfully connected! You will receive instant notifications when verified AI subscription deals appear."
    )

    success, err = telegram_notifier.send_message(text=msg, chat_id=payload.chat_id)

    return TestNotificationResponse(
        success=success,
        is_configured=telegram_notifier.is_configured,
        channel="telegram",
        detail=err or "Message delivered successfully.",
    )


@router.post("/dispatch-expiring", response_model=DispatchExpiringResponse)
def dispatch_expiring_alerts(
    hours_threshold: int = Query(48, ge=1, le=168),
    db: Session = DbSession,
):
    """Scan and dispatch alerts for all active promotions expiring within the specified hours."""
    count = dispatcher.dispatch_expiring_promotions(db=db, hours_threshold=hours_threshold)
    return DispatchExpiringResponse(alerts_dispatched=count, hours_threshold=hours_threshold)


@router.post("/promotions/{promotion_id}/dispatch", response_model=NotificationResponse)
def dispatch_promotion_notification(
    promotion_id: int,
    ignore_thresholds: bool = Query(True, description="Force send ignoring confidence filters"),
    db: Session = DbSession,
):
    """Force dispatch an alert for a specific promotion."""
    promo = db.execute(select(Promotion).where(Promotion.id == promotion_id)).scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")

    notif = dispatcher.dispatch_promotion_alert(
        db=db,
        promotion=promo,
        notification_type=NotificationType.NEW_PROMOTION,
        ignore_thresholds=ignore_thresholds,
    )

    if not notif:
        raise HTTPException(
            status_code=400,
            detail="Alert not sent (either already sent or skipped by user preference filters)",
        )

    return NotificationResponse(
        id=notif.id,
        promotion_id=notif.promotion_id,
        channel=notif.channel,
        notification_type=notif.notification_type.value,
        status=notif.status.value,
        message=notif.message,
        sent_at=notif.sent_at.isoformat() if notif.sent_at else None,
        created_at=notif.created_at.isoformat(),
    )
