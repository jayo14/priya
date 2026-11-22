Can I build a tool that searcch across multiple telegram channel, and reddit posts for free claude pro links, and gives gets them for me so that I can use those promos to subscribe to claude pro. Not just claude pro, but chatgpt (plus, go, or pro), grok pro, etc



Yes. You can build this, and I actually think it's a worthwhile project.

I'd approach it as a **subscription promotion discovery engine**: an automated tool that monitors Telegram channels, Reddit communities, and other public sources for legitimate promotional offers that give you access to premium AI subscriptions for free or at a discount.

The important distinction: you're not building another search engine. You're building a tool that finds opportunities, checks whether they're genuine, verifies whether they're still usable, and brings the best ones to you.

I'd call it something like **PromoHunter**, **SubScout**, or **FreeTier**.

## **1. What the tool should do**

Imagine opening your dashboard and seeing:

**PromoScout**

Monitoring

AI SUBSCRIPTION DEALS · LIVE DISCOVERY

# **12**

New offers

# **5**

Verified

# **3**

Expiring

**Latest discoveries**

[Bull Theory (@BullTheoryio) on X](https://images.openai.com/static-rsc-4/oKGxWNBt7fGvBVhXCj1CTv6SLDyoM6iYaL4pEMURc-RYZ4e-YKsqEkVDtejidr9h-1XfEvVRkIK2bJtp5pT399kk-eVfXcnvqvJu18PGx9wqoWX1kONWEnSth9Jthqef7EDVpeLogBpp8Vn0L8dUoZsJ2VecusLkcI8_MHSxEn8?purpose=inline)

**Claude Pro**

12-month promotional offer

Verified link

[File:ChatGPT-Logo.svg - Wikimedia Commons](https://images.openai.com/static-rsc-4/iIwQvt6lHcQFgj7BguLsxseHBBrUFkMcXG5YNkmFFW4lfJVJx4j903Vj6U7eh4G1RxYAM5rcotiwXgmy1bpDjVeUGauxGKEaWacWqJ6UawIltioycNX9Ru1jiDHQJ6b718nA6kh8GV93DvtXMfEhj4O5IYd7IWQ4fxKOZEoQ6CY?purpose=inline)

**ChatGPT Plus**

Potential promotional access

Needs verification

[xAI Grok - Conversational AI Tool | Web3Lists](https://images.openai.com/static-rsc-4/-wW12bbJ9LJDkYgnArNbeteQlZf41sBMDrbMXLtI0Eq1ayxk6fdxYjgnR2aNKklCqLjo3Rm-5DxRLOMxSjpEet-6fj4iZrs2vmCl9SJGms2D0-obSLAeItXmhio3v6af8GVkAgKQ3ditxVbHSNYwqJqmoYQO8VlPcDub1fcMupE?purpose=inline)

**Grok**

Discounted subscription offer

Unverified

Illustrative dashboard, not live offers.

## **2. Platforms and sources to monitor**

I'd support these initially:

| Platform       | What to discover              |
| -------------- | ----------------------------- |
| Claude         | Pro, Max promotions           |
| ChatGPT        | Go, Plus, Pro promotions      |
| Grok           | Premium, SuperGrok promotions |
| Google Gemini  | Google AI Pro promotions      |
| Perplexity     | Pro promotions                |
| Cursor         | Pro promotions                |
| GitHub Copilot | Pro promotions                |

Sources:

- Telegram public channels and groups.
- Reddit posts and comments.
- Official company announcements.
- Partner promotions and student offers.
- Public deal-sharing communities.

For Reddit, monitor relevant subreddits such as r/ClaudeAI, r/ChatGPT, r/Grok, r/ArtificialIntelligence and deal-related communities.

For Telegram, allow you to configure channel usernames and add channels to your monitoring list.

**One important discovery:** Not every promotion is available to everyone. For example, OpenAI's promotional offers can have country, account-age, existing-subscription and partner-specific restrictions. Some codes are explicitly non-transferable.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://help.openai.com\&sz=32)

OpenAI Help Center+2



Claude also says it doesn't have standing discounts for individual Pro subscriptions, although occasional promotions happen.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.claude.com\&sz=32)

Claude Help Center



Grok's current referral programme has geographical restrictions that exclude Nigeria.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://x.ai\&sz=32)

SpaceXSI



This is precisely why eligibility checking should be a major feature.

## **3. The intelligence layer**

This is where I'd make the application interesting.

A normal scraper finds links. Your application should understand what it finds.

Every discovered promotion should go through these stages:

**1. Discovery**

Telegram, Reddit, websites, announcements

**2. Extraction**

Extract product, plan, link, duration, requirements

**3. Validation**

Check link safety, destination, expiry and availability

**4. Eligibility assessment**

Country, account requirements, plan and payment restrictions

**5. Notification**

Show the offer and provide its original redemption link

### **Promotion scoring**

I'd give every offer a score based on:

- Authenticity: Is the source trustworthy?
- Availability: Does the link still work?
- Value: How many months of access does it provide?
- Eligibility: Can someone in Nigeria redeem it?
- Risk: Is it a suspicious link, account-sharing scheme or stolen code?
- Expiry: How much time remains?

Possible statuses:

- Verified: Officially confirmed and redemption page confirms the offer.
- Likely valid: Credible source, but redemption hasn't been confirmed.
- Unverified: Insufficient evidence.
- Expired: No longer available.
- Restricted: Not eligible in your region or for your account.

Don't automatically claim an offer is valid just because its URL returns HTTP 200.

## **4. Recommended technical architecture**

Given your existing development skills, I'd build it with:

## **PromoScout architecture**

**Frontend**

Next.js + TypeScript + Tailwind CSS

Dashboard, filters, offer details, saved promotions

**Backend API**

Python + FastAPI

Authentication, promotion management, eligibility and validation

**Collectors**

Telethon, Reddit API, RSS, web sources

**Processing**

Python, extraction, deduplication, AI classification

**Database**

PostgreSQL or SQLite initially

**Scheduler**

APScheduler or Celery

### **How to collect data**

**Telegram**

- Telethon for monitoring channels your authorized Telegram account can access.
- Telegram Bot API for channels where your bot has been added and granted appropriate access.
- Configurable channel lists.

**Reddit**

- Reddit API for posts and comments.
- Search queries for keywords such as `Claude Pro free`, `ChatGPT Plus promo`, `Grok subscription discount`.
- Monitor new submissions and relevant discussions.

Respect platform API limits, access permissions and scraping policies. Don't attempt to access private channels or communities without authorization.

### **AI processing**

You don't need an expensive LLM for everything.

Use:

- Regex and keyword matching for initial filtering.
- Python for URL parsing and deduplication.
- An optional LLM for understanding complicated promotion conditions.
- HTTP checks and safe browser inspection for link validation.

You can even make the AI provider configurable.

## **5. Features I'd include**

| Feature                            | Priority |
| ---------------------------------- | -------- |
| Telegram channel monitoring        | P0       |
| Reddit monitoring                  | P0       |
| Multiple AI subscription providers | P0       |
| Automatic promotion extraction     | P0       |
| Duplicate detection                | P0       |
| Expiry tracking                    | P0       |
| Nigeria eligibility assessment     | P0       |
| Direct redemption links            | P0       |
| Saved offers                       | P1       |
| Telegram notifications             | P1       |
| Automatic link rechecking          | P1       |
| Historical promotion database      | P2       |
| Community-submitted promotions     | P2       |

One important safety decision: the application should retrieve and organize redemption links, not automatically redeem codes, create accounts, bypass regional restrictions or reuse somebody else's personal referral.

## **6. Can you build it for free?**

Yes, for an initial version

You can start with:

| Component     | Free option                                    |
| ------------- | ---------------------------------------------- |
| Frontend      | Vercel                                         |
| Backend       | Local machine initially, then a free-tier host |
| Database      | SQLite / Supabase free tier                    |
| Telegram      | Telethon                                       |
| Reddit        | API access, subject to current limits          |
| Scheduling    | APScheduler                                    |
| Notifications | Telegram Bot API                               |
| AI extraction | Rules first; optional free model access        |

One caveat: continuous monitoring requires somewhere to run your collectors. Free hosting tiers can sleep, impose execution limits or restrict background workers. You could initially run the collector on your own computer and later move it to an always-on host.

## **7. My recommended MVP**

Don't start with seven subscription providers and sophisticated AI agents.

Start with three:

1. Claude Pro
2. ChatGPT Go / Plus / Pro
3. Grok

Monitor 10-20 Telegram channels and relevant Reddit communities.

Build the discovery, extraction, deduplication, eligibility and notification pipeline first.

Your first success criterion:

**A promotion gets posted in a Telegram channel at 2 AM. By 2:05 AM, your application has discovered it, extracted the link, assessed its credibility, checked its Nigerian eligibility and notified you.**

That's the product.

## **8. Three decisions before we design it**

I want to establish the actual product direction before generating the implementation prompts.

**1. Who is this product for?**

Just me. Private personal tool.

A public tool anyone can use.

Personal tool first, potentially a public product later.

**2. Which sources should it monitor?**

Select all that apply.

Telegram channels and groups

Reddit posts and comments

Websites and deal forums

Other public social media

**3. How should redemption work?**

Find offers, verify them and give me the links. I'll redeem manually.

Take me through the redemption process, with my confirmation at each step.

**4. Which subscriptions should it support?**

You can change this later.

Claude

ChatGPT

Grok

Gemini

Perplexity

Cursor

GitHub Copilot

Confirm product direction

My recommendation: **personal tool first, all three source types, manual redemption, and multiple providers from day one.**

Build something that saves you money, not something that costs you money to find discounts.



# **PromoScout: Architecture & Implementation Plan**



Personal product

Free-first

Manual redemption



My recommendation is to build PromoScout as a **personal AI-subscription promotion intelligence system**, not a general-purpose deal aggregator.

Its job is straightforward:

1. Continuously discover promotional offers.
2. Identify which AI subscription each offer concerns.
3. Extract redemption links and promotional conditions.
4. Detect duplicates and suspicious offers.
5. Determine whether the offer is potentially usable from Nigeria.
6. Notify you when a worthwhile opportunity appears.
7. Let you open the original redemption page and redeem it yourself.

The most important architectural decision: **discovery, validation and redemption are three separate responsibilities.**

We should never confuse finding a link with confirming that a promotion works.

## **1. Product scope**

### **Supported providers**

| Provider   | Plans/products to track                 |
| ---------- | --------------------------------------- |
| Anthropic  | Claude Pro, Max                         |
| OpenAI     | ChatGPT Go, Plus, Pro                   |
| xAI        | Grok subscriptions                      |
| Google     | Google AI Pro and relevant Gemini plans |
| Perplexity | Perplexity Pro                          |
| Cursor     | Cursor Pro                              |
| GitHub     | GitHub Copilot Pro                      |

The provider and plan catalogue should be database-driven, not hardcoded into the ingestion logic.

This allows us to add providers, rename plans and disable irrelevant products without rewriting collectors.

### **Supported discovery sources**

[Telegram | Quick Apps Store](https://images.openai.com/static-rsc-4/3MqL9rToXt7n8R6IPShZgp27VeBBnkMz1M9PqmtszeIY35KfAwleEdn4ck7y9YsXFhnnI8nQ4prvx9rrrLa6ZyyOdk3jiBKxW1Qa162am6MNIyT8G7IEJP3qIroATpM8zLBXTQP0oo6EOAZv95AUYSN6LRMHKdcgAgtk6L1vDaU?purpose=inline)

**Telegram**

Public channels and accessible groups

Primary collector

[Why Stack Overflow and Reddit Still Beats AI For Your Tech Problems | by Jotham Arinze | Medium](https://images.openai.com/static-rsc-4/bVmFAn_pHcE4EibR4CWwvHLwv4UkoZk_R4uECBrxbSDMeJYO7H7DiaTTqLZ0LQpHx5OmrmBpbXcO0L17PVW8DlJtW4gdP2Xy6MsSZsngIdy4oOjhrttNuXIQIrnbE_ydePs54UOcyxBTohfZZ-c6DwBtzUM_HCEul7bTOYQC6K8?purpose=inline)

**Reddit**

Posts, comments and relevant communities

Primary collector

[browser](https://images.openai.com/static-rsc-4/plKID0-FMYZiYPKuMThj4cubu24HOQzYiC7b_h6vnHrF3iATWhkiX--HU_CqDtkhRavuCdlL_A3iuKdWh6nRF64EbsZz56X6wDO8Fel5tfjIhGQ3JiwepjuX7sio7AogPQatGKiWr_US-emV7ddxiYufF3u8FVpORLHyJ97EC50WlM8KCK7oiqs6SAUSAWld?purpose=inline)

**Public web**

Official announcements, deal websites, RSS feeds and indexed pages

Primary collector

All three collectors should be independent. If Reddit becomes unavailable, Telegram and web discovery should continue working.

### **Explicit exclusions**

For the initial product:

- No automatic redemption.
- No account creation.
- No subscription purchasing.
- No shared accounts or stolen credentials.
- No CAPTCHA or geographical restriction bypassing.
- No paid APIs or mandatory paid AI models.
- No public multi-user platform.

These exclusions keep the MVP manageable and inexpensive.

## **2. Proposed system architecture**

I'd use a modular monolith with asynchronous collectors.

No microservices. No Kubernetes. No unnecessary infrastructure.

## **PromoScout system architecture**

**Discovery sources**

**Telegram**

**Reddit**

**Web**

**Ingestion layer**

Independent source adapters, scheduled polling, source metadata and raw content capture.

**Processing pipeline**

Normalization

Keyword filtering

AI classification

Information extraction

Deduplication

Link inspection

**Promotion intelligence**

Provider matching, eligibility assessment, authenticity assessment, expiry tracking and confidence scoring.

**PostgreSQL**

Sources, discovered content, promotions, redemption links, verification history and notifications.

**Delivery**

Next.js dashboard

Telegram bot notifications

### **Technology stack**

| Layer              | Technology                        |
| ------------------ | --------------------------------- |
| Frontend           | Next.js, TypeScript, Tailwind CSS |
| Backend            | Python 3.12+, FastAPI             |
| Database           | PostgreSQL                        |
| ORM                | SQLAlchemy 2.x                    |
| Migrations         | Alembic                           |
| Telegram ingestion | Telethon                          |
| Reddit ingestion   | Reddit API, where access permits  |
| Web ingestion      | httpx, BeautifulSoup, feedparser  |
| Browser inspection | Playwright, selectively           |
| Scheduling         | APScheduler initially             |
| Notifications      | Telegram Bot API                  |
| AI extraction      | Pluggable provider, optional      |
| Testing            | pytest, Ruff, frontend tests      |

I'd avoid Redis and Celery in the first version. A persistent scheduler, PostgreSQL-backed processing records and independent async collectors are sufficient at this scale.

For deployment, a small Linux machine or your own computer can run the backend and collectors. The dashboard can be deployed separately. Avoid Docker initially if it adds operational overhead.

## **3. Backend architecture and modules**

I'd organize the backend by business responsibility rather than creating a folder for every technical operation.

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── dashboard.py
│   │   │   ├── promotions.py
│   │   │   ├── sources.py
│   │   │   ├── providers.py
│   │   │   ├── notifications.py
│   │   │   └── settings.py
│   │   └── dependencies.py
│   │
│   ├── database/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── session.py
│   │
│   ├── discovery/
│   │   ├── base.py
│   │   ├── telegram.py
│   │   ├── reddit.py
│   │   ├── web.py
│   │   └── scheduler.py
│   │
│   ├── processing/
│   │   ├── normalizer.py
│   │   ├── filters.py
│   │   ├── classifier.py
│   │   ├── extractor.py
│   │   └── deduplicator.py
│   │
│   ├── intelligence/
│   │   ├── providers.py
│   │   ├── eligibility.py
│   │   ├── authenticity.py
│   │   ├── link_validator.py
│   │   ├── scoring.py
│   │   └── expiry.py
│   │
│   ├── notifications/
│   │   └── telegram.py
│   │
│   └── services/
│
├── migrations/
├── tests/
├── scripts/
├── pyproject.toml
└── .env.example
```

The important architectural principle is that collectors should not know how promotions are evaluated.

A Telegram collector should only know how to retrieve messages and submit them to the ingestion pipeline.

The processing system takes over from there.

### **4. Database design**

I'd start with these entities.

| Table                 | Responsibility                                    |
| --------------------- | ------------------------------------------------- |
| `providers`           | Claude, OpenAI, xAI, Google, etc.                 |
| `plans`               | Pro, Plus, Go, Max, etc.                          |
| `sources`             | Telegram channels, subreddits, websites and feeds |
| `discovered_items`    | Raw posts, messages and pages                     |
| `promotions`          | Extracted promotional opportunities               |
| `promotion_links`     | Original URLs and redemption destinations         |
| `verification_checks` | Historical link and offer checks                  |
| `eligibility_rules`   | Country and account restrictions                  |
| `notifications`       | Alerts sent and their delivery status             |
| `app_settings`        | Collection intervals and personal preferences     |

**Important relationship:** one promotion can be discovered in multiple places.

For example, the same Claude Pro offer could appear in three Telegram channels and two Reddit posts.

We should create one canonical promotion and associate all five discoveries with it.

This gives us source corroboration (independent confirmation) rather than five duplicate offers.

### **Promotion data model**

Every extracted promotion should have something resembling:

```
{
  "provider": "anthropic",
  "plan": "claude_pro",
  "title": "Claude Pro promotional access",
  "description": "Promotional subscription offer",
  "offer_type": "free_trial",
  "discount_percentage": null,
  "duration_days": null,
  "redemption_url": "https://example.com/redeem",
  "promo_code": null,
  "eligible_countries": [],
  "excluded_countries": [],
  "account_requirements": [],
  "payment_required": null,
  "expiry_date": null,
  "status": "unverified",
  "confidence_score": 0,
  "first_discovered_at": null,
  "last_checked_at": null
}
```

This is illustrative data, not a real promotion.

All extracted fields should support unknown values. The system must never invent promotional duration, eligibility or payment conditions to fill empty fields.

## **5. The promotion intelligence engine**

This is the most important part of PromoScout.

I want five distinct evaluation stages.

### **A. Provider and plan identification**

The system must recognize variations such as:

- Claude Pro free
- Anthropic Pro promo
- Claude subscription giveaway
- ChatGPT Plus trial
- GPT Plus activation
- Grok premium code

Use provider aliases, plan aliases, keyword matching and contextual classification.

### **B. Offer extraction**

Extract:

- Provider.
- Subscription plan.
- Offer type.
- Discount or free-access duration.
- Redemption link.
- Promotional code.
- Expiration date.
- Geographic restrictions.
- Account requirements.
- Payment requirements.
- Original source.

Offer types should include:

`free_trial`, `free_subscription`, `discount`, `student_offer`, `referral`, `partner_offer`, `giveaway`, `unknown`.

### **C. Authenticity assessment**

Don't trust a promotion simply because many people shared it.

Assess:

1. Is the original source official?
2. Does the link lead to the legitimate provider or authorized partner?
3. Is there an independently verifiable announcement?
4. Are the terms consistent?
5. Is there evidence of phishing, impersonation or account theft?

A Telegram post claiming to have free Claude Pro accounts is not equivalent to an official Claude promotional offer.

### **D. Nigerian eligibility assessment**

This deserves its own module.

Possible results:

| Status     | Meaning                         |
| ---------- | ------------------------------- |
| Eligible   | Nigeria is explicitly supported |
| Ineligible | Nigeria is explicitly excluded  |
| Unknown    | No reliable country information |
| Restricted | Additional conditions apply     |

Also check:

- Existing versus new subscribers.
- Student verification.
- Payment-card requirements.
- Referral eligibility.
- Account age.
- One-redemption-per-account restrictions.
- Whether the offer is genuinely free or requires a paid subscription after a trial.

Do not assume an offer is available in Nigeria merely because the website opens.

### **E. Promotion scoring**

I'd use a transparent deterministic score rather than allowing an LLM to decide whether an offer is trustworthy.

**Proposed confidence score**

# **100 points**

Maximum possible score, subject to evidence

Source credibility

**30**

Redemption destination

**25**

Terms and conditions

**20**

Independent corroboration

**15**

Freshness

**10**

The score measures evidence quality, not guaranteed redemption success.

A high score must not override an explicit country exclusion or expired offer.

The dashboard should display both the confidence score and the reasons behind it.

## **6. Discovery strategy and collection frequency**

We don't need to scrape the entire internet.

We need a manageable set of high-value sources and targeted queries.

I'd introduce a configurable source registry.

| Source type | Configuration                             |
| ----------- | ----------------------------------------- |
| Telegram    | Channel username or accessible channel ID |
| Reddit      | Subreddit, search query                   |
| Web         | Website, RSS feed, search endpoint        |

Initial collection schedule:

| Task                   | Suggested interval |
| ---------------------- | ------------------ |
| Telegram polling       | 2 minutes          |
| Reddit polling         | 5 minutes          |
| RSS feeds              | 15 minutes         |
| Public web pages       | 30 minutes         |
| Promotion revalidation | 6 hours            |
| Expiry evaluation      | 1 hour             |

These are starting configurations, not guarantees of source availability. Respect API quotas, platform terms and individual source restrictions. Use incremental cursors and backoff when rate-limited.

For web discovery, prioritize RSS feeds, official announcement pages and publicly accessible search interfaces. Don't make a paid search API a dependency.

### **Search vocabulary**

We should maintain a search-term catalogue for every provider.

For example:

```
SEARCH_TERMS = {    "anthropic": [        "Claude Pro free",        "Claude Pro promotion",        "Claude subscription offer",        "Anthropic promo code",    ],    "openai": [        "ChatGPT Plus free",        "ChatGPT Go promotion",        "ChatGPT Pro discount",        "OpenAI subscription offer",    ],    "xai": [        "Grok Pro free",        "SuperGrok promotion",        "Grok subscription discount",    ],}
```

Expand this catalogue for the other providers.

The terms should be editable through the application, rather than requiring code changes.

## **7. Free-operation strategy**

We should distinguish between free software and free infrastructure.

The software can be entirely open-source, but running collectors continuously still requires computing resources.

Here's the approach I'd take:

| Component           | Initial approach                | Cost         |
| ------------------- | ------------------------------- | ------------ |
| Next.js dashboard   | Vercel free tier or local       | ₦0           |
| FastAPI backend     | Local Linux machine             | ₦0           |
| PostgreSQL          | Local installation              | ₦0           |
| Telegram collection | Telethon                        | ₦0           |
| Reddit collection   | Official API, subject to access | ₦0 initially |
| Web collection      | httpx, RSS, BeautifulSoup       | ₦0           |
| Scheduling          | APScheduler                     | ₦0           |
| Notifications       | Telegram Bot API                | ₦0           |
| AI extraction       | Deterministic rules first       | ₦0           |

### **Avoid unnecessary AI expenses**

I'd build the extraction engine in layers:

1. Keyword matching eliminates irrelevant content.
2. Regex extracts URLs, codes and recognizable dates.
3. Deterministic parsers identify known providers and plans.
4. An optional LLM handles ambiguous messages.
5. Human review resolves uncertain offers.

This makes the system useful even when no AI model is configured.

### **One operational consideration**

Telethon's user-account session is sensitive. Store its session file securely, never commit it, and avoid running the same session concurrently in multiple processes.

Reddit API access and permitted use also need to be checked before implementation. If access is unavailable, the Reddit adapter should report that limitation instead of silently falling back to unauthorized scraping.

## **8. Frontend application design**

I don't want this to become a dashboard full of meaningless statistics.

The application should revolve around finding and acting on good promotions.

# **PromoScout**

Personal promotion intelligence

Monitoring

Discovered

# **148**

Verified

# **12**

New today

# **8**

**Your discoveries**

FILTER BY PROVIDER

All providers⌄

**Claude Pro promotional offer**

Unverified

Anthropic · Reddit · r/ClaudeAI

View promotion →

**ChatGPT Plus student offer**

Restricted

OpenAI · Telegram · Channel

View promotion →

**Cursor Pro discount**

Verified

Cursor · Official website

View promotion →

Illustrative interface with fictional discovery records.

### **Main navigation**

I'd use six sections:

1. **Overview:** discovery activity, recent offers and system health.
2. **Promotions:** searchable, filterable promotion database.
3. **Sources:** manage Telegram channels, subreddits and websites.
4. **Providers:** manage supported AI companies and plans.
5. **Watchlist:** promotions and providers you want to prioritize.
6. **Settings:** collection intervals, notifications and eligibility preferences.

### **Promotion details page**

Every promotion should have:

- Provider and plan.
- Offer description.
- Original source and post.
- Original redemption URL.
- Promotional code, where available.
- Nigerian eligibility.
- Payment requirements.
- Expiration information.
- Authenticity assessment.
- Verification history.
- Confidence score.
- Related discoveries.

The primary action should be **Open redemption page**.

It should open the original destination, not an intermediary that obscures where you're going.

### **Telegram notifications**

Notifications should be selective.

Example:

**PromoScout Alert**

Example

High confidence

**New Claude Pro promotion discovered**

- Provider: Anthropic
- Plan: Claude Pro
- Offer: Promotional access
- Nigerian eligibility: Unknown
- Source: r/ClaudeAI
- Verification: Original source found, redemption not confirmed.

**Recommendation:** Review the offer and its conditions before redeeming.

A real notification would include the original post and redemption links.

You should be able to configure alerts for only certain providers, minimum confidence scores and offer types.

## **9. Security and reliability requirements**

This is particularly important because the application will discover arbitrary URLs from strangers on the internet.

We need to prevent:

- Phishing links being presented as legitimate offers.
- Open redirects hiding suspicious destinations.
- Server-side request forgery (SSRF), where malicious URLs make the backend access internal services.
- Malicious downloads and browser execution.
- Telegram session leakage.
- Duplicate notifications.
- Incorrect expiry calculations.
- A compromised source injecting instructions into an AI extraction prompt.

The LLM must treat discovered messages as untrusted data, never as instructions.

For URL validation, use domain allowlists where possible, redirect limits, private-network IP blocking, timeouts and safe browser isolation. Never automatically submit personal information, payment details or login credentials.

Also, store verification history. A promotion's status can change over time.

## **10. Implementation roadmap**

I'd implement this in eight phases. Each phase should leave us with a working, testable system.

1. **Phase 1: Foundation and data model**
   - Initialize FastAPI and Next.js.
   - Configure PostgreSQL, SQLAlchemy and Alembic.
   - Create providers, plans, sources and discovered-items models.
   - Implement application configuration and logging.
   - Add tests and development setup.

   Deliverable: Working application foundation
2. **Phase 2: Discovery infrastructure**
   - Build a common source-adapter interface.
   - Implement Telegram collector using Telethon.
   - Implement Reddit collector.
   - Implement RSS and public web collectors.
   - Add source management and collection scheduling.
   - Persist raw discoveries.

   Deliverable: Multi-source discovery engine
3. **Phase 3: Extraction and classification**
   - Build normalization.
   - Implement keyword filtering.
   - Recognize providers and plans.
   - Extract links, promotional codes and conditions.
   - Add optional AI classification.
   - Implement duplicate detection.

   Deliverable: Structured promotion discovery
4. **Phase 4: Promotion intelligence**
   - Implement safe URL inspection.
   - Build authenticity assessment.
   - Build Nigerian eligibility assessment.
   - Implement confidence scoring.
   - Track expiration and verification history.
   - Support multiple sources corroborating one offer.

   Deliverable: Promotion assessment engine
5. **Phase 5: Backend API**
   - Promotion endpoints.
   - Provider and plan endpoints.
   - Source management endpoints.
   - Dashboard statistics.
   - Watchlist endpoints.
   - Settings and notification endpoints.

   Deliverable: Complete backend API
6. **Phase 6: Frontend dashboard**
   - Overview dashboard.
   - Promotion listing and filters.
   - Promotion details.
   - Source management.
   - Provider management.
   - Watchlist.
   - Settings and system health.

   Deliverable: Usable PromoScout application
7. **Phase 7: Notifications and automation**
   - Telegram bot setup.
   - Configurable notification rules.
   - New promotion alerts.
   - Expiring promotion alerts.
   - Failed collector alerts.
   - Scheduled revalidation.

   Deliverable: Automated discovery and notification
8. **Phase 8: Integration and deployment**
   - End-to-end tests.
   - Test duplicate handling.
   - Test collector failure and recovery.
   - Test malicious links.
   - Optimize resource consumption.
   - Configure persistent deployment.
   - Verify continuous monitoring.

   Deliverable: Production-ready personal tool

## **11. MVP acceptance criteria**

I wouldn't consider PromoScout complete just because it has a nice dashboard.

It must satisfy these conditions:

| Requirement             | Expected result                                  |
| ----------------------- | ------------------------------------------------ |
| Telegram discovery      | Retrieves new messages from configured sources   |
| Reddit discovery        | Retrieves accessible relevant posts and comments |
| Web discovery           | Collects relevant public announcements and feeds |
| Provider identification | Correctly identifies all seven providers         |
| Extraction              | Produces structured promotion records            |
| Deduplication           | Combines repeated discoveries                    |
| Validation              | Identifies suspicious and inaccessible links     |
| Eligibility             | Distinguishes Nigerian eligibility from unknown  |
| Expiry                  | Detects expired promotions                       |
| Notifications           | Sends useful, non-duplicated alerts              |
| Persistence             | Retains discoveries after restarting             |
| Cost                    | No mandatory paid API or model dependency        |

One particularly important test:

If the same promotion appears in 20 different Telegram channels and Reddit posts, PromoScout should recognize it as one opportunity with 20 discovery references.

## **12. Repository structure**

I'd keep the frontend and backend in one repository:

```
promoscout/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── lib/
│   └── types/
│
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   └── pyproject.toml
│
├── docs/
│   ├── architecture.md
│   ├── database.md
│   ├── discovery.md
│   └── deployment.md
│
├── scripts/
├── .env.example
├── .gitignore
└── README.md
```

No microservices or separate repositories. One codebase, independently runnable frontend and backend.

## **13. Important architectural decisions to lock**

Here is the proposed decision register:

| Decision       | Recommendation                     |
| -------------- | ---------------------------------- |
| Architecture   | Modular monolith                   |
| Frontend       | Next.js + TypeScript               |
| Backend        | FastAPI                            |
| Database       | PostgreSQL                         |
| ORM            | SQLAlchemy 2.x                     |
| Migrations     | Alembic                            |
| Telegram       | Telethon                           |
| Reddit         | Official API where available       |
| Web            | RSS + HTTP extraction              |
| Scheduling     | APScheduler                        |
| AI             | Optional, provider-independent     |
| Notifications  | Telegram Bot API                   |
| Redemption     | Manual                             |
| Deployment     | Single backend process initially   |
| Infrastructure | Free-first, self-hosted collectors |

Architecture recommendation

**My strongest recommendation is to make PromoScout deterministic-first and AI-assisted, not AI-dependent.**

The difference matters. If an AI API becomes unavailable or introduces charges, your discovery system should continue operating.

## **14. Let's establish the implementation baseline**

Before generating the Phase 1 implementation prompts, there are two practical decisions worth settling.

**1. Where should PromoScout run initially?**

My Linux computer (Zorin OS), running locally.

A small Linux VPS, if available.

Develop locally, then deploy to a Linux server.

**2. Reddit collection strategy**

Official Reddit API only, subject to access and quotas.

Official API first, with permitted public RSS/web sources as fallback.

**3. AI extraction strategy**

Optional AI. The application must work without it.

Rules and deterministic extraction only for MVP.

Lock implementation baseline

Once these are settled, we'll move into implementation phase by phase, with detailed agent prompts, tests and explicit completion criteria.

One final thought: PromoScout's real value isn't finding a free 
subscription once. It's becoming your personal radar for opportunities 
that would otherwise disappear in thousands of Telegram messages and 
Reddit posts.



