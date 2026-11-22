# Priya — Production Deployment & Operations Guide

This guide covers deploying and operating **Priya** on a Linux server without requiring Docker, Kubernetes, Redis, Celery, or external paid services.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Reverse Proxy (Nginx)     |
                      |   Port 80/443 (HTTPS)       |
                      +--------------+--------------+
                                     |
                    +----------------+----------------+
                    |                                 |
           /api/* & /docs                    /* (Static & SSR)
                    |                                 |
                    v                                 v
        +-----------------------+         +-----------------------+
        |   FastAPI Backend     |         |    Nuxt 3 Frontend    |
        |   Uvicorn (Port 8000) |         |    Nitro (Port 3000)  |
        +-----------+-----------+         +-----------------------+
                    |
                    | (SQLAlchemy 2.x / Psycopg 3)
                    v
        +-----------------------+
        |  PostgreSQL 16 Engine |
        |  Port 5432 (Local)    |
        +-----------------------+
                    ^
                    | (CLI Runner / systemd Timer)
        +-----------------------+
        |  Priya Scout Runner   |
        |  `python -m app.cli`  |
        +-----------------------+
```

- **Lightweight Monolith**: Designed for servers with constrained memory (e.g., 1 GB to 2 GB RAM).
- **Deterministic**: 100% rules-based, no external LLM billing, no token costs.
- **Zero Celery/Redis**: Scheduled scraping and alert dispatching run via native Linux `systemd.timer` or cron.
- **Direct Bot API**: Telegram notifications are pushed directly over outbound HTTPS without intermediary message queues.

---

## System Requirements

- **OS**: Ubuntu 22.04 LTS / 24.04 LTS or Debian 12 (Linux x86_64 or ARM64)
- **RAM**: Minimum 1 GB, Recommended 2 GB
- **CPU**: 1+ cores
- **Disk**: 10 GB SSD
- **Software**:
  - Python 3.12+
  - Node.js 20.x or 22.x LTS
  - PostgreSQL 16
  - Nginx (or Caddy)

---

## 1. PostgreSQL Setup

Install and configure PostgreSQL:

```bash
sudo apt update && sudo apt install -y postgresql postgresql-contrib

# Switch to postgres user and create application user and database
sudo -u postgres psql <<EOF
CREATE USER priya_user WITH PASSWORD 'your_strong_production_password';
CREATE DATABASE priya OWNER priya_user;
GRANT ALL PRIVILEGES ON DATABASE priya TO priya_user;
EOF
```

Ensure PostgreSQL runs locally:
```bash
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

---

## 2. Repository & Environment Setup

Clone repository and configure environment:

```bash
git clone https://github.com/your-username/priya.git /var/www/priya
cd /var/www/priya

# Configure environment variables
cp .env.example .env
nano .env
```

Ensure the following variables are configured in `.env`:

```env
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://priya_user:your_strong_production_password@127.0.0.1:5432/priya
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
TELEGRAM_CHAT_ID=-1001234567890
```

---

## 3. Backend Setup

```bash
cd /var/www/priya/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# Run database migrations and seed baseline data
alembic upgrade head
python -c "
from app.database.session import SessionLocal
from app.database.seed import seed_database
with SessionLocal() as db:
    seed_database(db)
"
```

---

## 4. Frontend Setup

Compile the Nuxt 3 application into production artifacts:

```bash
cd /var/www/priya/frontend
npm ci
npm run build
```

This generates `.output/server/index.mjs` which runs lightweight Nitro without requiring a heavyweight dev server.

---

## 5. Systemd Service Configuration

Copy the provided unit files to `/etc/systemd/system/`:

```bash
# Substitute current user and path
export APP_USER=www-data
export APP_DIR=/var/www/priya

sed -e "s|%USER%|$APP_USER|g" -e "s|%WORKDIR%|$APP_DIR|g" \
  $APP_DIR/scripts/systemd/priya-backend.service | sudo tee /etc/systemd/system/priya-backend.service

sed -e "s|%USER%|$APP_USER|g" -e "s|%WORKDIR%|$APP_DIR|g" \
  $APP_DIR/scripts/systemd/priya-frontend.service | sudo tee /etc/systemd/system/priya-frontend.service

sed -e "s|%USER%|$APP_USER|g" -e "s|%WORKDIR%|$APP_DIR|g" \
  $APP_DIR/scripts/systemd/priya-scout.service | sudo tee /etc/systemd/system/priya-scout.service

sudo cp $APP_DIR/scripts/systemd/priya-scout.timer /etc/systemd/system/priya-scout.timer

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable --now priya-backend.service
sudo systemctl enable --now priya-frontend.service
sudo systemctl enable --now priya-scout.timer
```

Verify status:
```bash
sudo systemctl status priya-backend.service
sudo systemctl status priya-frontend.service
sudo systemctl list-timers priya-scout.timer
```

---

## 6. Nginx Reverse Proxy Configuration

Install and configure Nginx:

```nginx
# /etc/nginx/sites-available/priya.conf
server {
    listen 80;
    server_name deals.yourdomain.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name deals.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/deals.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/deals.yourdomain.com/privkey.pem;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API & Docs routes -> FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Nuxt 3 Frontend -> Nitro
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/priya.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. Manual CLI Commands & Maintenance

You can trigger on-demand scraping, pipeline execution, or expiring deal checks at any time:

```bash
# Run full scout across all sources
/var/www/priya/scripts/scout.sh run

# Force scrape all sources regardless of interval
/var/www/priya/scripts/scout.sh run --force

# Check and alert on deals expiring in < 48 hours
/var/www/priya/scripts/scout.sh expiring

# Display engine metrics
/var/www/priya/scripts/scout.sh stats
```

---

## 8. Logs & Monitoring

Use standard `journalctl` to inspect live service logs:

```bash
# Follow backend logs
journalctl -u priya-backend.service -f

# Follow frontend logs
journalctl -u priya-frontend.service -f

# Follow periodic scout runs
journalctl -u priya-scout.service -f
```

Automated Health Check script:
```bash
/var/www/priya/scripts/check-health.sh
```
