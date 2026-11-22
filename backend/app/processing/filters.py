"""Keyword filtering and spam/scam detection for discovered items."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Positive signals indicating genuine promotional opportunities
PROMOTIONAL_PATTERNS = [
    r"\bfree\s+(?:trial|month|months|subscription|access|tier|pro|plus|credit)\b",
    r"\b\d+\s+months?\s+free\b",
    r"\b\d+\s+days?\s+free\b",
    r"\b(?:discount|promo\s+code|coupon|voucher)\b",
    r"\b\d{1,2}%\s+off\b",
    r"\b(?:student\s+(?:discount|offer|pack|developer|plan))\b",
    r"\b(?:partner\s+offer|referral\s+(?:code|link)|giveaway)\b",
    r"\b(?:100%\s+off|special\s+offer|limited\s+time\s+offer)\b",
    r"\b(?:claim\s+(?:free|your|offer)|redeem\s+(?:code|offer))\b",
]

# Negative patterns indicating illicit account sales, cracking, or scams
ILLICIT_PATTERNS = [
    r"\b(?:buy|selling|sell)\s+(?:claude|chatgpt|openai|grok)\s+accounts?\b",
    r"\b(?:shared|cracked|hacked|stolen)\s+accounts?\b",
    r"\b(?:bin|carding|fullz|dumps|cookie\s+method)\b",
    r"\b(?:dm\s+(?:to\s+buy|me\s+for\s+account|for\s+cheap))\b",
    r"\b(?:vouch\s+for\s+sale|cheap\s+rate|instant\s+delivery\s+accounts?)\b",
    r"\b(?:login\s+credentials\s+below|email:pass)\b",
]


@dataclass
class FilterResult:
    """Outcome of filtering check for promotional relevance and safety."""

    is_relevant: bool
    is_spam_or_illicit: bool
    relevance_score: float  # 0.0 to 1.0
    matched_keywords: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None


class ContentFilter:
    """Deterministic filter assessing content relevance for AI subscription deals."""

    def __init__(self):
        self._positive_regexes = [
            re.compile(p, re.IGNORECASE) for p in PROMOTIONAL_PATTERNS
        ]
        self._illicit_regexes = [
            re.compile(p, re.IGNORECASE) for p in ILLICIT_PATTERNS
        ]

    def evaluate(self, title: Optional[str], content: str) -> FilterResult:
        full_text = f"{title or ''} {content}".strip()
        if not full_text:
            return FilterResult(
                is_relevant=False,
                is_spam_or_illicit=False,
                relevance_score=0.0,
                rejection_reason="Empty content",
            )

        # 1. Check for illicit/scam account trading
        for reg in self._illicit_regexes:
            match = reg.search(full_text)
            if match:
                return FilterResult(
                    is_relevant=False,
                    is_spam_or_illicit=True,
                    relevance_score=0.0,
                    matched_keywords=[match.group(0)],
                    rejection_reason=f"Detected illicit account trading or scam pattern: '{match.group(0)}'",
                )

        # 2. Check for positive promotional matches
        matched: List[str] = []
        for reg in self._positive_regexes:
            match = reg.search(full_text)
            if match:
                matched.append(match.group(0))

        if not matched:
            return FilterResult(
                is_relevant=False,
                is_spam_or_illicit=False,
                relevance_score=0.1,
                rejection_reason="No promotional deal keywords detected",
            )

        # Calculate normalized score based on density and variety of signals
        score = min(1.0, 0.4 + (0.2 * len(matched)))

        return FilterResult(
            is_relevant=True,
            is_spam_or_illicit=False,
            relevance_score=score,
            matched_keywords=matched,
        )
