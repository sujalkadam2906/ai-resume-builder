# Production Deployment & Operations Guide

**Application:** AI-Powered Resume Builder & Candidate Platform
**Target Architecture:** Vercel (React SPA) + Render (FastAPI Backend) + Supabase (PostgreSQL + Auth)
**Audience:** DevSecOps Engineers, System Administrators, Full-Stack Developers

---

## 1. Production Architecture

```text
                       [ User Browser ]
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
         ▼ (HTTPS)                                 ▼ (HTTPS + Bearer JWT)
┌──────────────────────┐                ┌──────────────────────────────┐
│   Vercel Frontend    │                │     Render Web Service       │
│  React + Vite SPA    │                │       FastAPI Backend        │
│  - Supabase JS Auth  │                │  - Supabase JWKS JWT Verify  │
│  - Invite-only gate  │                │  - Tenant Ownership Scoping  │
└────────┬─────────────┘                │  - Sliding-Window Rate Limit │
         │                              └──────────────┬───────────────┘
         │ (Auth API)                                  │ (psycopg / SQLAlchemy)
         ▼                                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Supabase Platform                            │
│  - Supabase Auth (GoTrue, Email Confirmation, Password Recovery)     │
│  - Supabase PostgreSQL (13 App Tables + auth.users + RLS Policies)   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Authentication & Access Control Configuration

### Supabase Auth Dashboard Settings (Manual Verification Required)
1. **Authentication → Providers → Email**:
   - **Enable Email provider**: `ON`
   - **Confirm email**: `ON` (mandatory — prevents Supabase from issuing a session/JWT to unconfirmed email addresses).
2. **Authentication → URL Configuration**:
   - **Site URL**: `https://<your-vercel-domain>.vercel.app`
   - **Redirect URLs**: Add `https://<your-vercel-domain>.vercel.app/auth/callback`
3. **Authentication → Rate Limits / SMTP**:
   - Supabase Free tier default SMTP is rate-limited (low hourly email cap). Configure custom SMTP before opening public signup.

### Server-Side Enforcement (`backend/app/core/auth.py`)
- **JWT Verification**: Every protected `/api/v1/*` route requires `Authorization: Bearer <supabase_jwt>`, verified cryptographically via `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` (`RS256`, `ES256`, `EdDSA`), checking `aud`, `iss`, `exp`, and `sub`.
- **Email Verification**:
  - Standard Supabase JWTs do not include `email_confirmed_at` or top-level `email_verified` unless a Custom Access Token Hook is configured.
  - `SupabaseAuthValidator.verify_jwt()` rejects any token containing `email_verified: false` or `email_confirmed_at: null`.
  - When those claims are absent, `get_current_user()` queries `auth.users.email_confirmed_at` on PostgreSQL and rejects unconfirmed users with `HTTP 403`.
- **Access & Signup Gating (`ALLOWED_EMAILS` + `ALLOW_PUBLIC_SIGNUP`)**:
  - **Operator-only / Restricted Beta (default)**: `ALLOW_PUBLIC_SIGNUP=false` and `ALLOWED_EMAILS=operator@example.com` (or comma-separated beta list).
  - **Fail-closed safety**: If `ALLOWED_EMAILS` is empty AND `ALLOW_PUBLIC_SIGNUP=false`, the backend rejects all users with `HTTP 403`.
  - **Public SaaS (only after explicit approval)**: Set `ALLOW_PUBLIC_SIGNUP=true` (backend), `ALLOWED_EMAILS=` (empty), and `VITE_ALLOW_PUBLIC_SIGNUP=true` (frontend).

---

## 3. Supabase Free Plan Backup & Recovery Strategy

> [!IMPORTANT]
> **Supabase Free Plan Limitations & Exclusions:**
> 1. **No Automated Backups:** Supabase Free plan **does NOT include automated daily backups or Point-in-Time Recovery (PITR)**.
> 2. **What `supabase db dump` EXCLUDES by default:**
>    - Running `supabase db dump` (or `pg_dump` on public schema) dumps **only the application tables in the `public` schema**.
>    - It **excludes platform-managed schemas: `auth`, `storage`, `realtime`, and database extension internals**.
>    - It **excludes `auth.users` records**. Therefore, if you only dump the `public` schema and restore into a fresh database, all foreign keys referencing `auth.users(id)` (`user_id` on `candidate_profiles`, `resumes`, etc.) will fail or dangle!
>    - It **excludes database roles, passwords, and service-role grants**.
> 3. **Physical Storage Exclusions:** SQL dumps contain **zero binary file objects**. If `STORAGE_BACKEND=supabase` is configured, file blobs in Supabase Storage buckets are stored on object storage, not in database SQL dumps. (Currently, the app defaults to `STORAGE_BACKEND=local`, storing generated documents under `/app/storage/resumes`).

