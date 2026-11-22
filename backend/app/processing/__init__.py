"""Processing module for extraction, classification, and deduplication."""

from app.processing.classifier import ClassificationResult, EntityClassifier
from app.processing.deduplicator import PromotionDeduplicator
from app.processing.extractor import ExtractedOffer, OfferExtractor
from app.processing.filters import ContentFilter, FilterResult
from app.processing.normalizer import (
    extract_domain,
    extract_urls,
    normalize_text,
    normalize_url,
)
from app.processing.pipeline import PipelineStats, ProcessingPipeline

__all__ = [
    "normalize_text",
    "normalize_url",
    "extract_domain",
    "extract_urls",
    "ContentFilter",
    "FilterResult",
    "EntityClassifier",
    "ClassificationResult",
    "OfferExtractor",
    "ExtractedOffer",
    "PromotionDeduplicator",
    "ProcessingPipeline",
    "PipelineStats",
]
