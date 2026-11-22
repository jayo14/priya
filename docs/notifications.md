# Priya Notifications & Telegram Bot Integration (Phase 7)

Priya includes an automated, deterministic real-time alerting engine that delivers instant push notifications to subscribers via the Telegram Bot API when new or expiring high-confidence AI subscription deals are discovered.

---

## 1. Alert Types (`NotificationType`)

| Alert Type | Trigger | Purpose |
|---|---|---|
| `NEW_PROMOTION` | New promotion created with confidence $\ge$ user threshold (default 60%). | Instant discovery announcement with redemption link. |
| `PROMOTION_EXPIRING` | Promotion scheduled to expire in $\le 48$ hours. | Urgent notification reminding users to claim before expiry. |
| `VERIFICATION_STATUS_CHANGED` | Promotion score updated or verified by live HTTP checks. | Re-scoring announcement when status upgrades to `VERIFIED`. |

---

## 2. Notification Dispatcher & Duplicate Prevention (`dispatcher.py`)

A deal finder must never spam users with duplicate alerts. Priya guarantees single-delivery semantics:

### Threshold Filtering
Before sending an alert, the `NotificationDispatcher` evaluates user preferences:
- **Confidence Threshold**: Deals scoring below the configured threshold (e.g. 60% or 75%) are automatically muted.
- **Nigeria-Only Preference**: When active, deals that explicitly exclude Nigeria or require unsupported payment methods are withheld.
- **Channel Enablement**: Alerts can be toggled on/off globally.

### Duplicate Prevention
Every dispatched alert is recorded in the PostgreSQL `notifications` table. Before sending any alert, Priya queries:
```sql
SELECT 1 FROM notifications 
WHERE promotion_id = :id 
  AND notification_type = :type 
  AND status = 'sent';
```
If an alert of the same type has already been delivered, subsequent dispatch calls are skipped idempotently.

---

## 3. Message Formatting (`formatter.py`)

Alerts are rendered in clean HTML with structured formatting:

```html
🚀 <b>Priya Alert: New AI Deal Discovered!</b>

🤖 <b>Provider:</b> Anthropic
📦 <b>Plan:</b> Claude Pro
🎯 <b>Deal:</b> Claude Pro 1-Month Free Access for Students
⏱ <b>Access:</b> 30 Days Free
🏷 <b>Promo Code:</b> <code>CLAUDE_CAMPUS_2026</code>
⭐ <b>Score:</b> 85/100 (VERIFIED)

🇳🇬 <b>Nigerian Usability:</b> ✅ Eligible in Nigeria
💳 <b>Payment Note:</b> Local Naira debit cards often fail CBN foreign limits. A funded Virtual USD Card (Geegpay, Chipper, Payday) is recommended.

🔗 <a href="https://claude.ai/promo/campus"><b>Open Redemption Page</b></a>

<i>You discover the opportunity. Priya brings it to you. You decide whether to claim it.</i>
```

---

## 4. Telegram Bot API Client (`telegram.py`)

- **Direct HTTP API**: Communicates directly with `https://api.telegram.org/bot<token>/sendMessage` via `httpx`.
- **Zero Paid Dependencies**: Does not require third-party paid services or heavy bot frameworks.
- **HTML Fallback**: If custom HTML entities are rejected by Telegram (HTTP 400), automatically re-attempts delivery with plain text to guarantee alert arrival.
- **Simulated Development Mode**: When `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is omitted in development, messages are logged at `INFO` level without raising fatal runtime errors.

---

## 5. API Endpoints (`backend/app/api/routes/notifications.py`)

- `GET /api/v1/notifications`: List all historical notifications with delivery timestamp and status (`pending`, `sent`, `failed`).
- `POST /api/v1/notifications/test`: Send a test notification to verify bot credentials.
- `POST /api/v1/notifications/dispatch-expiring`: Scan active deals and dispatch alerts for offers expiring within 48 hours.
- `POST /api/v1/notifications/promotions/{id}/dispatch`: Force-dispatch an alert for a specific promotion.
