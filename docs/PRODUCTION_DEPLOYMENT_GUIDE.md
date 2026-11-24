# Production Deployment & Operations Guide

**Application:** AI-Powered Resume Builder & Candidate Platform  
**Target Architecture:** Modular Monolith with Zero-Trust Edge Security  
**Audience:** DevSecOps Engineers, System Administrators, Full-Stack Developers  

---

## 1. Recommended Architecture

The production architecture is intentionally designed as an efficient, highly reliable modular monolith. It avoids unnecessary complexity (no Kubernetes, Redis, or Kafka clusters required) while providing enterprise-grade security and zero open inbound ports via Cloudflare Tunnel.

```
                              [ User Browser ]
                                     │
                                     ▼
                ┌─────────────────────────────────────────┐
                │        Cloudflare Zero Trust Edge        │
                │  - DDoS Protection & Web Application FW │
                │  - Identity Provider (Google / Email OTP)│
                │  - Injects 'Cf-Access-Jwt-Assertion'    │
                └────────────────────┬────────────────────┘
                                     │ Encrypted Cloudflare Tunnel
                                     ▼
     ┌─────────────────────────────────────────────────────────────┐
     │                     Production Server                       │
     │                                                             │
     │   ┌─────────────────────────────────────────────────────┐   │
     │   │                    cloudflared                      │   │
     │   │     (Zero open inbound ports on the host firewall)  │   │
     │   └──────────────┬──────────────────────┬───────────────┘   │
     │                  │                      │                   │
     │         Port 80  ▼             Port 8000▼                   │
     │    ┌──────────────────┐   ┌─────────────────────────────┐   │
     │    │  Nginx / Static  │   │       FastAPI Backend       │   │
     │    │   React SPA      │   │  - Independent JWT verify   │   │
     │    │   (Vite dist)    │   │  - Rate Limiter & Headers   │   │
     │    └──────────────────┘   │  - Resume Engine CLI        │   │
     │                           └─────────────┬───────────────┘   │
     │                                         │                   │
     │                                 Port 5432│                   │
     │                                         ▼                   │
     │                           ┌─────────────────────────────┐   │
     │                           │        PostgreSQL 16        │   │
     │                           │   (Encrypted Volume Mount)  │   │
     │                           └─────────────────────────────┘   │
     │                                                             │
     │    ┌────────────────────────────────────────────────────┐   │
     │    │ Persistent Storage: /app/storage/resumes           │   │
     │    └────────────────────────────────────────────────────┘   │
     └─────────────────────────────────────────────────────────────┘
```

---

## 2. Infrastructure & Hosting Requirements

### Minimum Recommended Server Specs:
- **Compute:** 2 vCPU cores
- **Memory:** 2 GB RAM (4 GB recommended for ReportLab PDF rendering spikes)
- **Disk:** 25 GB NVMe SSD storage
- **Operating System:** Ubuntu 22.04 LTS or Debian 12
- **Suitable Providers:** Hetzner Cloud (CX22/CPX21), Vultr High Frequency, DigitalOcean Droplet, AWS EC2 (t4g.small), or managed PaaS (Render / Railway with Supabase).

---

## 3. Server Environment Preparation

### Step 1: Install Docker & Docker Compose
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### Step 2: Configure Environment Variables
Copy `docs/PRODUCTION_ENV_TEMPLATE.md` to `.env` on your server:
```bash
cp docs/PRODUCTION_ENV_TEMPLATE.md .env
chmod 600 .env
```
Fill in your production PostgreSQL credentials, Cloudflare Access team name, Application AUD, and AI provider API keys.

---

## 4. Zero-Trust Cloudflare Access Setup

