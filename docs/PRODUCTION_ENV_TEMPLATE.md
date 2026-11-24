# Production Environment Configuration Template

This document provides a sanitized configuration template for deploying the AI Resume Builder Platform in production.

> [!CAUTION]
> **NEVER** commit real API keys, tokens, or database passwords to version control. This template contains placeholder values only. Copy these settings to your secure server environment variables or deployment manager (e.g. Doppler, AWS Secrets Manager, or server `.env`).

---

## Environment Variables Specification

```ini
# ==============================================================================
# 1. Core Application & Server Runtime
# ==============================================================================
# Set to 'production' to enforce fail-closed security, disable Swagger docs, and enforce HSTS
APP_ENV=production
APP_NAME=AI Resume Builder Platform API
DEBUG=false
HOST=0.0.0.0
PORT=8000

# ==============================================================================
# 2. CORS & Network Security
# ==============================================================================
# Comma-separated list of allowed origins. In production, never use wildcards (*)
CORS_ORIGINS=https://resume.yourdomain.com,https://app.yourdomain.com

# ==============================================================================
# 3. PostgreSQL Database Connection
# ==============================================================================
# Format: postgresql+psycopg://<user>:<password>@<host>:<port>/<database>
POSTGRES_USER=resume_app_user
POSTGRES_PASSWORD=generate_a_secure_random_password_here
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=resume_builder_prod

# Full SQLAlchemy database connection string
DATABASE_URL=postgresql+psycopg://resume_app_user:generate_a_secure_random_password_here@db:5432/resume_builder_prod

# ==============================================================================
# 4. Zero-Trust Cloudflare Access (Mandatory in Production)
# ==============================================================================
# Found in Cloudflare Zero Trust Dashboard -> Settings -> Custom Pages / Team Domain
CF_ACCESS_TEAM_NAME=your-team-name

# Found in Cloudflare Zero Trust Dashboard -> Access -> Applications -> View AUD
CF_ACCESS_AUD=your_application_audience_tag_hex_string

# Enforces cryptographic verification on all requests to protected API routes
REQUIRE_CF_ACCESS=true

# Strictly disables developer bypasses in production
ALLOW_DEV_AUTH_BYPASS=false

# Comma-separated list of verified emails permitted to access the application
# (Empty = all authenticated Cloudflare Access users in your team)
ALLOWED_EMAILS=your.email@example.com

# ==============================================================================
# 5. Persistent Storage Configuration
# ==============================================================================
# local: files stored on persistent server volume
# supabase: future object storage integration
STORAGE_BACKEND=local

# ==============================================================================
# 6. Rate Limiting & Resource Protection
# ==============================================================================
# Maximum allowed requests per 60-second sliding window per client
RATE_LIMIT_GENERATION_PER_MINUTE=10
RATE_LIMIT_ANALYSIS_PER_MINUTE=15
RATE_LIMIT_EXPORT_PER_MINUTE=20

# ==============================================================================
# 7. Multi-Provider AI Credentials (Backend Only)
# ==============================================================================
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Groq Cloud API Key
GROQ_API_KEY=your_groq_api_key_here

# Cohere API Key
COHERE_API_KEY=your_cohere_api_key_here

# OpenRouter API Key
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Cloudflare Workers AI Token & Account ID
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id_here
```

---

## Validation Checklist Before Deployment

- [ ] `APP_ENV` is set to `production`.
- [ ] `DEBUG` is set to `false`.
- [ ] `REQUIRE_CF_ACCESS` is set to `true`.
- [ ] `ALLOW_DEV_AUTH_BYPASS` is set to `false`.
- [ ] `CF_ACCESS_TEAM_NAME` matches your actual Cloudflare Access organization subdomain.
- [ ] `CF_ACCESS_AUD` matches the exact Application AUD tag from the Zero Trust portal.
- [ ] `POSTGRES_PASSWORD` is a strong, cryptographically generated string (min 32 characters).
- [ ] `CORS_ORIGINS` contains only your production frontend domain (HTTPS).
- [ ] File permissions on persistent `storage/` volume permit write access by the backend process.