### Realistic Backup Limitations & What Can Actually Be Dumped:

#### Part A: Application Data Dump (`public` schema)
```bash
mkdir -p backups

# Export application schema and records (public tables only)
supabase db dump --db-url "$SUPABASE_DB_URL" -f backups/supabase_public_$(date +%Y%m%d_%H%M).sql
chmod 600 backups/supabase_*.sql
```

#### Part B: Auth Identity Limitation (UNRESOLVED RECOVERY LIMITATION)
> [!CAUTION]
> **Supabase Auth Schema Backup Is An Unresolved Recovery Limitation:**
> - `supabase db dump` is a wrapper that explicitly filters out platform-managed schemas, including `auth`.
> - Do not rely on unverified CLI flags to back up GoTrue auth state. Attempting to manually dump and restore the internal `auth` schema over a live Supabase project can corrupt authentication state, break GoTrue internal versioning, or violate platform constraints.
> - **Operational Reality:** On the Supabase Free plan, **there is no officially supported, fully verified end-to-end mechanism to export and restore the complete Supabase Auth service state**.
> - For rollback/recovery on the **existing** Supabase project, `auth.users` remains untouched in PostgreSQL by our migrations, which only modify `public` tables.
> - In a total disaster recovery scenario (e.g. migrating to a completely new Supabase project ref), user accounts and encrypted passwords cannot be automatically restored from a public SQL dump and would need to be re-invited or recreated via the Supabase Admin API.

#### Part C: Storage Objects
- For `STORAGE_BACKEND=local`: Persist the mounted server directory (`/app/storage/resumes` or `./storage`).
- For `STORAGE_BACKEND=supabase`: File blobs reside in object storage and are **not** present in SQL dumps. Mirror bucket contents via Storage API if enabled.

---

### Realistic Recovery Strategy & Limitations:

> [!WARNING]
> **Do not claim complete disaster recovery unless verified!**
> A tested, realistic recovery strategy follows:

1. **Validation on Disposable Local PostgreSQL (SCHEMA & APPLICATION FK VALIDATION ONLY)**:
   > [!NOTE]
   > The disposable local container test uses a lightweight `auth.users` table stub.
   > This validates **only application foreign keys, table constraints, and ownership backfill restoration**.
   > It does **NOT** validate or test real Supabase GoTrue Auth service recovery.
   ```bash
   docker run --name pg-backup-verify -e POSTGRES_PASSWORD=postgres -p 5435:5432 -d postgres:16
   PGPASSWORD=postgres psql -h localhost -p 5435 -U postgres -c "CREATE DATABASE restore_verify;"

   # Step 1: Initialize minimal auth.users stub to satisfy application foreign keys
   PGPASSWORD=postgres psql -h localhost -p 5435 -U postgres -d restore_verify -c \
     "CREATE SCHEMA IF NOT EXISTS auth; CREATE TABLE auth.users (id uuid PRIMARY KEY, email text, email_confirmed_at timestamptz); \
      INSERT INTO auth.users (id, email, email_confirmed_at) VALUES ('00000000-0000-0000-0000-000000000001', 'operator@example.com', now());"

   # Step 2: Restore public schema tables & data
   PGPASSWORD=postgres psql -h localhost -p 5435 -U postgres -d restore_verify -f backups/supabase_public_*.sql

   # Step 3: Verify sujal and demo_candidate integrity
   PGPASSWORD=postgres psql -h localhost -p 5435 -U postgres -d restore_verify -c \
     "SELECT slug, is_synthetic, user_id FROM candidate_profiles;"

   docker rm -f pg-backup-verify
   ```

2. **Rollback on Production Supabase (Maintenance Window Recovery)**:
   - If an upgrade failure occurs during the maintenance window:
     - Prefer executing the Alembic downgrade if schema-only: `alembic downgrade 4426bf87b36a`.
     - If public data corruption occurred, restore the `public` schema dump (`backups/supabase_public_*.sql`) using `psql` to recreate the public application tables.
     - `auth.users` will remain intact in Supabase Auth on the existing instance, preserving user UUIDs.
   - **Expected Downtime**: 15–30 minutes. Any new user activity created after the backup timestamp is lost.
   - **Storage Recovery**: If local storage was lost, re-generate exports from approved resume manifests via the API.

---

## 4. Production Migration Maintenance Window & Deployment Sequence

> [!IMPORTANT]
> **Why RLS Alone Is Insufficient During Migration:**
> The backend application connects to PostgreSQL using the primary database user (`postgres` / connection pooler). In PostgreSQL, superusers and table owners **bypass Row-Level Security (BYPASSRLS)** by default. Therefore, RLS policies enforced for limited roles do NOT restrict the backend service role!
> The **application code's query-level tenant isolation is the primary security boundary**. If the migration ran while the old backend was running, the old backend would serve newly backfilled data without user isolation checks!
> Consequently, **a scheduled maintenance window is mandatory** during migration.

