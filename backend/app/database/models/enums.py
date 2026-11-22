"""Domain enumerations for database models."""

import enum


class SourceType(str, enum.Enum):
    TELEGRAM = "telegram"
    REDDIT = "reddit"
    WEBSITE = "website"
    RSS = "rss"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    IRRELEVANT = "irrelevant"
    FAILED = "failed"


class OfferType(str, enum.Enum):
    FREE_TRIAL = "free_trial"
    FREE_SUBSCRIPTION = "free_subscription"
    DISCOUNT = "discount"
    STUDENT_OFFER = "student_offer"
    REFERRAL = "referral"
    PARTNER_OFFER = "partner_offer"
    GIVEAWAY = "giveaway"
    UNKNOWN = "unknown"


class PromotionStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    LIKELY_VALID = "likely_valid"
    VERIFIED = "verified"
    EXPIRED = "expired"
    RESTRICTED = "restricted"
    INVALID = "invalid"


class LinkType(str, enum.Enum):
    REDEMPTION = "redemption"
    OFFICIAL_ANNOUNCEMENT = "official_announcement"
    REFERRAL = "referral"
    SOURCE_POST = "source_post"
    TERMS_AND_CONDITIONS = "terms_and_conditions"
    OTHER = "other"


class EligibilityRuleType(str, enum.Enum):
    INCLUDED_COUNTRY = "included_country"
    EXCLUDED_COUNTRY = "excluded_country"
    NEW_ACCOUNTS_ONLY = "new_accounts_only"
    EXISTING_SUBSCRIBERS_ONLY = "existing_subscribers_only"
    STUDENT_VERIFICATION = "student_verification"
    PAYMENT_METHOD_REQUIRED = "payment_method_required"
    ACCOUNT_AGE_REQUIREMENT = "account_age_requirement"
    REDEMPTION_LIMIT = "redemption_limit"
    OTHER = "other"


class NotificationType(str, enum.Enum):
    NEW_PROMOTION = "new_promotion"
    PROMOTION_UPDATED = "promotion_updated"
    PROMOTION_EXPIRING = "promotion_expiring"
    VERIFICATION_STATUS_CHANGED = "verification_status_changed"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
