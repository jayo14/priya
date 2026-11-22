"""Notification dispatching service with duplicate prevention and user rule evaluation."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import setup_logging
from app.database.models.enums import NotificationStatus, NotificationType
from app.database.models.notification import Notification
from app.database.models.promotion import Promotion
from app.database.models.setting import AppSetting
from app.notifications.formatter import format_expiring_alert, format_promotion_alert
from app.notifications.telegram import TelegramNotifier

logger = setup_logging()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationDispatcher:
    """Manages alert rules, duplicate prevention, and multi-channel delivery."""

    def __init__(self, notifier: Optional[TelegramNotifier] = None):
        self.notifier = notifier or TelegramNotifier()

    @staticmethod
    def get_preferences(db: Session) -> dict:
        """Fetch user preferences from app_settings."""
        setting = db.execute(
            select(AppSetting).where(AppSetting.key == "user_preferences")
        ).scalar_one_or_none()
        default_prefs = {
            "min_confidence_score": 60,
            "nigeria_only_filter": False,
            "telegram_notifications_enabled": True,
        }
        if setting and setting.value:
            default_prefs.update(setting.value)
        return default_prefs

    def should_alert(self, db: Session, promotion: Promotion) -> tuple[bool, Optional[str]]:
        """Evaluate whether a promotion passes notification thresholds.

        Returns (should_alert: bool, skip_reason: Optional[str]).
        """
        prefs = self.get_preferences(db)

        if not prefs.get("telegram_notifications_enabled", True):
            return False, "Telegram notifications disabled in settings."

        min_conf = prefs.get("min_confidence_score", 60)
        if promotion.confidence_score < min_conf:
            return False, f"Confidence score {promotion.confidence_score} is below threshold {min_conf}."

        if prefs.get("nigeria_only_filter", False):
            upper_ex = [c.upper() for c in (promotion.excluded_countries or [])]
            upper_el = [c.upper() for c in (promotion.eligible_countries or [])]
            if "NG" in upper_ex or (upper_el and "NG" not in upper_el and "GLOBAL" not in upper_el):
                return False, "Filtered out: Nigeria is excluded and nigeria_only_filter is active."

        return True, None

    def dispatch_promotion_alert(
        self,
        db: Session,
        promotion: Promotion,
        notification_type: NotificationType = NotificationType.NEW_PROMOTION,
        ignore_thresholds: bool = False,
    ) -> Optional[Notification]:
        """Format and dispatch a promotion alert with duplicate prevention."""
        # 1. Evaluate alert criteria
        if not ignore_thresholds:
            eligible, reason = self.should_alert(db, promotion)
            if not eligible:
                logger.info(f"Skipping alert for promo #{promotion.id}: {reason}")
                return None

        # 2. Duplicate Prevention Check
        existing_sent = db.execute(
            select(Notification).where(
                Notification.promotion_id == promotion.id,
                Notification.notification_type == notification_type,
                Notification.status == NotificationStatus.SENT,
            )
        ).scalar_one_or_none()

        if existing_sent:
            logger.info(
                f"Skipping duplicate alert for promo #{promotion.id} ({notification_type.value} already sent at {existing_sent.sent_at})"
            )
            return None

        # 3. Format Message
        message_text = format_promotion_alert(
            promotion=promotion, notification_type=notification_type
        )

        # 4. Create Notification Record (Pending)
        notif = Notification(
            promotion_id=promotion.id,
            channel="telegram",
            notification_type=notification_type,
            status=NotificationStatus.PENDING,
            message=message_text,
            created_at=utc_now(),
        )
        db.add(notif)
        db.flush()

        # 5. Send via Telegram Notifier
        success, err = self.notifier.send_message(message_text)

        if success:
            notif.status = NotificationStatus.SENT
            notif.sent_at = utc_now()
        else:
            notif.status = NotificationStatus.FAILED

        db.commit()
        db.refresh(notif)
        return notif

    def dispatch_expiring_promotions(
        self, db: Session, hours_threshold: int = 48
    ) -> int:
        """Scan for promotions expiring in the next N hours and send alerts."""
        now = utc_now()
        threshold_time = now + timedelta(hours=hours_threshold)

        expiring_promos = list(
            db.execute(
                select(Promotion).where(
                    Promotion.expires_at.is_not(None),
                    Promotion.expires_at > now,
                    Promotion.expires_at <= threshold_time,
                )
            )
            .scalars()
            .all()
        )

        sent_count = 0
        for promo in expiring_promos:
            notif = self.dispatch_promotion_alert(
                db=db,
                promotion=promo,
                notification_type=NotificationType.PROMOTION_EXPIRING,
            )
            if notif and notif.status == NotificationStatus.SENT:
                sent_count += 1

        logger.info(
            f"Expiring scan checked {len(expiring_promos)} deals, dispatched {sent_count} alert(s)"
        )
        return sent_count
