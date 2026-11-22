"""HTML message formatters for Telegram notifications."""

import html
from typing import Optional

from app.database.models.enums import NotificationType
from app.database.models.promotion import Promotion


def format_promotion_alert(
    promotion: Promotion,
    notification_type: NotificationType = NotificationType.NEW_PROMOTION,
    custom_headline: Optional[str] = None,
) -> str:
    """Format an extracted promotion into an HTML-formatted Telegram alert message."""
    provider_name = promotion.provider.name if promotion.provider else "AI Provider"
    plan_name = promotion.plan.name if promotion.plan else "Subscription Plan"
    title_escaped = html.escape(promotion.title)

    if notification_type == NotificationType.PROMOTION_EXPIRING:
        header = "⏳ <b>Priya Alert: Deal Expiring Soon!</b>"
    elif notification_type == NotificationType.VERIFICATION_STATUS_CHANGED:
        header = "🛡 <b>Priya Alert: Promotion Verified!</b>"
    else:
        header = "🚀 <b>Priya Alert: New AI Deal Discovered!</b>"

    if custom_headline:
        header = f"⚡ <b>{html.escape(custom_headline)}</b>"

    lines = [
        header,
        "",
        f"🤖 <b>Provider:</b> {html.escape(provider_name)}",
        f"📦 <b>Plan:</b> {html.escape(plan_name)}",
        f"🎯 <b>Deal:</b> {title_escaped}",
    ]

    # Offer parameters
    if promotion.duration_days:
        lines.append(f"⏱ <b>Access:</b> {promotion.duration_days} Days Free")
    elif promotion.discount_percentage:
        lines.append(f"💸 <b>Discount:</b> {promotion.discount_percentage}% Off")

    if promotion.promo_code:
        lines.append(f"🏷 <b>Promo Code:</b> <code>{html.escape(promotion.promo_code)}</code>")

    # Status & Confidence
    status_label = promotion.status.value.replace("_", " ").upper()
    lines.append(f"⭐ <b>Score:</b> {promotion.confidence_score}/100 ({status_label})")

    # Nigerian Regional & Banking Assessment
    upper_el = [c.upper() for c in (promotion.eligible_countries or [])]
    upper_ex = [c.upper() for c in (promotion.excluded_countries or [])]

    if "NG" in upper_ex:
        ng_status = "❌ Ineligible (Nigeria explicitly excluded)"
    elif "NG" in upper_el or "GLOBAL" in upper_el or not upper_el:
        ng_status = "✅ Eligible in Nigeria"
    else:
        ng_status = "⚠️ Regional restrictions apply"

    lines.extend([
        "",
        f"🇳🇬 <b>Nigerian Usability:</b> {ng_status}",
    ])

    if promotion.payment_required:
        lines.append(
            "💳 <b>Payment Note:</b> Local Naira debit cards often fail CBN foreign limits. A funded Virtual USD Card (Geegpay, Chipper, Payday) is recommended."
        )

    # Primary Redemption Link
    primary_link = None
    if promotion.links:
        for lnk in promotion.links:
            if lnk.is_primary or lnk.link_type.value == "redemption":
                primary_link = lnk
                break
        if not primary_link:
            primary_link = promotion.links[0]

    if primary_link:
        safe_url = html.escape(primary_link.original_url)
        lines.extend([
            "",
            f"🔗 <a href=\"{safe_url}\"><b>Open Redemption Page</b></a>",
        ])

    lines.extend([
        "",
        "<i>You discover the opportunity. Priya brings it to you. You decide whether to claim it.</i>",
    ])

    return "\n".join(lines)


def format_expiring_alert(promotion: Promotion, hours_remaining: int) -> str:
    """Format an alert specifically for an expiring opportunity."""
    return format_promotion_alert(
        promotion=promotion,
        notification_type=NotificationType.PROMOTION_EXPIRING,
        custom_headline=f"Deal Expiring in ~{hours_remaining} Hours!",
    )
