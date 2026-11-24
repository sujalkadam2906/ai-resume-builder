# Quality Assurance & Testing Engineering Manual

**Project:** AI-Powered Resume Builder & Candidate Platform  
**Test Suite Size:** 130 Automated Tests (100% Passing)  
**Test Frameworks:** Pytest 9.2 (Python), TypeScript 5.5 / Vite 5.4 (Frontend)  

---

## 1. Test Architecture Overview

The platform maintains a high-assurance test pyramid covering unit, integration, security, and end-to-end workflows:

```
                            ▲
                           / \
                          / E2E\          1 Complete Resume Workspace Flow
                         /------\
                        /Security\        9 Zero-Trust & OWASP Guard Tests
                       /----------\
                      / Integration\      60 Database, Model, & API Tests
                     /--------------\
                    /   Unit Tests   \    60 Core Engine & Algorithm Tests
                   /──────────────────\
```

---

## 2. Running Test Suites

### Complete Test Run (All 130 Tests):
```bash
# Run core engine tests
pytest tests/ -v

# Run backend API and security tests
pytest backend/tests/ -v
```

### Targeted Security Hardening Suite:
```bash
pytest backend/tests/test_security_hardening.py -v
```

### Targeted End-to-End Workspace Lifecycle Test:
```bash
pytest backend/tests/test_m32_e2e_flow.py -v
```

### Frontend Build & Typecheck Verification:
```bash
npm --prefix frontend run build
```

---

## 3. Test Modules & Coverage Breakdown

### A. Core Engine Test Suite (`tests/` — 61 Tests)
1. `test_multi_profile_isolation.py` (22 tests): Verifies filesystem directory boundaries, SHA-256 migration integrity, traversal blocking, and candidate-specific fixed project rules.
2. `test_multi_provider.py` (10 tests): Validates the AI provider cascade, fallback triggers (HTTP 429, 401, 500, timeouts), and anti-hallucination sanitization.
3. `test_project_selection.py` (5 tests): Tests the 45/25/20/10 weighted scoring engine, 4-project cap, and slot #2 safeguard pinning.
4. `test_rendering_and_ats.py` (2 tests): Verifies single-page A4 document budget and 100-point ATS evaluation score.
5. `test_profile_and_reconciliation.py` (12 tests): Tests profile loading, skill classification, certification retention, and design palette integrity.
6. `test_extraction.py` (3 tests): Tests PDF text extraction and scanned PDF detection.
7. `test_jd_analysis.py` (3 tests): Tests canonical synonym resolution and skill extraction.
8. `test_documentation_release.py` (4 tests): Privacy compliance tests ensuring zero private phone numbers or personal emails are committed to tracked documentation.

### B. Backend API & Security Suite (`backend/tests/` — 69 Tests)
1. `test_security_hardening.py` (9 tests):
   - Cryptographic Cloudflare Access JWT validation (RS256 JWKS).
   - Rejection of forged signatures, expired tokens, and audience mismatches.
   - Rejection of naked `Cf-Access-Authenticated-User-Email` headers.
   - Production fail-closed behavior when `APP_ENV=production`.
   - OWASP security headers (`nosniff`, `DENY`, CSP, HSTS).
   - Sliding-window rate limiting on `/generate` and exports.
   - Directory traversal protection in file export paths.
2. `test_backend_hardening.py` (8 tests):
   - Strict PUT/PATCH semantics (PUT removed -> 405 Method Not Allowed).
   - Partial update field preservation.
   - Tamper-proofing `is_archived` and `archived_at` against PATCH injection.
   - Mutation locking on archived candidate profiles (HTTP 400).
   - Database transaction rollback on failed operations.
   - Global exception handling and sanitization of internal tracebacks.
3. `test_profiles_api.py` (14 tests): Candidate CRUD, pagination, unique slug enforcement (409 Conflict), child resource isolation (education, experience, skills, projects, certifications).
4. `test_resume_generation_api.py` (13 tests): Job description CRUD, analysis, matching, draft generation, version snapshot creation, and ATS evaluation.
5. `test_m32_e2e_flow.py` (1 test): Complete end-to-end lifecycle test covering profile check, JD ingestion, matching, draft generation, export rejection on draft, manual edit, approval, PDF/DOCX generation, version branching, and ATS scoring.
6. `test_profile_ingestion.py` (8 tests): JSON/YAML ingestion validation, dry-run auditing, and idempotent database loading.
7. `test_database.py` (7 tests): Database connection pooling, session lifecycle, cascade deletions, and readiness probes.
8. `test_health.py` (5 tests): Liveness, readiness, system info, and AI provider cascade health endpoints.

---

## 4. Continuous Integration Recommendations

In GitHub Actions or CI/CD pipelines, configure the test runner:
```yaml
name: Test Suite & Security Audit
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: resume_builder
        ports:
          - 5434:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: pip install -e . && pip install fastapi "uvicorn[standard]" "sqlalchemy>=2.0" "psycopg[binary]" alembic pyjwt cryptography pytest httpx
      - run: alembic upgrade head
      - run: pytest tests/ backend/tests/ -v
      - run: cd frontend && npm ci && npm run build
```
