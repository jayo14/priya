# Priya — Production Deployment Guide

This guide describes how to deploy the Priya application on a dedicated Linux server without requiring containerization or paid services.

## 1. System Requirements

- **Operating System**: Ubuntu 22.04 LTS or 24.04 LTS
- **Hardware**: Minimum 1 vCPU, 2GB RAM, 20GB SSD
- **Packages**:
  ```bash
  sudo apt update
  sudo apt install -y python3.12 python3.12-venv postgresql postgresql-contrib nginx curl
  ```
- **Node.js**:
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt install -y nodejs
  ```

## 2. PostgreSQL Configuration

Create a dedicated system user and databases:

```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE priya;
CREATE DATABASE priya_test;
CREATE USER priya_user WITH PASSWORD 'strong_production_password';
GRANT ALL PRIVILEGES ON DATABASE priya TO priya_user;
GRANT ALL PRIVILEGES ON DATABASE priya_test TO priya_user;
ALTER DATABASE priya OWNER TO priya_user;
ALTER DATABASE priya_test OWNER TO priya_user;
\q
```

## 3. Application Setup

Clone the repository to `/opt/priya` or user directory:

```bash
cd /opt/priya
cp .env.example .env
```

Edit `.env` for production:
```env
APP_NAME=Priya
APP_ENV=production
DEBUG=false

API_HOST=127.0.0.1
API_PORT=8000
API_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://priya_user:strong_production_password@127.0.0.1:5432/priya
FRONTEND_URL=https://yourdomain.com
CORS_ORIGINS=["https://yourdomain.com"]

LOG_LEVEL=INFO
TIMEZONE=Africa/Lagos
```

Install dependencies, run migrations, and seed:
```bash
make install
make db-migrate
make db-seed
make build-frontend
```

## 4. Systemd Service Management

### Backend Service (`/etc/systemd/system/priya-backend.service`)
```ini
[Unit]
Description=Priya FastAPI Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=priya
WorkingDirectory=/opt/priya/backend
ExecStart=/opt/priya/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5
EnvironmentFile=/opt/priya/.env

[Install]
WantedBy=multi-user.target
```

### Frontend Service (`/etc/systemd/system/priya-frontend.service`)
```ini
[Unit]
Description=Priya Next.js Frontend Service
After=network.target priya-backend.service

[Service]
Type=simple
User=priya
WorkingDirectory=/opt/priya/frontend
ExecStart=/usr/bin/npm run start -- -p 3000 -H 127.0.0.1
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=NEXT_PUBLIC_API_URL=https://yourdomain.com/api/v1

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now priya-backend
sudo systemctl enable --now priya-frontend
```

## 5. Nginx Reverse Proxy & SSL

Configure `/etc/nginx/sites-available/priya`:
```nginx
server {
    server_name yourdomain.com;

    # Frontend routes
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API routes
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable SSL via Certbot:
```bash
sudo certbot --nginx -d yourdomain.com
```

## 6. Security & Hardening Checklist

- [x] `DEBUG` set to `false` in production.
- [x] OpenAPI `/docs` and `/redoc` disabled in production.
- [x] Database credentials restricted to local socket or strong password.
- [x] CORS origins strictly limited to production domain.
- [x] Systemd services set to auto-restart on crash.
- [x] Backups enabled for PostgreSQL (`pg_dump`).
