"""Safe URL inspection, redirect resolution, and SSRF prevention module."""

import ipaddress
import re
import socket
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import httpx

from app.core.logging import setup_logging

logger = setup_logging()

# Official domains for each supported AI provider
OFFICIAL_PROVIDER_DOMAINS: Dict[str, Set[str]] = {
    "anthropic": {"anthropic.com", "claude.ai", "support.anthropic.com"},
    "openai": {"openai.com", "chatgpt.com", "help.openai.com"},
    "xai": {"x.ai", "grok.com", "x.com", "twitter.com"},
    "google": {
        "google.com",
        "deepmind.google",
        "gemini.google.com",
        "one.google.com",
        "ai.google.dev",
        "cloud.google.com",
    },
    "perplexity": {"perplexity.ai", "pplx.ai"},
    "cursor": {"cursor.com", "cursor.sh"},
    "github": {"github.com", "github.blog", "education.github.com", "copilot.github.com"},
}

# Recognized legitimate verification / education / partner portals
AUTHORIZED_PARTNER_DOMAINS: Set[str] = {
    "sheerid.com",
    "services.sheerid.com",
    "unidays.com",
    "myunidays.com",
    "studentbeans.com",
    "microsoft.com",
    "azure.microsoft.com",
    "aws.amazon.com",
    "apple.com",
    "apps.apple.com",
    "play.google.com",
    "stripe.com",
}

# Known URL shorteners that conceal destination
KNOWN_URL_SHORTENERS: Set[str] = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "is.gd",
    "buff.ly",
    "ow.ly",
    "rebrand.ly",
    "cutt.ly",
    "shorturl.at",
    "rb.gy",
}

# Suspicious TLDs frequently abused for phishing scams
SUSPICIOUS_TLDS: Set[str] = {
    ".top",
    ".xyz",
    ".tk",
    ".ml",
    ".ga",
    ".cf",
    ".gq",
    ".buzz",
    ".fit",
    ".work",
    ".online",
    ".site",
    ".click",
}


@dataclass
class LinkInspectionResult:
    """Detailed audit record of an inspected URL."""

    original_url: str
    is_safe: bool = True
    is_accessible: bool = False
    status_code: Optional[int] = None
    final_url: str = ""
    final_domain: str = ""
    redirect_chain: List[str] = field(default_factory=list)
    is_provider_domain: bool = False
    is_partner_domain: bool = False
    is_url_shortener: bool = False
    is_suspicious: bool = False
    risk_reasons: List[str] = field(default_factory=list)
    content_type: Optional[str] = None


