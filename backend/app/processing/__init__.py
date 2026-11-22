"""Processing module for extraction, classification, and deduplication."""

from app.processing.normalizer import (
    extract_domain,
    extract_urls,
    normalize_text,
    normalize_url,
)

__all__ = [
    "normalize_text",
    "normalize_url",
    "extract_domain",
    "extract_urls",
]
