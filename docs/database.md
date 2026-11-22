# Priya — Database Schema & Data Models

This document details the database schema, models, constraints, and relationships implemented in Priya using SQLAlchemy 2.x declarative models and Alembic migrations on PostgreSQL.

## 1. Domain Entities & Tables

### `providers`
Represents foundational AI companies offering generative AI models and services.
- `id` (INTEGER, Primary Key)
- `name` (VARCHAR(100), Unique, Not Null, Indexed) — Canonical display name (e.g., "Anthropic", "OpenAI").
- `slug` (VARCHAR(100), Unique, Not Null, Indexed) — URL-safe canonical slug (e.g., "anthropic").
- `website_url` (VARCHAR(255), Nullable)
- `description` (TEXT, Nullable)
- `aliases` (JSONB, Default `[]`) — Alternative names and spellings.
- `is_active` (BOOLEAN, Default `True`, Indexed)
- `created_at`, `updated_at` (TIMESTAMPTZ, Default UTC)

### `plans`
Represents specific subscription plans belonging to a provider.
- `id` (INTEGER, Primary Key)
- `provider_id` (INTEGER, Foreign Key `providers.id` ON DELETE CASCADE, Not Null, Indexed)
- `name` (VARCHAR(100), Not Null) — (e.g., "Claude Pro", "ChatGPT Plus").
- `slug` (VARCHAR(100), Not Null, Indexed) — (e.g., "claude-pro").
- `description` (TEXT, Nullable)
- `aliases` (JSONB, Default `[]`)
- `is_active` (BOOLEAN, Default `True`, Indexed)
- `created_at`, `updated_at` (TIMESTAMPTZ, Default UTC)
- **Constraint**: `UNIQUE(provider_id, slug)`

### `sources`
Monitored external channels, communities, websites, or feeds.
- `id` (INTEGER, Primary Key)
- `name` (VARCHAR(150), Not Null)
- `source_type` (ENUM: `telegram`, `reddit`, `website`, `rss`, Indexed)
- `identifier` (VARCHAR(255), Not Null, Indexed) — (e.g., `@claude_ai_deals`, `r/ChatGPT`).
- `url` (VARCHAR(500), Nullable)
- `description` (TEXT, Nullable)
- `is_active` (BOOLEAN, Default `True`, Indexed)
- `collection_interval_seconds` (INTEGER, Default `3600`)
- `last_collected_at`, `last_successful_collection_at`, `last_error_at` (TIMESTAMPTZ, Nullable)
- `last_error_message` (TEXT, Nullable)
- `created_at`, `updated_at` (TIMESTAMPTZ, Default UTC)
- **Constraint**: `UNIQUE(source_type, identifier)`

### `discovered_items`
Raw content gathered from external sources prior to or following processing.
- `id` (INTEGER, Primary Key)
- `source_id` (INTEGER, Foreign Key `sources.id` ON DELETE CASCADE, Not Null, Indexed)
- `external_id` (VARCHAR(255), Not Null, Indexed) — Message ID, post ID, or URL hash.
- `content_type` (VARCHAR(50), Default `post`) — `telegram_message`, `reddit_post`, etc.
- `title` (VARCHAR(500), Nullable)
- `content` (TEXT, Not Null)
- `author` (VARCHAR(150), Nullable)
- `original_url` (VARCHAR(1000), Nullable)
- `published_at` (TIMESTAMPTZ, Nullable)
- `discovered_at` (TIMESTAMPTZ, Default UTC, Indexed)
- `content_hash` (VARCHAR(64), Nullable, Indexed) — SHA-256 hash for deduplication.
- `raw_metadata` (JSONB, Default `{}`)
- `processing_status` (ENUM: `pending`, `processing`, `processed`, `irrelevant`, `failed`, Indexed)
- `processed_at` (TIMESTAMPTZ, Nullable)
- `processing_error` (TEXT, Nullable)
- `created_at`, `updated_at` (TIMESTAMPTZ, Default UTC)
- **Constraint**: `UNIQUE(source_id, external_id)`

