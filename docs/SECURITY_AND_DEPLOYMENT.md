# Security Architecture & Production Deployment Manual

**Product:** AI-Powered Resume Builder & Candidate Platform
**Target Standard:** OWASP Top 10 API Security & Multi-Tenant Isolation
**Deployment Stack:** Vercel (Frontend) + Render (FastAPI Backend) + Supabase (PostgreSQL + Auth)

---

## 1. Supabase JWT Authentication & Multi-Tenant Isolation

### Authentication Workflow
1. User authenticates on the React SPA via Supabase Auth (`signInWithPassword`, email confirmation, password recovery).
2. Frontend attaches `Authorization: Bearer <access_token>` to all `/api/v1/*` requests.
3. FastAPI backend (`backend/app/core/auth.py`) validates every protected request:
   - Fetches public keys from `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`.
   - Verifies asymmetric signature (`RS256`, `ES256`, `EdDSA`) and mandatory claims (`aud`, `iss`, `exp`, `sub`, `email`).
   - Enforces email verification: rejects explicit unverified JWT claims (`email_verified: false` / `email_confirmed_at: null`) and verifies `auth.users.email_confirmed_at IS NOT NULL` on PostgreSQL when absent from standard Supabase JWTs.
   - Enforces `ALLOWED_EMAILS` and `ALLOW_PUBLIC_SIGNUP` (fails closed with `HTTP 403` if `ALLOWED_EMAILS` is empty and `ALLOW_PUBLIC_SIGNUP=false`).
4. Naked identity headers without a signed JWT are strictly rejected with `HTTP 401`.
5. Ownership is derived solely from verified JWT `sub` (`current_user.user_uuid`); client-supplied `user_id` values are ignored.

---

## 2. API & Application Security Hardening

### OWASP Security Headers (`backend/app/core/middleware.py`)
Every HTTP response includes `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, `Content-Security-Policy`, and `Strict-Transport-Security` (when `APP_ENV=production`).

### Sliding-Window Rate Limiting (`backend/app/core/rate_limiter.py`)
Process-local sliding-window rate limits keyed by `user:{user_id}` and fallback `ip:{client_ip}`:
- Resume Generation (`POST /api/v1/resumes/generate`): `10` req/min per user (`20` req/min per IP)
- JD Analysis (`POST /api/v1/job-descriptions/{jd_id}/analyze`): `15` req/min per user (`30` req/min per IP)
- ATS Evaluation (`POST /api/v1/resumes/{resume_id}/evaluate`): `15` req/min per user (`30` req/min per IP)
- Document Exports (`GET /api/v1/resumes/{resume_id}/export/pdf|docx`): `20` req/min per user (`40` req/min per IP)
- AI Provider Status (`GET /api/v1/system/providers`): `10` req/min per user (`20` req/min per IP)

> [!NOTE]
> **Process-Local Limitation:** The rate limiter stores counters in process memory. Limits reset on backend restarts and are not shared across multiple Render worker instances. A shared store (e.g., Redis) is recommended before scaling to multiple workers or opening public signup.

### Input-Size & Path Traversal Protections
- `JobDescriptionBase.raw_text` and `JobDescriptionUpdate.raw_text` are bounded to `max_length=50000` characters (`min_length=20`).
- Export directory paths sanitize candidate slugs and verify containment within `settings.storage_path.resolve()`.

---

## 3. Supabase Free Plan Backup & Recovery

- **No Automatic Backups on Free Plan:** Supabase Free does **not** provide automated daily backups or PITR.
- **Manual Logical Export:** Use `supabase db dump --db-url "$SUPABASE_DB_URL" -f backups/supabase_prod_YYYYMMDD.sql` (or `pg_dump --format=plain --no-owner --no-privileges`) before any migration.
- **Database vs. Storage:** SQL dumps cover PostgreSQL tables only; Supabase Storage bucket objects (if used) must be backed up separately.
- **Verification:** Always test-restore dumps into a disposable local PostgreSQL instance (`psql -d restore_verify -f ...`) before relying on them.

---

## 4. Production Deployment Order

1. Verify a real production Supabase backup/export and recovery plan.
2. Review exact migration SQL (`alembic upgrade 7a8f9c0d1e2b --sql`).
3. Apply the ownership migration to production Supabase (`alembic upgrade head`).
4. Verify migration revision, ownership backfill, private `sujal` profile, `demo_candidate` template, and related record integrity.
5. Deploy backend on Render (`/api/v1/health` for liveness probe).
6. Test API auth and two-user tenant isolation.
7. Deploy frontend on Vercel (`VITE_ALLOW_PUBLIC_SIGNUP=false`).
8. Test signup, email confirmation, login, logout, recovery, and resume workflow.
9. Only then decide whether public signup can be opened.
