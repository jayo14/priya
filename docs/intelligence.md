# Priya Promotion Intelligence & Verification Engine (Phase 4)

The Promotion Intelligence layer is Priya's core verification and evaluation system. It takes raw extracted promotions and executes deterministic safety, authenticity, Nigerian banking feasibility, and dynamic confidence scoring before presenting deals to users.

---

## 1. Safe Link Inspection & SSRF Prevention (`link_validator.py`)

Discovering URLs from third-party social media and public forums introduces security risks (SSRF, phishing, open redirects, and malware). Priya validates all links through deterministic safety guardrails:

### SSRF Protection
- **Protocol Restriction**: Only `http` and `https` schemes are accepted. Protocols such as `file://`, `ftp://`, `gopher://`, and `data:` are rejected immediately.
- **Private & Reserved IP Defense**: Target hostnames and IP literals are validated against private, loopback, link-local, multicast, and reserved CIDR ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fe80::/10`).
- **Redirect Chain Inspection**: Redirects (HTTP 301, 302, 303, 307, 308) are followed up to 5 hops with per-hop SSRF validation.

### Domain Categorization
- **Official AI Provider Domains**: Mapped for each supported provider (e.g. Anthropic: `claude.ai`, `anthropic.com`; OpenAI: `chatgpt.com`, `openai.com`; xAI: `x.ai`, `grok.com`; Google: `deepmind.google`, `gemini.google.com`; Perplexity: `perplexity.ai`; Cursor: `cursor.com`; GitHub: `github.com`).
- **Authorized Partner Portals**: Recognized academic and merchant portals (e.g. `services.sheerid.com`, `unidays.com`, `studentbeans.com`, `microsoft.com`, `stripe.com`).
- **Shortener & Impersonation Detection**: Known link shorteners (`bit.ly`, `tinyurl.com`, `t.co`) are flagged to follow through to final canonical destinations. Deceptive lookalikes (e.g. domains containing brand tokens on high-risk TLDs such as `.xyz`, `.top`, `.online`) are flagged as potential brand impersonation lures.

---

## 2. Authenticity Assessment (`authenticity.py`)

Evaluates whether an offer is genuine, official, or a scam/account-theft trap:

- **Source Credibility**:
  - Official announcement channels & corporate blogs: High credibility (+25 to +30 pts).
  - Dedicated provider communities (e.g. `r/ClaudeAI`, `r/ChatGPT`): Moderately high (+20 pts).
  - Standard tech deal communities & Telegram channels: Baseline (+10 pts).
- **Scam & Fraud Pattern Filtering**:
  - Rejects illicit offers mentioning "cracked accounts", "BIN method", "carding", "shared accounts", "modded apk", "stolen cookies", or "DM for password/crypto".
  - Detected scams immediately zero out authenticity scores and transition promotion status to `INVALID`.

---

## 3. Nigerian Regional & Financial Usability (`eligibility.py`)

A deal is useless to a Nigerian user if regional geoblocks or banking restrictions prevent redemption. This module provides transparent eligibility breakdown:

| Evaluation Dimension | Behavior & Guidance |
|---|---|
| **Explicit Country Scope** | Evaluates whether `NG` (or `GLOBAL`) is included or excluded. Grok referral programs and US-only student programs are flagged accordingly. |
| **Banking & Card Feasibility** | Nigerian bank-issued domestic Naira debit cards (Verve, Mastercard, Visa) frequently fail on foreign USD gateways due to international spend limits ($0/month). When `payment_required` is `True`, Priya advises using funded Virtual USD Cards (e.g., Geegpay, Chipper Cash, Payday, Eversend) or mobile app store billing. |
| **Student Verification** | If student status is required (e.g. via SheerID or UNiDAYS), flags that Nigerian `.edu.ng` institutions may require manual document review rather than automated verification. |
| **Account Age / Status** | Distinguishes offers restricted to fresh sign-ups vs existing subscribers. |

Structured `EligibilityRule` records are stored in PostgreSQL for each evaluated promotion.

---

## 4. 100-Point Dynamic Confidence Rubric (`scoring.py`)

Promotions are scored deterministically on a 100-point scale measuring evidence quality:

```text
┌────────────────────────────────────────────────────────┐
│               100-Point Evidence Rubric                │
├─────────────────────────────────┬──────────────────────┤
│ 1. Source Credibility           │ 0 to 30 points       │
│ 2. Redemption Destination       │ 0 to 25 points       │
│ 3. Terms & Conditions Clarity   │ 0 to 20 points       │
│ 4. Independent Corroboration    │ 0 to 15 points       │
│ 5. Freshness                    │ 0 to 10 points       │
└─────────────────────────────────┴──────────────────────┘
```

### Lifecycle Status Mapping:
- **`INVALID`**: Scam indicators detected, or URL violates safety/SSRF rules.
- **`EXPIRED`**: Offer has passed its expiration date or text indicates codes are exhausted.
- **`RESTRICTED`**: Offer terms explicitly exclude Nigeria or impose blocking constraints.
- **`VERIFIED`**: Score $\ge 75$ with destination confirmed on official provider or authorized partner domain.
- **`LIKELY_VALID`**: Score $\ge 50$ with credible terms.
- **`UNVERIFIED`**: Score $< 50$ (insufficient evidence).

---

## 5. Expiration Tracking (`expiry.py`)

- Computes active vs urgent vs expired status.
- Urgent threshold: Offers expiring within 48 hours are tagged `urgent`.
- Inferred expiry: Identifies textual patterns (e.g. "valid for 24 hours", "ends Dec 31").

---

## 6. Verification Audit Trail

Every run of the Intelligence Engine persists timestamped audit logs in the `verification_checks` table:
- `url_safety`: Details redirect hops, final destination domain, accessibility.
- `authenticity`: Details trust signals and risk flags.
- `nigeria_eligibility`: Details geographic status and card usability notes.
- `expiry`: Details urgency and remaining days.
- `confidence_scoring`: Details points per rubric category and reason codes.

---

## 7. API Endpoints

- `POST /api/v1/promotions/{id}/verify`: Triggers an on-demand re-verification run and returns updated score and audit entries.
- `GET /api/v1/promotions/{id}/eligibility`: Returns regional and Nigerian banking guidance and active rules.
- `GET /api/v1/promotions/{id}/verification-checks`: Returns historical audit checks.
- `GET /api/v1/promotions?min_confidence=75`: Filter promotions by minimum confidence score.
