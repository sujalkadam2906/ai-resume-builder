# Security Architecture & Production Deployment Manual

**Product:** AI-Powered Resume Builder & Candidate Platform  
**Target Standard:** OWASP Top 10 API Security & Zero-Trust Architecture  
**Release Version:** 1.0.0  

---

## 1. Zero-Trust Cloudflare Access Authentication

The platform implements independent cryptographic authentication on the backend entry point:

### Authentication Workflow:
1. External user accesses `resume.yourdomain.com`.
2. Cloudflare Zero Trust evaluates access policies (Identity Provider SSO / One-Time Email PIN).
3. Cloudflare signs the request and injects the header `Cf-Access-Jwt-Assertion`.
4. The FastAPI backend (`backend/app/core/auth.py`) intercepts the request:
   - Fetches public keys from `https://{team_name}.cloudflareaccess.com/cdn-cgi/access/certs`.
   - Parses RSA keys using `jwt.algorithms.RSAAlgorithm`.
   - Cryptographically verifies the `RS256` signature.
   - Validates mandatory claims: `aud` (Audience), `iss` (Issuer), `exp` (Expiration), `sub` (User ID).
   - Validates user email against the configured `ALLOWED_EMAILS` whitelist.
5. Naked or unverified headers (e.g. `Cf-Access-Authenticated-User-Email` without a signed JWT) are strictly rejected with HTTP 401 Unauthorized.
6. When `APP_ENV=production`, all protected endpoints fail closed if the JWT is missing or invalid.

---

## 2. API & Application Security Hardening

### OWASP Security Headers (`backend/app/core/middleware.py`):
Every HTTP response includes:
- `X-Content-Type-Options: nosniff` (Prevents MIME sniffing attacks)
- `X-Frame-Options: DENY` (Blocks framing and clickjacking)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: accelerometer=(), camera=(), geolocation=(), ...`
- `Content-Security-Policy: default-src 'self'; frame-ancestors 'none';`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` (HSTS active in production)

### Sliding-Window Rate Limiting (`backend/app/core/rate_limiter.py`):
Prevents Denial-of-Service and AI quota exhaustion on compute-heavy routes:
- Resume Generation (`/resumes/generate`): Max 10 requests / minute
- JD Analysis (`/job-descriptions/{id}/analyze`): Max 15 requests / minute
- Document Exports (`/export/pdf`, `/export/docx`): Max 20 requests / minute
- Exceeding limit returns `HTTP 429 Too Many Requests` with `Retry-After` header.

### File Storage Traversal Defense (`backend/app/services/resume_export_service.py`):
- Candidate slug parameters are sanitized with regex `re.sub(r"[^a-zA-Z0-9_\-]", "", slug)`.
- Storage directory paths are verified against `settings.storage_path.resolve()`, preventing directory traversal attacks (`../`).

---

## 3. Database Security & Backup Operations

### Network Isolation:
In production, the PostgreSQL 16 container communicates over an internal Docker network and is not exposed to the public Internet.

### Automated Backups (`scripts/backup_db.py`):
Execute a manual backup:
```bash
python scripts/backup_db.py
```
This utility:
- Executes `pg_dump` securely from the container.
- Computes a cryptographic SHA256 checksum.
- Records backup metadata and file size in `backups/`.

### Disaster Recovery & Restoration:
```bash
cat backups/resume_builder_backup_<timestamp>.sql | docker exec -i resume_builder_db psql -U postgres -d resume_builder
```

---

## 4. Production Deployment Steps

1. **Provision Linux Server:** Ubuntu 22.04 LTS (2 vCPU, 2-4 GB RAM).
2. **Install Docker & Docker Compose:** Official Docker Engine packages.
3. **Configure Environment:** Copy `docs/PRODUCTION_ENV_TEMPLATE.md` to `.env` on server and chmod 600.
4. **Deploy Cloudflare Tunnel:** Install `cloudflared` to expose backend port 8000 without opening inbound firewall ports.
5. **Run Database Migrations:**
   ```bash
   docker compose run --rm backend alembic upgrade head
   ```
6. **Build Frontend Assets:**
   ```bash
   npm --prefix frontend run build
   ```
7. **Start Backend Container:**
   ```bash
   docker compose up -d backend
   ```
8. **Verify Probes:**
   - Liveness: `curl http://localhost:8000/api/v1/health`
   - Readiness: `curl http://localhost:8000/api/v1/health/ready`