class SafeLinkValidator:
    """Validates URLs against SSRF, inspects redirect chains, and classifies destination safety."""

    def __init__(self, timeout: float = 5.0, max_redirects: int = 5):
        self.timeout = timeout
        self.max_redirects = max_redirects

    @staticmethod
    def is_private_ip(ip_str: str) -> bool:
        """Check whether an IP address belongs to private, loopback, or reserved ranges."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return (
                ip.is_private
                or ip.is_loopback
                or ip.is_reserved
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_unspecified
            )
        except ValueError:
            return False

    def check_ssrf(self, hostname: str, resolve_dns: bool = True) -> tuple[bool, Optional[str]]:
        """Verify that a hostname does not resolve to private or internal network interfaces.

        Returns (is_safe, error_reason).
        """
        # Strip port if present
        if ":" in hostname:
            hostname = hostname.split(":")[0]

        # Check IP literal directly
        if self.is_private_ip(hostname):
            return False, f"Host '{hostname}' is a private or reserved IP address."

        # Reject common localhost aliases
        if hostname.lower() in ("localhost", "0.0.0.0", "127.0.0.1", "::1"):
            return False, f"Host '{hostname}' resolves to loopback interface."

        if not resolve_dns:
            return True, None

        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, socktype, proto, canonname, sockaddr in addr_info:
                ip_str = sockaddr[0]
                if self.is_private_ip(ip_str):
                    return False, f"Hostname '{hostname}' resolves to private IP address {ip_str}."
        except socket.gaierror:
            # Cannot resolve hostname: not an SSRF breach against local network
            return True, None
        except Exception as exc:
            return False, f"Address validation error: {exc}"

        return True, None

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract lowercase domain name without port or www prefix."""
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.split(":")[0].lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return ""

    def evaluate_domain_safety(
        self, domain: str, provider_slug: Optional[str] = None
    ) -> tuple[bool, bool, bool, bool, List[str]]:
        """Evaluate domain categorization and potential phishing indicators.

        Returns: (is_provider, is_partner, is_shortener, is_suspicious, reasons)
        """
        domain = domain.lower()
        reasons: List[str] = []

        is_provider = False
        if provider_slug and provider_slug in OFFICIAL_PROVIDER_DOMAINS:
            official_domains = OFFICIAL_PROVIDER_DOMAINS[provider_slug]
            is_provider = any(
                domain == d or domain.endswith("." + d) for d in official_domains
            )

        # Also check across any official AI provider domain
        all_official = set().union(*OFFICIAL_PROVIDER_DOMAINS.values())
        if not is_provider and any(domain == d or domain.endswith("." + d) for d in all_official):
            is_provider = True

        is_partner = any(
            domain == d or domain.endswith("." + d) for d in AUTHORIZED_PARTNER_DOMAINS
        )
        is_shortener = domain in KNOWN_URL_SHORTENERS

        is_suspicious = False

        # Brand impersonation detection: domain contains brand name but is NOT an official domain
        brand_tokens = ["claude", "anthropic", "chatgpt", "openai", "perplexity", "copilot", "deepmind"]
        for token in brand_tokens:
            if token in domain and not is_provider:
                is_suspicious = True
                reasons.append(
                    f"Possible brand impersonation: '{domain}' contains '{token}' but is not an official domain."
                )

        # Suspicious TLD check for non-official, non-partner domains
        if not is_provider and not is_partner:
            for tld in SUSPICIOUS_TLDS:
                if domain.endswith(tld):
                    is_suspicious = True
                    reasons.append(f"Domain uses high-risk TLD '{tld}'.")
                    break

        # Check for multiple hyphens or deceptive character combinations
        if domain.count("-") >= 3 and not is_provider:
            is_suspicious = True
            reasons.append("Domain contains excessive hyphens indicative of phishing lures.")

        return is_provider, is_partner, is_shortener, is_suspicious, reasons

    def inspect_url(
        self,
        url: str,
        provider_slug: Optional[str] = None,
        perform_network_check: bool = True,
    ) -> LinkInspectionResult:
        """Inspect a URL for safety, follow redirect chains, and evaluate domain safety."""
        result = LinkInspectionResult(
            original_url=url,
            final_url=url,
            final_domain=self.extract_domain(url),
        )

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            result.is_safe = False
            result.is_suspicious = True
            result.risk_reasons.append(
                f"Unsupported URL scheme '{parsed.scheme}'. Only http/https are permitted."
            )
            return result

        hostname = parsed.hostname
        if not hostname:
            result.is_safe = False
            result.risk_reasons.append("Missing hostname in URL.")
            return result

        # Check SSRF on initial hostname
        ssrf_safe, ssrf_err = self.check_ssrf(hostname, resolve_dns=perform_network_check)
        if not ssrf_safe:
            result.is_safe = False
            result.is_suspicious = True
            result.risk_reasons.append(f"SSRF violation: {ssrf_err}")
            return result

        # Initial domain evaluation
        (
            result.is_provider_domain,
            result.is_partner_domain,
            result.is_url_shortener,
            is_suspicious,
            reasons,
        ) = self.evaluate_domain_safety(result.final_domain, provider_slug)

        if is_suspicious:
            result.is_suspicious = True
            result.risk_reasons.extend(reasons)

        if not perform_network_check:
            result.is_accessible = True
            return result

        # Follow redirects safely with httpx
        try:
            current_url = url
            headers = {"User-Agent": "PriyaDealScout/1.0 (+https://github.com/promoscout)"}

            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=False,
                verify=True,
                headers=headers,
            ) as client:
                redirect_count = 0

                while redirect_count < self.max_redirects:
                    resp = client.head(current_url)
                    result.status_code = resp.status_code
                    result.content_type = resp.headers.get("content-type")

                    # Handle redirects (301, 302, 303, 307, 308)
                    if resp.is_redirect and "location" in resp.headers:
                        location = resp.headers["location"]
                        # Resolve relative redirect
                        next_url = str(httpx.URL(current_url).join(location))
                        result.redirect_chain.append(next_url)

                        # Inspect next hop for SSRF
                        next_parsed = urlparse(next_url)
                        if next_parsed.hostname:
                            hop_safe, hop_err = self.check_ssrf(next_parsed.hostname)
                            if not hop_safe:
                                result.is_safe = False
                                result.is_suspicious = True
                                result.risk_reasons.append(
                                    f"SSRF violation during redirect: {hop_err}"
                                )
                                return result

                        current_url = next_url
                        redirect_count += 1
                    else:
                        break

                result.final_url = current_url
                result.final_domain = self.extract_domain(current_url)
                result.is_accessible = 200 <= resp.status_code < 400

                # Re-evaluate final destination domain
                (
                    is_prov,
                    is_part,
                    is_short,
                    is_susp,
                    final_reasons,
                ) = self.evaluate_domain_safety(result.final_domain, provider_slug)

                result.is_provider_domain = is_prov
                result.is_partner_domain = is_part
                result.is_url_shortener = is_short
                if is_susp:
                    result.is_suspicious = True
                    result.risk_reasons.extend(final_reasons)

        except httpx.RequestError as exc:
            result.is_accessible = False
            result.risk_reasons.append(f"HTTP request error: {str(exc)}")
        except Exception as exc:
            result.is_accessible = False
            result.risk_reasons.append(f"Unexpected inspection error: {str(exc)}")

        return result