### Step-by-Step Maintenance Window & Rollout Procedure:

1. **Verify Real Production Supabase Backup**:
   - Create a manual logical export via `supabase db dump` or `pg_dump` (Section 3).
   - Test-restore the dump into a disposable local PostgreSQL container to verify integrity of `sujal` and `demo_candidate`.

2. **Restrict Traffic / Enter Maintenance Window**:
   - **Render Backend**: In the Render Dashboard, suspend the Web Service or redirect inbound requests to a static maintenance page.
   - **Vercel Frontend**: Route to a maintenance notice or pause traffic to avoid incoming mutations during schema change.
   - **Supabase Auth**: In Supabase Dashboard → Authentication → Settings, confirm **"Disable new user signups"** is toggled ON to prevent new user creations during the migration window.
   - **Estimated Downtime**: 10–15 minutes.

3. **Review Migration SQL Offline**:
   ```bash
   alembic upgrade 7a8f9c0d1e2b --sql
   ```

4. **Apply Ownership Migration to Supabase**:
   ```bash
   alembic upgrade head
   ```

5. **Verify Database Integrity Immediately**:
   - Confirm `alembic current` returns `7a8f9c0d1e2b (head)`.
   - Execute verification query:
     ```sql
     SELECT slug, is_synthetic, user_id FROM candidate_profiles;
     ```
   - Confirm `sujal` has the operator's exact `auth.users.id` UUID (`is_synthetic = false`).
   - Confirm `demo_candidate` has `user_id IS NULL` and `is_synthetic = true`.
   - Confirm all 13 RLS policies exist:
     ```sql
     SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public';
     ```

6. **Deploy New Tenant-Enforcing Backend on Render**:
   - Set environment variables:
     - `APP_ENV=production`
     - `REQUIRE_AUTH=true`
     - `ALLOW_PUBLIC_SIGNUP=false`
     - `ALLOWED_EMAILS=<operator_email>`
   - Render Health Check Path: `/api/v1/health`.
   - Trigger deployment.

7. **Verify Backend Health & Tenant Isolation (Before Restoring User Traffic)**:
   - Probe liveness: `curl -I https://<backend>/api/v1/health` (HTTP 200).
   - Probe readiness: `curl -I https://<backend>/api/v1/health/ready` (HTTP 200).
   - Verify unauthenticated requests fail closed: `curl -I https://<backend>/api/v1/profiles` (HTTP 401).
   - Perform smoke query with operator JWT to confirm private profile is accessible.

8. **Deploy Frontend on Vercel**:
   - Set `VITE_ALLOW_PUBLIC_SIGNUP=false` (Invite-only default).
   - Deploy production build.

9. **Restore Public Traffic & Run Acceptance Tests**:
   - End maintenance window.
   - Verify end-to-end login, profile loading, and resume generation with operator credentials.
   - Confirm uninvited users receive 403 Forbidden.

10. **Future Public SaaS Transition (Only After Explicit Approval)**:
    - Only when ready to accept public registrations:
      - Supabase Dashboard: Enable new signups.
      - Render: Set `ALLOW_PUBLIC_SIGNUP=true` and clear `ALLOWED_EMAILS`.
      - Vercel: Set `VITE_ALLOW_PUBLIC_SIGNUP=true`.

---

## 5. Migration Rollback & Data-Loss Warning

> [!CAUTION]
> **Honest Downgrade Risks:** Running `alembic downgrade 4426bf87b36a` executes `DROP COLUMN user_id` on `candidate_profiles`, `job_descriptions`, `resumes`, and `file_assets`, and drops all 13 RLS policies.
> - **Permanent data loss:** Any multi-user ownership links (`user_id`) created after the upgrade will be **permanently destroyed** on downgrade, and multi-tenant isolation will stop working if the newer backend code is still running.
> - **Recommended rollback:** Put the backend in maintenance mode, restore the pre-migration logical Supabase backup created in Section 3, and redeploy the previous backend/frontend commits.

---

## 6. Health Checks & Monitoring

- **Liveness Probe (`/api/v1/health`)**: Returns `HTTP 200` whenever the FastAPI process is alive (no DB check). Configure **Render Health Check Path** to `/api/v1/health`.
- **Readiness Probe (`/api/v1/health/ready`)**: Verifies storage writeability, resume engine imports, and PostgreSQL connectivity (`SELECT 1`). Returns `HTTP 200` when healthy and `HTTP 503` when degraded, without exposing database URLs or credentials.
