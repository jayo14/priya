"""Deterministic provider, plan, and offer type classifier."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.database.models.enums import OfferType
from app.database.models.provider import Plan, Provider
from app.database.repositories.provider_repo import ProviderRepository

PROVIDER_RULES: Dict[str, List[str]] = {
    "anthropic": [r"\bclaude\b", r"\banthropic\b", r"\bsonnet\b", r"\bopus\b"],
    "openai": [r"\bchatgpt\b", r"\bopenai\b", r"\bgpt-?4o?\b", r"\bgpt\s*plus\b"],
    "xai": [r"\bx\.?ai\b", r"\bgrok\b", r"\bsupergrok\b"],
    "google": [r"\bgemini\b", r"\bgoogle\s*ai\b", r"\bgemini\s*advanced\b"],
    "perplexity": [r"\bperplexity\b", r"\bpplx\b"],
    "cursor": [r"\bcursor\b", r"\bcursor\s*ai\b", r"\banysphere\b"],
    "github": [r"\bgithub\b", r"\bcopilot\b", r"\bgithub\s*copilot\b"],
}

PLAN_RULES: Dict[str, Dict[str, List[str]]] = {
    "anthropic": {
        "claude-pro": [r"\bclaude\s*pro\b", r"\bpro\s*tier\b", r"\bpro\b"],
        "claude-max": [r"\bclaude\s*max\b", r"\bmax\s*tier\b", r"\bteam\b"],
    },
    "openai": {
        "chatgpt-plus": [r"\bchatgpt\s*plus\b", r"\bgpt\s*plus\b", r"\bplus\b"],
        "chatgpt-pro": [r"\bchatgpt\s*pro\b", r"\bgpt\s*pro\b"],
        "chatgpt-go": [r"\bchatgpt\s*go\b", r"\bgo\s*tier\b"],
    },
    "xai": {
        "grok-premium": [r"\bgrok\s*premium\b", r"\bpremium\b", r"\bx\s*premium\b"],
        "supergrok": [r"\bsupergrok\b", r"\bgrok\s*pro\b", r"\bsuper\s*grok\b"],
    },
    "google": {
        "google-ai-pro": [r"\bgoogle\s*ai\s*pro\b", r"\bgemini\s*pro\b"],
        "google-one-ai-premium": [
            r"\bgoogle\s*one\b",
            r"\bai\s*premium\b",
            r"\bgemini\s*advanced\b",
        ],
    },
    "perplexity": {
        "perplexity-pro": [r"\bperplexity\s*pro\b", r"\bpro\b", r"\bpplx\s*pro\b"],
    },
    "cursor": {
        "cursor-pro": [r"\bcursor\s*pro\b", r"\bpro\b"],
    },
    "github": {
        "github-copilot-pro": [
            r"\bcopilot\s*pro\b",
            r"\bindividual\b",
            r"\bcopilot\b",
        ],
    },
}

OFFER_TYPE_RULES: List[Tuple[OfferType, List[str]]] = [
    (
        OfferType.STUDENT_OFFER,
        [
            r"\bstudent\s*(?:pack|discount|offer|verification)\b",
            r"\bfor\s+students\b",
            r"\bsheerid\b",
            r"\b\.edu\b",
            r"\buniversity\s+offer\b",
        ],
    ),
    (
        OfferType.FREE_TRIAL,
        [
            r"\bfree\s*trial\b",
            r"\b\d+\s*days?\s*(?:free\s*)?trial\b",
            r"\btrial\s*period\b",
            r"\btry\s*free\b",
        ],
    ),
    (
        OfferType.FREE_SUBSCRIPTION,
        [
            r"\bfree\s*subscription\b",
            r"\b\d+\s*months?\s*free\b",
            r"\b1\s*year\s*free\b",
            r"\bfree\s*(?:for\s*\d+\s*(?:months?|year))\b",
            r"\b100%\s*off\b",
        ],
    ),
    (
        OfferType.DISCOUNT,
        [
            r"\b\d{1,2}%\s*off\b",
            r"\bdiscount\s*(?:code|rate|price)?\b",
            r"\bpromo\s*code\b",
            r"\bvoucher\b",
            r"\bcoupon\b",
            r"\$\d+\s*off\b",
        ],
    ),
    (
        OfferType.GIVEAWAY,
        [
            r"\bgiveaway\b",
            r"\braffle\b",
            r"\bretweet\s*to\s*win\b",
            r"\blucky\s*winners?\b",
        ],
    ),
    (
        OfferType.PARTNER_OFFER,
        [
            r"\bpartner\s*(?:offer|promotion|deal)\b",
            r"\bbundled\s*with\b",
            r"\bexclusive\s*deal\b",
        ],
    ),
    (
        OfferType.REFERRAL,
        [
            r"\breferral\s*(?:link|code)?\b",
            r"\binvite\s*friend\b",
            r"\buse\s*my\s*(?:code|ref)\b",
        ],
    ),
]


@dataclass
class ClassificationResult:
    """Classification outcome identifying provider, plan, and offer type."""

    provider_id: Optional[int]
    provider_slug: Optional[str]
    plan_id: Optional[int]
    plan_slug: Optional[str]
    offer_type: OfferType
    confidence_delta: int = 0


class EntityClassifier:
    """Deterministic classifier recognizing AI providers, subscription plans, and offer types."""

    def __init__(self):
        # Precompile regexes
        self._compiled_providers = {
            slug: [re.compile(p, re.IGNORECASE) for p in patterns]
            for slug, patterns in PROVIDER_RULES.items()
        }
        self._compiled_plans = {
            prov_slug: {
                plan_slug: [re.compile(p, re.IGNORECASE) for p in patterns]
                for plan_slug, patterns in plan_dict.items()
            }
            for prov_slug, plan_dict in PLAN_RULES.items()
        }
        self._compiled_offer_types = [
            (otype, [re.compile(p, re.IGNORECASE) for p in patterns])
            for otype, patterns in OFFER_TYPE_RULES
        ]

    def classify(
        self, db: Session, title: Optional[str], content: str
    ) -> ClassificationResult:
        full_text = f"{title or ''} {content}"

        # 1. Identify Provider
        matched_provider_slug: Optional[str] = None
        for slug, regexes in self._compiled_providers.items():
            if any(r.search(full_text) for r in regexes):
                matched_provider_slug = slug
                break

        provider: Optional[Provider] = None
        if matched_provider_slug:
            provider = ProviderRepository.get_by_slug(db, matched_provider_slug)

        # 2. Identify Plan if provider was recognized
        matched_plan_slug: Optional[str] = None
        plan: Optional[Plan] = None
        if provider and provider.slug in self._compiled_plans:
            for p_slug, p_regexes in self._compiled_plans[provider.slug].items():
                if any(r.search(full_text) for r in p_regexes):
                    matched_plan_slug = p_slug
                    break

            if matched_plan_slug:
                plan = ProviderRepository.get_plan_by_slug(
                    db, provider_id=provider.id, slug=matched_plan_slug
                )

        # 3. Identify Offer Type
        matched_offer_type = OfferType.UNKNOWN
        for otype, o_regexes in self._compiled_offer_types:
            if any(r.search(full_text) for r in o_regexes):
                matched_offer_type = otype
                break

        # Calculate confidence signal
        confidence = 0
        if provider:
            confidence += 30
        if plan:
            confidence += 25
        if matched_offer_type != OfferType.UNKNOWN:
            confidence += 20

        return ClassificationResult(
            provider_id=provider.id if provider else None,
            provider_slug=provider.slug if provider else None,
            plan_id=plan.id if plan else None,
            plan_slug=plan.slug if plan else None,
            offer_type=matched_offer_type,
            confidence_delta=confidence,
        )
