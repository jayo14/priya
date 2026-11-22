# Priya — Phase 2: Discovery Infrastructure

This document details the architecture, design, and operation of the Multi-Source Discovery Engine implemented in Phase 2 of Priya.

## 1. Objective and Design Philosophy

The discovery layer is responsible for gathering raw promotional content from external networks (Telegram, Reddit, RSS feeds, and public web announcement pages).

**Core Design Principles:**
- **Decoupled Responsibilities**: Collectors only retrieve and structure raw data into `RawDiscoveredItem` contracts; they do not parse or assess promotion eligibility.
- **Zero Paid Dependencies**: All collectors operate over public endpoints (e.g. Telegram public web previews, Reddit public JSON/RSS, web feeds) without requiring paid API keys, phone numbers, or third-party proxies.
- **Deduplication at Ingestion**: Ingestion checks both source-specific external IDs and SHA-256 normalized content hashes, ensuring duplicate posts are never stored twice.
- **Fault-Tolerant & Isolated**: Network failures or rate limits on one source (e.g. Reddit 429) do not affect other sources. Source state (`last_collected_at`, `last_successful_collection_at`, `last_error_at`, `last_error_message`) is persisted in PostgreSQL for full operational visibility.

---

## 2. Collector Implementations

### Telegram Collector (`app.discovery.telegram.TelegramCollector`)
- **Target**: Public Telegram channels (e.g. `@ChatGPT_Promocodes`, `@ai_promos_daily`).
- **Mechanism**: Queries Telegram's public web preview endpoint `https://t.me/s/{channel_name}`.
- **Extraction**: Parses message text, outbound links, views, and publication timestamps from HTML without requiring Telegram bot tokens or API login.
- **Identifer Normalization**: Automatically strips `@`, URLs, and trailing paths.

### Reddit Collector (`app.discovery.reddit.RedditCollector`)
- **Target**: Subreddits (e.g. `r/ClaudeAI`, `r/ChatGPT`, `r/PerplexityAI`) or targeted queries (`search:title:pro OR title:discount`).
- **Mechanism**: Queries Reddit's public JSON API (`/r/{subreddit}/new.json`) with an identified User-Agent.
- **Resilience**: If Reddit returns HTTP 429 (rate-limited) or blocks JSON requests, the collector automatically falls back to Reddit's public RSS feed (`/r/{subreddit}/new.rss`).
- **Extraction**: Post title, selftext, outbound URLs, karma score, flair, author, and creation timestamp.

### RSS & Atom Collector (`app.discovery.web.RssCollector`)
- **Target**: Official company newsrooms and blogs (e.g., OpenAI blog, Google AI blog, GitHub changelog).
- **Mechanism**: Fetches feeds with `httpx` and parses standard RSS 2.0 and Atom XML via `feedparser`.
- **Extraction**: Entry IDs, sanitized HTML text, author tags, and publication timestamps.

### Web Page Collector (`app.discovery.web.WebPageCollector`)
- **Target**: Official landing pages and deal sites.
- **Mechanism**: Retrieves page HTML using `httpx` with redirect following.
- **Extraction**: Strips non-content tags (`<script>`, `<style>`, `<nav>`, `<footer>`) with BeautifulSoup, extracts article text, and gathers all outbound promotional links into metadata.

---

## 3. Orchestration & Persistence

The `DiscoveryOrchestrator` (`app.discovery.orchestrator.DiscoveryOrchestrator`) coordinates execution:
1. Receives a single `Source` or queries all active sources from `SourceRepository`.
2. Resolves the appropriate collector by `source.source_type`.
3. Executes collection asynchronously with timeouts.
4. For each `RawDiscoveredItem`:
   - Checks `DiscoveryRepository.get_by_external_id(source_id, external_id)`.
   - Checks `DiscoveryRepository.get_by_content_hash(hash)`.
   - If novel, persists to `discovered_items` with status `PENDING`.
5. Updates source collection timestamps and error logs in PostgreSQL.

---

## 4. Background Scheduling

The `DiscoveryScheduler` (`app.discovery.scheduler.DiscoveryScheduler`):
- Runs as an asynchronous background worker loop.
- Periodically checks which active sources are due (`now - last_collected_at >= collection_interval_seconds`).
- Triggers collection without external message brokers (no Redis or Celery).

---

## 5. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/sources` | List all registered sources with status and timestamps. |
| `POST` | `/api/v1/sources` | Register a new discovery source. |
| `GET` | `/api/v1/sources/{id}` | Retrieve source details. |
| `POST` | `/api/v1/sources/{id}/collect` | Trigger immediate on-demand collection for a source. |
| `POST` | `/api/v1/discovery/collect-all` | Trigger discovery across all active sources. |
| `GET` | `/api/v1/discovery/items` | Query raw discovered items with status filtering. |