### Step 1: Add Application in Cloudflare Zero Trust Dashboard
1. Log in to [Cloudflare Zero Trust](https://one.dash.cloudflare.com/).
2. Navigate to **Access** > **Applications** > **Add an application**.
3. Select **Self-hosted**.
4. Configure application details:
   - **Application Name:** `AI Resume Builder`
   - **Application Domain:** `resume.yourdomain.com`
   - **Session Duration:** 24 hours
5. Under **Policies**:
   - Rule Name: `Allow Team`
   - Action: `Allow`
   - Criteria: `Emails` (enter authorized emails e.g. `your.email@example.com`) or `Emails Ending In` (`@yourcompany.com`).
6. Click **Next** to finalize.

### Step 2: Retrieve the Application AUD Tag
1. In the applications list, click your newly created application.
2. Click **Overview** or **View JWT AUD**.
3. Copy the alphanumeric Application Audience tag string.
4. Set this string in your server's `.env`:
   ```ini
   CF_ACCESS_TEAM_NAME=your-team-name
   CF_ACCESS_AUD=your_application_audience_tag_here
   REQUIRE_CF_ACCESS=true
   ```

### Step 3: Install & Start Cloudflare Tunnel (`cloudflared`)
Cloudflare Tunnel exposes the local web server to your domain without opening any inbound ports on your server firewall.
```bash
# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Authenticate tunnel
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create resume-builder-tunnel

# Configure ingress in ~/.cloudflared/config.yml:
tunnel: <TUNNEL_UUID>
credentials-file: /root/.cloudflared/<TUNNEL_UUID>.json

ingress:
  - hostname: resume.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404

# Route DNS
cloudflared tunnel route dns resume-builder-tunnel resume.yourdomain.com

# Run tunnel as a persistent system service
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

## 5. Database Setup & Migrations

### Step 1: Start PostgreSQL
```bash
docker compose up -d db
```

### Step 2: Run Alembic Database Migrations
Ensure the database schema is up-to-date with all 13 application tables:
```bash
docker compose run --rm backend alembic upgrade head
```

### Step 3: Seed Initial Candidate Profiles (One-Time)
Import the master candidate profiles into the database:
```bash
docker compose run --rm backend python -c "
from backend.app.database.session import SessionLocal
from backend.app.services.profile_ingestion import ProfileIngestionService

session = SessionLocal()
ingestion = ProfileIngestionService()
res = ingestion.import_all(session, target_profile_ids=['demo_candidate', 'sujal'], overwrite=False)
print('Ingestion Complete:', res)
session.close()
"
```

---

## 6. Frontend Production Build

The React single-page app must be compiled to optimized static assets:
```bash
# Build production bundle inside frontend/
npm --prefix frontend install
npm --prefix frontend run build
```
The output will reside in `frontend/dist/`. In production, this directory can be served via Nginx or embedded into the backend container as static files.

---

## 7. Starting the Backend Service

Run the containerized backend using Docker Compose:
```bash
docker compose up -d backend
```

Verify backend health:
```bash
curl http://localhost:8000/api/v1/health
# Response: {"status":"healthy","database":"connected","timestamp":"..."}

curl http://localhost:8000/api/v1/health/ready
# Response: {"status":"ready","database":"connected","checks":{...}}
```

---

## 8. Automated Database Backup Procedure

Backups are critical for production data safety.

### Running a Manual Backup
```bash
python scripts/backup_db.py
```
This script dumps the database via `pg_dump`, calculates a cryptographic SHA256 checksum, and saves metadata into `backups/`.

### Setting Up Automated Daily Backups via Crontab
Add a cron job to execute the backup script daily at 2:00 AM:
```bash
crontab -e
```
Add the following entry:
```cron
0 2 * * * cd /opt/ai-resume-builder && /usr/bin/python3 scripts/backup_db.py >> /var/log/resume_builder_backup.log 2>&1
```

### Database Restoration Procedure
In the event of hardware failure or disaster recovery:
1. Ensure the PostgreSQL service is running:
   ```bash
   docker compose up -d db
   ```
2. Restore the SQL backup file:
   ```bash
   cat backups/resume_builder_backup_<timestamp>.sql | docker exec -i resume_builder_db psql -U postgres -d resume_builder
   ```
3. Run readiness check to confirm restoration:
   ```bash
   curl http://localhost:8000/api/v1/health/ready
   ```

---

## 9. Monitoring & Maintenance

### Health & Liveness Checks:
- **Liveness Probe:** `GET /api/v1/health` (HTTP 200)
- **Readiness Probe:** `GET /api/v1/health/ready` (HTTP 200, checks DB connection pool)
- **AI Providers Cascade Status:** `GET /api/v1/system/providers` (Requires Cloudflare Access JWT in production)

### Inspecting Backend Logs:
```bash
docker compose logs -f backend --tail=100
```

---

## 10. Rollback Procedure

If a deployed update introduces defects:
1. **Revert Application Code / Image:**
   ```bash
   git checkout <PREVIOUS_STABLE_COMMIT_HASH>
   docker compose build backend
   docker compose up -d backend
   ```
2. **Revert Database Migration (if applicable):**
   ```bash
   docker compose run --rm backend alembic downgrade -1
   ```
3. **Emergency Database Restoration (if data corruption occurred):**
   Restore the latest pre-deployment backup using the procedure in Section 8.
4. **Verify Health:**
   ```bash
   curl http://localhost:8000/api/v1/health/ready
   ```
