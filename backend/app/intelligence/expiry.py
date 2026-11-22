"""Promotion expiry evaluation and lifecycle tracking."""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ExpiryResult:
    """Outcome of promotion expiration status check."""

    is_expired: bool
    expires_at: Optional[datetime]
    days_remaining: Optional[int]
    urgency: str  # "expired", "urgent", "active", "unknown"
    explanation: str


class ExpiryAssessor:
    """Tracks and evaluates whether promotional offers have expired."""

    def evaluate(
        self,
        expires_at: Optional[datetime],
        first_discovered_at: Optional[datetime],
        text_content: Optional[str] = None,
    ) -> ExpiryResult:
        """Evaluate promotion expiry based on timestamp or contextual hints."""
        now = utc_now()

        # If explicit expiration timestamp exists
        if expires_at:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            is_expired = now >= expires_at
            delta = expires_at - now
            days_remaining = max(0, delta.days) if not is_expired else 0

            if is_expired:
                return ExpiryResult(
                    is_expired=True,
                    expires_at=expires_at,
                    days_remaining=0,
                    urgency="expired",
                    explanation=f"Offer expired on {expires_at.strftime('%Y-%m-%d %H:%M UTC')}.",
                )
            elif delta.total_seconds() <= 48 * 3600:
                return ExpiryResult(
                    is_expired=False,
                    expires_at=expires_at,
                    days_remaining=days_remaining,
                    urgency="urgent",
                    explanation=f"Offer is expiring soon! Ends in {days_remaining} day(s).",
                )
            else:
                return ExpiryResult(
                    is_expired=False,
                    expires_at=expires_at,
                    days_remaining=days_remaining,
                    urgency="active",
                    explanation=f"Offer active. Valid until {expires_at.strftime('%Y-%m-%d')}.",
                )

        # Contextual text hints
        if text_content:
            text_lower = text_content.lower()

            # Obvious indicators that offer ended
            if re.search(r"\b(offer\s+has\s+ended|promotion\s+expired|deal\s+is\s+dead|no\s+longer\s+working|code\s+exhausted)\b", text_lower):
                return ExpiryResult(
                    is_expired=True,
                    expires_at=now,
                    days_remaining=0,
                    urgency="expired",
                    explanation="Discovered text indicates promotion has ended or code is exhausted.",
                )

            # Heuristic for hours / days remaining
            hours_match = re.search(r"\b(?:ends|expires|valid)\s+(?:in|for)\s+(\d+)\s+hours?\b", text_lower)
            if hours_match and first_discovered_at:
                hrs = int(hours_match.group(1))
                inferred_expiry = first_discovered_at + timedelta(hours=hrs)
                is_exp = now >= inferred_expiry
                return ExpiryResult(
                    is_expired=is_exp,
                    expires_at=inferred_expiry,
                    days_remaining=0 if is_exp else max(0, (inferred_expiry - now).days),
                    urgency="expired" if is_exp else "urgent",
                    explanation=f"Inferred {hrs}-hour expiry from discovery time.",
                )

        # If older than 30 days with no explicit expiry, flag caution
        if first_discovered_at:
            age_days = (now - first_discovered_at).days
            if age_days > 45:
                return ExpiryResult(
                    is_expired=False,
                    expires_at=None,
                    days_remaining=None,
                    urgency="urgent",
                    explanation=f"Offer discovered {age_days} days ago without expiry date; may no longer be active.",
                )

        return ExpiryResult(
            is_expired=False,
            expires_at=None,
            days_remaining=None,
            urgency="unknown",
            explanation="No explicit expiry date specified.",
        )
