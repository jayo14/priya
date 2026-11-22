"""Deterministic extraction of promotional offer parameters."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.database.models.enums import OfferType
from app.database.models.source import DiscoveredItem
from app.processing.classifier import ClassificationResult, EntityClassifier
from app.processing.normalizer import extract_domain, extract_urls, normalize_url

# Regex patterns for promo codes
PROMO_CODE_PATTERNS = [
    r"\bcode\s*[:\-=\s]\s*([A-Z0-9_\-]{4,25})\b",
    r"\buse\s+(?:code|coupon|promo)\s*[:\-=\s]?\s*([A-Z0-9_\-]{4,25})\b",
    r"\bpromo(?:code)?\s*[:\-=\s]\s*([A-Z0-9_\-]{4,25})\b",
    r"\bvoucher\s*[:\-=\s]\s*([A-Z0-9_\-]{4,25})\b",
]

# Patterns for discount percentages
DISCOUNT_PERCENTAGE_PATTERN = re.compile(
    r"\b(\d{1,2}(?:\.\d{1,2})?)\s*%\s*(?:off|discount)\b", re.IGNORECASE
)

# Patterns for duration in days
DURATION_PATTERNS = [
    (re.compile(r"\b(\d+)\s*months?\s*(?:free|trial|access)?\b", re.IGNORECASE), 30),
    (re.compile(r"\b(\d+)\s*days?\s*(?:free|trial|access)?\b", re.IGNORECASE), 1),
    (re.compile(r"\b1\s*year\s*(?:free|trial|access)?\b", re.IGNORECASE), 365),
    (re.compile(r"\b12\s*months?\s*(?:free|trial|access)?\b", re.IGNORECASE), 365),
]

# Countries extraction
COUNTRY_MAP = {
    "nigeria": "NG",
    "nigerian": "NG",
    "united states": "US",
    "usa": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "canada": "CA",
    "india": "IN",
    "germany": "DE",
    "worldwide": "GLOBAL",
    "global": "GLOBAL",
}


@dataclass
class ExtractedOffer:
    """Structured promotion parameters extracted from a raw discovered item."""

    provider_id: Optional[int]
    plan_id: Optional[int]
    title: str
    description: Optional[str]
    offer_type: OfferType
    discount_percentage: Optional[Decimal] = None
    duration_days: Optional[int] = None
    promo_code: Optional[str] = None
    redemption_url: Optional[str] = None
    normalized_url: Optional[str] = None
    destination_domain: Optional[str] = None
    extracted_urls: List[str] = field(default_factory=list)
    eligible_countries: List[str] = field(default_factory=list)
    excluded_countries: List[str] = field(default_factory=list)
    account_requirements: Dict[str, Any] = field(default_factory=dict)
    payment_required: Optional[bool] = None
    expires_at: Optional[datetime] = None
    confidence_score: int = 0


class OfferExtractor:
    """Extracts structured promotion terms from DiscoveredItem."""

    def __init__(self):
        self.classifier = EntityClassifier()
        self._compiled_code_regexes = [
            re.compile(p, re.IGNORECASE) for p in PROMO_CODE_PATTERNS
        ]

    def extract(self, db: Session, item: DiscoveredItem) -> Optional[ExtractedOffer]:
        title = item.title or ""
        content = item.content or ""
        full_text = f"{title}\n{content}"

        # 1. Run Classification
        classification: ClassificationResult = self.classifier.classify(db, title, content)
        if not classification.provider_id:
            # Cannot form a promotion without an identifiable AI provider
            return None

        # 2. Extract Promo Code
        promo_code: Optional[str] = None
        for reg in self._compiled_code_regexes:
            match = reg.search(full_text)
            if match:
                code_cand = match.group(1).strip()
                # Exclude common false positives
                if code_cand.upper() not in {"FREE", "PROMO", "DISCOUNT", "TRIAL", "HTTP", "HTTPS"}:
                    promo_code = code_cand.upper()
                    break

        # 3. Extract Discount Percentage
        discount_percentage: Optional[Decimal] = None
        pct_match = DISCOUNT_PERCENTAGE_PATTERN.search(full_text)
        if pct_match:
            try:
                discount_percentage = Decimal(pct_match.group(1))
            except Exception:
                discount_percentage = None

        # 4. Extract Duration Days
        duration_days: Optional[int] = None
        for reg, multiplier in DURATION_PATTERNS:
            d_match = reg.search(full_text)
            if d_match:
                try:
                    num_str = d_match.group(1) if d_match.groups() else "1"
                    duration_days = int(num_str) * multiplier
                    break
                except Exception:
                    continue

        # 5. Extract Links
        urls = extract_urls(full_text)
        # Check raw_metadata for any pre-extracted links
        if item.raw_metadata and "extracted_links" in item.raw_metadata:
            for link in item.raw_metadata["extracted_links"]:
                if link not in urls:
                    urls.append(link)

        redemption_url: Optional[str] = None
        normalized_url: Optional[str] = None
        destination_domain: Optional[str] = None

        if urls:
            redemption_url = urls[0]
            normalized_url = normalize_url(redemption_url)
            destination_domain = extract_domain(redemption_url)

        # 6. Extract Country Restrictions
        eligible_countries: List[str] = []
        lower_text = full_text.lower()
        for kw, code in COUNTRY_MAP.items():
            if re.search(r"\b" + kw + r"\b", lower_text):
                if code not in eligible_countries:
                    eligible_countries.append(code)

        # 7. Extract Payment Requirement
        payment_required: Optional[bool] = None
        if re.search(r"\b(?:no\s+(?:credit\s*)?card\s*(?:needed|required))\b", lower_text):
            payment_required = False
        elif re.search(r"\b(?:credit\s*card\s*required|payment\s*method\s*required)\b", lower_text):
            payment_required = True

        # 8. Extract Account Requirements
        account_requirements: Dict[str, Any] = {}
        if re.search(r"\bnew\s+accounts?\s+only\b", lower_text):
            account_requirements["new_accounts_only"] = True
        if re.search(r"\bexisting\s+(?:subscribers|users)\b", lower_text):
            account_requirements["existing_subscribers"] = True
        if classification.offer_type == OfferType.STUDENT_OFFER:
            account_requirements["student_verification"] = True

        # 9. Compute Confidence Score (0 to 100)
        confidence = classification.confidence_delta
        if promo_code:
            confidence += 15
        if redemption_url:
            confidence += 10
        if duration_days:
            confidence += 10
        if discount_percentage:
            confidence += 10
        confidence = min(95, max(10, confidence))

        # Generate readable canonical title
        provider_name = classification.provider_slug.capitalize() if classification.provider_slug else "AI"
        plan_name = f" {classification.plan_slug.replace('-', ' ').title()}" if classification.plan_slug else ""
        offer_name = f" ({classification.offer_type.value.replace('_', ' ').title()})"
        canonical_title = f"{provider_name}{plan_name} Deal{offer_name}"

        return ExtractedOffer(
            provider_id=classification.provider_id,
            plan_id=classification.plan_id,
            title=canonical_title,
            description=title if title and title != canonical_title else content[:300],
            offer_type=classification.offer_type,
            discount_percentage=discount_percentage,
            duration_days=duration_days,
            promo_code=promo_code,
            redemption_url=redemption_url,
            normalized_url=normalized_url,
            destination_domain=destination_domain,
            extracted_urls=urls,
            eligible_countries=eligible_countries,
            account_requirements=account_requirements,
            payment_required=payment_required,
            confidence_score=confidence,
        )
