# Priya Frontend Architecture — Nuxt 3, shadcn-vue & Material Symbols

The Priya web client is built with **Nuxt 3** and **Vue 3**, styled with **Tailwind CSS** using **shadcn-vue** design tokens and primitives (`radix-vue`), and powered by Google's **Material Symbols (New) Rounded** icons.

---

## 1. Design System & Tech Stack

- **Framework**: Nuxt 3 (SSR/SSG & Nitro engine) + Vue 3 (Composition API `<script setup>`).
- **Styling**: Tailwind CSS with shadcn dark zinc/emerald design system tokens (`var(--background)`, `var(--card)`, `var(--primary)`, `var(--border)`).
- **Headless UI Primitives**: `radix-vue`, `class-variance-authority` (`cva`), `clsx`, `tailwind-merge`.
- **Icons**: Google **Material Symbols (New) Rounded** loaded via Google Fonts and rendered via `<MaterialIcon name="..." />`.

---

## 2. Directory Structure

```text
frontend/
├── assets/
│   └── css/
│       └── main.css           # Tailwind directives, CSS variables, Material Symbols styling
├── components/
│   ├── ui/                    # shadcn-vue UI primitives
│   │   ├── Button.vue         # CVA variants (default, secondary, outline, ghost, destructive)
│   │   ├── Badge.vue          # Status pills (verified, likely, restricted, unverified)
│   │   ├── Card.vue           # Rounded container with hover transitions
│   │   ├── Input.vue          # Form input with focus rings
│   │   └── Dialog.vue         # Teleported modal dialog with backdrop blur
│   ├── MaterialIcon.vue       # Material Symbols Rounded icon wrapper
│   ├── Navbar.vue             # Header with live health ping and navigation
│   ├── DealCard.vue           # Promotion card with confidence meter and 1-click code copy
│   └── DealDetailModal.vue    # Full audit log, Nigeria banking guidance, and re-verify action
├── composables/
│   └── usePriyaApi.ts         # Auto-imported API composable
├── layouts/
│   └── default.vue            # Layout shell with Navbar and responsive footer
├── lib/
│   ├── api.ts                 # Typed REST client connecting to FastAPI backend
│   └── utils.ts               # cn() helper
├── pages/
│   ├── index.vue              # Real-time Overview Dashboard with top KPI cards
│   ├── deals.vue              # Deals directory with search, provider filter, Nigeria filter
│   ├── watchlist.vue          # Saved bookmarked promotions and watched AI providers
│   ├── sources.vue            # Ingestion manager with on-demand scraping & pipeline trigger
│   └── settings.vue           # Alert thresholds, Nigeria-only mode, polling intervals
├── nuxt.config.ts             # Nuxt configuration and Google Fonts links
├── tailwind.config.ts         # Theme extension and shadcn color mapping
└── package.json
```

---

## 3. Pages & User Experience

### 1. Overview Dashboard (`/`)
- **4 Top KPI Cards**: Discovered items count, verified promotions, expiring promotions, and Nigerian-usable deals.
- **Provider Catalogue**: Quick access pills for all 7 AI providers (Claude, ChatGPT, Grok, Gemini, Perplexity, Cursor, Copilot).
- **Recent Opportunities**: High-confidence recent deals with 1-click claim links.

### 2. Deals Directory (`/deals`)
- **Live Search**: Filters by promotion title, provider name, or promo code.
- **Provider Filtering**: Instant filtering by AI lab.
- **Offer Types**: Filter by Free Trial, Discount, Student Offer, or Referral.
- **Nigeria Usable Only**: One-click toggle filtering out geo-restricted deals.
- **Confidence Filter**: Slider to filter out deals below a chosen confidence score.

### 3. Deal Detail Modal
- **Authenticity Audit**: Breakdown of source credibility and official destination match.
- **Nigerian Banking Guidance**: Explicit feasibility checks on local Naira cards vs funded Virtual USD Cards (Geegpay, Chipper, Payday).
- **Verification Audit Trail**: Full list of automated verification checks (`url_safety`, `authenticity`, `nigeria_eligibility`, `expiry`).
- **One-Click Re-verification**: Triggers on-demand live HTTP verification.

### 4. Watchlist (`/watchlist`)
- Saved promotions bookmarked by the user.
- Watched AI providers for priority alerting.

### 5. Sources & Ingestion (`/sources`)
- Monitored Telegram channels, Reddit communities, and RSS feeds.
- "Scout All Sources" and "Run Extraction Pipeline" manual triggers.

### 6. Settings (`/settings`)
- Alert confidence threshold slider (0–100%).
- Nigeria-only default filter toggle.
- Polling frequency interval selection.
