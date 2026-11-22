"""Text and URL normalization utilities for promotion processing."""

import html
import re
from typing import List, Set
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# Common tracking parameters to strip for clean canonical comparison
TRACKING_PARAMS: Set[str] = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "gbraid",
    "wbraid",
    "ref_src",
    "ref",
    "yclid",
    "mc_eid",
    "igshid",
    "_hsenc",
    "_hsmi",
}

# Regex for finding HTTP/HTTPS URLs in unformatted text
URL_REGEX = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """
    Clean, decode HTML entities, normalize unicode whitespace and quotes.
    Preserves original meaning without destructive alterations.
    """
    if not text:
        return ""

    # Decode HTML entities (e.g. &amp;, &quot;, &#39;)
    decoded = html.unescape(text)
    if "&" in decoded:
        decoded = html.unescape(decoded)

    # Normalize unicode quotation marks and dashes
    cleaned = (
        decoded.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u200b", "")  # zero-width space
        .replace("\ufeff", "")  # byte order mark
    )

    # Collapse multi-newlines and multi-spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()


def normalize_url(url: str) -> str:
    """
    Normalize URL by lowercasing scheme/host, removing tracking parameters,
    and standardizing format for duplicate detection.
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return url.strip()

        # Lowercase scheme and netloc (domain)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        # Remove default ports
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        # Strip tracking query parameters while preserving promo codes & intent
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        filtered_params = {
            k: v for k, v in query_params.items() if k.lower() not in TRACKING_PARAMS
        }

        new_query = urlencode(filtered_params, doseq=True)

        # Standardize path
        path = parsed.path
        if not path:
            path = "/"
        elif len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        clean_url = urlunparse((scheme, netloc, path, parsed.params, new_query, ""))
        return clean_url
    except Exception:
        return url.strip()


def extract_domain(url: str) -> str:
    """Extract clean lowercase destination domain from URL."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.split(":")[0]  # strip port if present
    except Exception:
        return ""


def extract_urls(text: str) -> List[str]:
    """Find and return all valid URLs within a block of text."""
    if not text:
        return []
    matches = URL_REGEX.findall(text)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for match in matches:
        clean = match.rstrip(".,;!?'\")>]}")
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result