### `promotions`
Canonical promotional deal for an AI subscription.
- `id` (INTEGER, Primary Key)
- `provider_id` (INTEGER, Foreign Key `providers.id` ON DELETE RESTRICT, Not Null, Indexed)
- `plan_id` (INTEGER, Foreign Key `plans.id` ON DELETE SET NULL, Nullable, Indexed)
- `title` (VARCHAR(255), Not Null)
- `description` (TEXT, Nullable)
- `offer_type` (ENUM: `free_trial`, `free_subscription`, `discount`, `student_offer`, `referral`, `partner_offer`, `giveaway`, `unknown`, Indexed)
- `discount_percentage` (NUMERIC(5, 2), Nullable)
- `duration_days` (INTEGER, Nullable)
- `promo_code` (VARCHAR(100), Nullable, Indexed)
- `eligible_countries` (JSONB, Default `[]`) — ISO 3166-1 alpha-2 codes (e.g. `["NG", "US"]`).
- `excluded_countries` (JSONB, Default `[]`)
- `account_requirements` (JSONB, Default `{}`)
- `payment_required` (BOOLEAN, Nullable)
- `starts_at`, `expires_at` (TIMESTAMPTZ, Nullable, `expires_at` Indexed)
- `status` (ENUM: `unverified`, `likely_valid`, `verified`, `expired`, `restricted`, `invalid`, Indexed)
- `confidence_score` (INTEGER, Default `0`, Indexed)
- `first_discovered_at`, `last_discovered_at` (TIMESTAMPTZ, Default UTC, Indexed)
- `last_checked_at` (TIMESTAMPTZ, Nullable)
- `created_at`, `updated_at` (TIMESTAMPTZ, Default UTC)
- **Constraint**: `CHECK (confidence_score >= 0 AND confidence_score <= 100)`

### `promotion_discoveries`
Corroboration junction table associating promotions with discovered items.
- `id` (INTEGER, Primary Key)
- `promotion_id` (INTEGER, Foreign Key `promotions.id` ON DELETE CASCADE, Not Null, Indexed)
- `discovered_item_id` (INTEGER, Foreign Key `discovered_items.id` ON DELETE CASCADE, Not Null, Indexed)
- `created_at` (TIMESTAMPTZ, Default UTC)
- **Constraint**: `UNIQUE(promotion_id, discovered_item_id)`

### `promotion_links`
Target URLs, referral links, and terms associated with promotions.
- `id` (INTEGER, Primary Key)
- `promotion_id` (INTEGER, Foreign Key `promotions.id` ON DELETE CASCADE, Not Null, Indexed)
- `original_url` (TEXT, Not Null)
- `normalized_url` (TEXT, Not Null, Indexed)
- `destination_domain` (VARCHAR(255), Not Null, Indexed)
- `link_type` (ENUM: `redemption`, `official_announcement`, `referral`, `source_post`, `terms_and_conditions`, `other`)
- `is_primary` (BOOLEAN, Default `False`)
- `is_active` (BOOLEAN, Default `True`)
- `created_at`, `updated_at` (TIMESTAMPTZ, Default UTC)

### `verification_checks`
Historical records of verification operations performed on promotions.
- `id` (INTEGER, Primary Key)
- `promotion_id` (INTEGER, Foreign Key `promotions.id` ON DELETE CASCADE, Not Null, Indexed)
- `check_type` (VARCHAR(50), Not Null, Indexed)
- `result` (VARCHAR(50), Not Null) — `pass`, `fail`, `warning`
- `status` (VARCHAR(50), Not Null) — `completed`, `failed`, `pending`
- `details` (JSONB, Default `{}`)
- `checked_at` (TIMESTAMPTZ, Default UTC, Indexed)

### `eligibility_rules`
Structured country and eligibility restrictions.
- `id` (INTEGER, Primary Key)
- `promotion_id` (INTEGER, Foreign Key `promotions.id` ON DELETE CASCADE, Not Null, Indexed)
- `rule_type` (ENUM: `included_country`, `excluded_country`, `new_accounts_only`, `existing_subscribers_only`, `student_verification`, `payment_method_required`, `account_age_requirement`, `redemption_limit`, `other`)
- `country_code` (VARCHAR(2), Nullable)
- `description` (TEXT, Not Null)
- `evidence_url` (VARCHAR(1000), Nullable)
- `created_at`, `updated_at` (TIMESTAMPTZ, Default UTC)

### `notifications`
Alert records for discovered or updated opportunities.
- `id` (INTEGER, Primary Key)
- `promotion_id` (INTEGER, Foreign Key `promotions.id` ON DELETE CASCADE, Nullable, Indexed)
- `channel` (VARCHAR(50), Not Null)
- `notification_type` (ENUM: `new_promotion`, `promotion_updated`, `promotion_expiring`, `verification_status_changed`)
- `status` (ENUM: `pending`, `sent`, `failed`, Indexed)
- `message` (TEXT, Not Null)
- `sent_at` (TIMESTAMPTZ, Nullable)
- `created_at` (TIMESTAMPTZ, Default UTC, Indexed)

### `app_settings`
Dynamic key-value configuration.
- `id` (INTEGER, Primary Key)
- `key` (VARCHAR(100), Unique, Not Null, Indexed)
- `value` (JSONB, Not Null)
- `description` (TEXT, Nullable)
- `updated_at` (TIMESTAMPTZ, Default UTC)

## 2. Migration and Seeding

- Migrations are managed via Alembic:
  ```bash
  make db-migrate
  make db-rollback
  ```
- Seed operation:
  ```bash
  make db-seed
  ```
  The seed mechanism is completely idempotent. It populates all seven providers (Anthropic, OpenAI, xAI, Google, Perplexity, Cursor, GitHub) and their canonical subscription plans without duplicating existing records.
