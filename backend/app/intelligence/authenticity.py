"""Authenticity and risk assessment module for AI subscription promotions."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.intelligence.link_validator import LinkInspectionResult


@dataclass
class AuthenticityResult:
    """Outcome of promotion authenticity and fraud risk analysis."""

    is_authentic: bool
    is_scam: bool
    authenticity_score: int  # 0 to 30 points
    trust_signals: List[str] = field(default_factory=list)
    risk_signals: List[str] = field(default_factory=list)


# Unambiguous scam and illicit account sharing terms
SCAM_FRAUD_PATTERNS = [
    re.compile(r"\b(cracked|bin\s+method|carding|stolen\s+cookies|cookie\s+method)\b", re.I),
    re.compile(r"\b(shared\s+account|login\s+with\s+(my|this)\s+(email|credentials|account))\b", re.I),
    re.compile(r"\b(modded\s+apk|download\s+crack|bypass\s+(paywall|payment))\b", re.I),
    re.compile(r"\b(send\s+(usdt|crypto|bitcoin|eth)|dm\s+for\s+(password|login))\b", re.I),
    re.compile(r"\b(free\s+accounts?\s+list|combo\s+list|leaked\s+credentials)\b", re.I),
    re.compile(r"\b(lifetime\s+access\s+for\s+\$?\d+)\b", re.I),
]

# Official domain / source markers
HIGH_TRUST_SOURCE_PATTERNS = [
    re.compile(r"(anthropic|openai|xai|google|github|perplexity|cursor)\.com", re.I),
    re.compile(r"\b(official|announcement|press\s+release|verified)\b", re.I),
]


class AuthenticityAssessor:
    """Evaluates whether an offer is legitimate, authentic, or fraudulent."""

    def evaluate(
        self,
        title: str,
        content: str,
        source_type: Optional[str] = None,
        source_identifier: Optional[str] = None,
        link_inspection: Optional[LinkInspectionResult] = None,
        is_provider_domain: bool = False,
        is_partner_domain: bool = False,
    ) -> AuthenticityResult:
        """Run authenticity heuristics and calculate score contribution (0-30 points)."""
        combined_text = f"{title}\n{content}"
        risk_signals: List[str] = []
        trust_signals: List[str] = []

        is_scam = False

        # 1. Check for scam & illicit phrases
        for pattern in SCAM_FRAUD_PATTERNS:
            match = pattern.search(combined_text)
            if match:
                is_scam = True
                risk_signals.append(f"Illicit pattern detected: '{match.group(0)}'")

        # 2. Check link safety indicators
        if link_inspection:
            if not link_inspection.is_safe:
                is_scam = True
                risk_signals.extend(link_inspection.risk_reasons)
            elif link_inspection.is_suspicious:
                risk_signals.extend(link_inspection.risk_reasons)

            if link_inspection.is_provider_domain:
                is_provider_domain = True
            if link_inspection.is_partner_domain:
                is_partner_domain = True

        # 3. Source credibility evaluation
        source_points = 10  # default baseline for standard public web / reddit / telegram
        ident_lower = (source_identifier or "").lower()

        if any(
            official in ident_lower
            for official in ("openai.com", "anthropic.com", "x.ai", "github.blog", "deepmind.google")
        ):
            source_points = 25
            trust_signals.append("Source is an official company announcement channel.")
        elif any(sub in ident_lower for sub in ("claudeai", "chatgpt", "grok", "github", "perplexityai")):
            source_points = 20
            trust_signals.append("Source is a primary dedicated community for the AI provider.")
        elif source_type == "rss":
            source_points = 15
            trust_signals.append("Source is an established RSS feed.")

        # 4. Destination domain credibility
        dest_points = 0
        if is_provider_domain:
            dest_points = 15
            trust_signals.append("Destination URL directs directly to the official provider domain.")
        elif is_partner_domain:
            dest_points = 10
            trust_signals.append("Destination URL directs to an authorized educational or verification partner.")
        elif link_inspection and link_inspection.is_accessible:
            dest_points = 5
            trust_signals.append("Destination URL is accessible.")

        # Calculate preliminary score
        score = source_points + dest_points

        # Scam overrides everything
        if is_scam:
            score = 0
            is_authentic = False
        else:
            if is_provider_domain or is_partner_domain:
                is_authentic = True
            elif score >= 25 and not risk_signals:
                is_authentic = True
            else:
                is_authentic = False

        # Clamp between 0 and 30
        score = max(0, min(30, score))

        return AuthenticityResult(
            is_authentic=is_authentic,
            is_scam=is_scam,
            authenticity_score=score,
            trust_signals=trust_signals,
            risk_signals=risk_signals,
        )
