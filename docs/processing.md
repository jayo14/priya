# Priya — Phase 3: Extraction, Classification & Deduplication

This document details the deterministic processing pipeline implemented in Phase 3 of Priya.

## 1. Objective and Pipeline Lifecycle

The processing pipeline transforms unorganized, raw text collected in `discovered_items` into structured, validated canonical `promotions`.

```text
Raw DiscoveredItem (Status: PENDING)
                 │
                 ▼
     [ Stage 1: Normalization ]
     - HTML entity unescaping (&amp; -> &)
     - Unicode cleanup & whitespace standardization
     - URL tracking param stripping (utm_*, fbclid)
                 │
                 ▼
     [ Stage 2: Filtering & Spam Rejection ]
     - Positive deal keyword detection
     - Negative scam/illicit trading patterns blocked
     - Marks non-deals as IRRELEVANT
                 │
                 ▼
     [ Stage 3: Entity Classification ]
     - Recognizes 7 AI Providers (Anthropic, OpenAI, xAI, Google, Perplexity, Cursor, GitHub)
     - Recognizes specific Subscription Plans (Claude Pro, ChatGPT Plus, Grok Premium, etc.)
     - Classifies OfferType (free_trial, free_subscription, discount, student_offer, etc.)
                 │
                 ▼
     [ Stage 4: Structured Offer Extraction ]
     - Extracts promotional codes (e.g. SPRING50)
     - Extracts discount percentages & duration in days
     - Extracts geographic eligibility (Nigeria / Global)
     - Extracts payment & account requirements
     - Computes baseline confidence score (0 to 100)
                 │
                 ▼
     [ Stage 5: Deduplication & Source Corroboration ]
     - Matches existing active promotions by promo code, URL, or domain/plan
     - If matched: Corroborates existing promotion (links discovery, boosts confidence)
     - If new: Creates new canonical Promotion & primary PromotionLink
                 │
                 ▼
   DiscoveredItem marked as PROCESSED
```

---

## 2. Pipeline Modules

### 1. Normalizer (`app.processing.normalizer`)
- `normalize_text(text: str) -> str`: Unescapes HTML entities, handles double-encoding, strips zero-width spaces, standardizes curly quotes.
- `normalize_url(url: str) -> str`: Removes marketing/tracking query parameters (`utm_*`, `fbclid`, `gclid`, `ref_src`, `yclid`, etc.) while strictly preserving redemption query parameters and promo codes.
- `extract_domain(url: str) -> str`: Normalizes lowercase destination domain without `www.` prefix.
- `extract_urls(text: str) -> list[str]`: Regex scanner for all HTTP/HTTPS links embedded in message body.

### 2. Content Filter (`app.processing.filters`)
- Positive patterns detect genuine subscription incentives (`free trial`, `discount`, `promo code`, `student pack`, `voucher`).
- Negative patterns block spam, scams, and illicit account trading (`buy claude account`, `carding`, `cookie method`, `cracked accounts`, `email:pass`).
- Items failing filter are tagged `IRRELEVANT` with the rejection reason logged, stopping wasteful processing.

### 3. Entity Classifier (`app.processing.classifier`)
- Deterministic regex and token matching for all seven supported AI providers and their plans.
- Assigns canonical `provider_id` and `plan_id` via database lookup.
- Classifies `OfferType`:
  - `free_trial`: Time-limited trial of subscription.
  - `free_subscription`: Extended free access (e.g., 6 months free).
  - `discount`: Percentage or fixed price reduction.
  - `student_offer`: Verified student program (e.g., GitHub Student Pack, SheerID).
  - `referral`: User referral codes.
  - `partner_offer`: Bundle or third-party promotion.
  - `giveaway`: Sweepstakes or raffle.

### 4. Parameter Extractor (`app.processing.extractor`)
- **Promo Codes**: Extracts alphanumeric promo codes (`SPRINGAI2026`).
- **Discounts**: Regex extraction for percentages (`50% off`).
- **Duration**: Converts months/days/years into normalized days (`3 months` -> 90 days).
- **Country Eligibility**: Detects mentions of Nigeria (`NG`), US, UK, Global.
- **Payment Requirements**: Evaluates whether credit card / payment method is required.
- **Account Requirements**: Detects `new_accounts_only` vs existing subscribers.
- **Confidence Scoring**: Assigns deterministic 0-100 score based on corroborated signals.

### 5. Deduplication & Corroboration (`app.processing.deduplicator`)
- Matches against existing canonical promotions in database:
  - Match by promo code.
  - Match by normalized redemption URL.
  - Match by provider + plan + destination domain.
- **Source Corroboration**: When the same offer is seen in multiple Telegram channels or Reddit posts, Priya associates all discoveries with the single canonical promotion rather than duplicating it. Each additional corroboration increases the confidence score.

---

## 3. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/processing/run` | Execute extraction pipeline on pending discovered items. |
| `GET` | `/api/v1/processing/stats` | Status counts across lifecycle (pending, processed, irrelevant, failed). |
| `GET` | `/api/v1/promotions` | List canonical promotions with filters for provider, plan, status, offer type, and `nigeria_eligible`. |
| `GET` | `/api/v1/promotions/{id}` | Retrieve full promotion details, corroborating discoveries, and links. |
