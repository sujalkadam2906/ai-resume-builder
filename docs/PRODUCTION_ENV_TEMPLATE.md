# Production Environment Configuration Template

This document provides a sanitized configuration template for deploying the AI Resume Builder Platform on **Render (Backend)**, **Vercel (Frontend)**, and **Supabase (PostgreSQL + Auth)**.

> [!CAUTION]
> **NEVER** commit real API keys, tokens, or database passwords to version control. Configure these values only in Render / Vercel dashboard environment settings.

---

## 1. Render Backend Environment Variables

```ini
# ==============================================================================
# Core Application & Server Runtime
# ==============================================================================
APP_ENV=production
APP_NAME=AI Resume Builder Platform API
DEBUG=false
HOST=0.0.0.0
PORT=8000

# ==============================================================================
# CORS & Network Security
# ==============================================================================
# Exact Vercel production frontend origin(s), no wildcards (*)
CORS_ORIGINS=https://your-app.vercel.app

# ==============================================================================
# Supabase PostgreSQL Connection
# ==============================================================================
# Full SQLAlchemy connection string (use Supabase PostgreSQL credentials)
DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<db-password>@aws-0-<region>.pooler.supabase.com:5432/postgres

# ==============================================================================
# Supabase Auth & Access Control (Fail-Closed in Production)
# ==============================================================================
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_JWT_AUD=authenticated
REQUIRE_AUTH=true
ALLOW_DEV_AUTH_BYPASS=false

# Signup & Access Gate:
# - Operator-only / Restricted Beta: ALLOW_PUBLIC_SIGNUP=false and ALLOWED_EMAILS=operator@example.com
# - Public SaaS (only after explicit approval): ALLOW_PUBLIC_SIGNUP=true and ALLOWED_EMAILS=
ALLOW_PUBLIC_SIGNUP=false
ALLOWED_EMAILS=operator@example.com

# ==============================================================================
# Storage & Rate Limiting (Process-Local Sliding Window)
# ==============================================================================
STORAGE_BACKEND=local
RATE_LIMIT_GENERATION_PER_MINUTE=10
RATE_LIMIT_ANALYSIS_PER_MINUTE=15
RATE_LIMIT_EXPORT_PER_MINUTE=20

# ==============================================================================
# Multi-Provider AI Credentials (Backend Only)
# ==============================================================================
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id_here
```

---

## 2. Vercel Frontend Environment Variables

```ini
# Backend Render API URL (no trailing slash)
VITE_API_BASE_URL=https://your-backend.onrender.com

# Public Supabase Project URL and Anon Key (NEVER put service_role key in Vercel!)
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Keep false until public signup is explicitly approved
VITE_ALLOW_PUBLIC_SIGNUP=false
```

---

## 3. Pre-Deployment Validation Checklist

- [ ] `APP_ENV=production`, `DEBUG=false`, `REQUIRE_AUTH=true`, `ALLOW_DEV_AUTH_BYPASS=false`.
- [ ] `ALLOW_PUBLIC_SIGNUP=false` and `ALLOWED_EMAILS` set to authorized email(s) for initial rollout.
- [ ] `VITE_ALLOW_PUBLIC_SIGNUP=false` on Vercel.
- [ ] `SUPABASE_URL` and `CORS_ORIGINS` match exact production domains (HTTPS).
- [ ] Render Health Check Path is set to `/api/v1/health`.
- [ ] Supabase Dashboard → Auth → Email → **Confirm email** is enabled.
- [ ] Supabase Dashboard → Auth → URL Configuration includes `https://your-app.vercel.app/auth/callback`.
