# Project Architecture & System Design Manual

**Product Name:** AI-Powered Resume Builder & Candidate Platform  
**Architecture:** Modern Modular Monolith with Zero-Trust Edge Security  
**Version:** 1.0.0  
**Date:** November 2026  

---

## 1. Architectural Overview

The platform is engineered as a high-assurance **Modular Monolith**. It unifies an existing high-precision Python resume generation engine with an asynchronous FastAPI backend and a responsive React single-page application.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Frontend (React 18 + TS)                         │
│  - TanStack Query v5 state management    - Live scaled A4 document preview │
│  - Tailwind CSS + Lucide icons            - Multi-profile candidate switch  │
│  - Side-by-side interactive YAML editor   - ATS heuristic scoring radar     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / JSON API (REST)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Web Application                           │
│  - Cloudflare Access Zero-Trust JWT Auth  - Sliding-Window Rate Limiter     │
│  - OWASP Security Headers (CSP, HSTS)    - Global Exception Sanitization   │
│  - Candidate CRUD & Isolation Controls    - Version Snapshot Branching      │
└──────────────────┬──────────────────────────────────────────┬───────────────┘
                   │                                          │
                   ▼                                          ▼
┌────────────────────────────────────┐     ┌──────────────────────────────────┐
│      PostgreSQL 16 Database        │     │    Core Python Resume Engine     │
│  - SQLAlchemy 2.0 ORM + psycopg 3  │     │  - Multi-Provider AI Cascade     │
│  - 13 Relational Tables            │     │  - 45/25/20/10 Project Ranking   │
│  - Alembic Schema Migrations       │     │  - ReportLab Flowable Canvas     │
│  - Cascade Deletions & Auditing    │     │  - python-docx Document Builder  │
└────────────────────────────────────┘     └──────────────────────────────────┘
```

---

## 2. Frontend Architecture (`frontend/`)

### Core Technologies:
- **UI Framework:** React 18.3 with TypeScript 5.5
- **Build Tool:** Vite 5.4 (producing a highly optimized 430 kB production bundle)
- **Routing:** React Router DOM 6.26 (Nested routing under `AppLayout`)
- **Server State & Caching:** TanStack React Query 5.51 with automatic query invalidation and optimistic UI updates
- **Styling:** Tailwind CSS with CSS custom properties supporting dynamic Dark and Light themes

### Key Page Modules:
1. **Dashboard (`DashboardPage.tsx`):** Real-time PostgreSQL connectivity status, candidate profile counts, target JD activity, and AI provider health cascade overview.
2. **Profiles (`ProfilesPage.tsx`):** Tabbed candidate management (Overview, Projects, Skills, Experience, Education, Credentials), archive/restore controls, and fixed project safeguards.
3. **Job Descriptions (`JobDescriptionsPage.tsx`):** Raw JD ingestion, deterministic keyword and skill extraction, and candidate compatibility breakdown.
4. **Resume Builder (`ResumeBuilderPage.tsx`):** 4-step wizard, side-by-side interactive form editor, live A4 preview canvas with zoom/fit, and human approval modal.
5. **Resume Library (`ResumesPage.tsx`):** Library of draft and approved resumes, search, status filtering, version snapshot history, and one-click PDF/DOCX downloads.
6. **ATS Diagnostics (`AtsAnalysisPage.tsx`):** 100-point heuristic scoring radar (Format 30 pts, Relevance 50 pts, Quality 20 pts), keyword match density, and compliance checks.
7. **System Settings (`SettingsPage.tsx`):** Theme preferences, AI fallback sequence health, and database connection readiness.

---

## 3. Backend Architecture (`backend/app/`)

### Technology Stack:
- **Framework:** FastAPI 0.133 on Starlette with Uvicorn
- **Validation:** Pydantic 2.12 schemas for request parsing, data normalization, and strict API response models
- **Database Access:** SQLAlchemy 2.0 Declarative Base with thread-safe session lifecycle and psycopg 3 driver
- **Migrations:** Alembic 1.18 versioned migration scripts

### Database Relational Schema (13 Tables):
1. `candidate_profiles`: Candidate identity, slug, full name, headline, location, synthetic flag, config rules, and archive timestamps.
2. `educations`: Degree, institution, field of study, graduation year, and CGPA.
3. `experiences`: Employer, role, dates, location, and achievements.
4. `skills`: Category, skill name, proficiency level, and display priority.
5. `projects`: Project title, description, role, technologies, highlights, fixed position rules, and URLs.
6. `certifications`: Credential name, issuer, issue date, credential ID, and verification link.
7. `achievements`: Competitive programming ranks, awards, and recognitions.
8. `professional_developments`: Virtual job simulations, training programs, and workshops.
9. `job_descriptions`: Target job postings, raw text, company, title, and profile linkage.
10. `requirement_matrices`: Structured skill extraction, responsibilities, and keyword matches.
11. `resumes`: Tailored resume drafts, approved resumes, and full editable manifests.
12. `resume_versions`: Immutable version snapshots (v1, v2) capturing content state upon approval.
13. `ats_evaluations`: Deterministic ATS heuristic evaluation history.

---

## 4. Python Resume Engine (`src/resume_builder/`)

### Multi-Provider AI Fallback Architecture:
The resume engine implements an abstracted provider interface (`BaseProvider`) supporting an automated cascade:
1. **Google Gemini (Primary):** `gemini-2.5-flash` via `google-genai` SDK
2. **Groq API:** `llama-3.3-70b-versatile` for high-throughput generation
3. **Cohere API:** `command-r-plus-08-2024` via SDK v2
4. **OpenRouter API:** Access to open-weights models via REST client
5. **Cloudflare Workers AI:** Fast edge inference via REST client
6. **Offline Python Engine:** 100% deterministic local rule-based generator requiring zero external network calls or API keys

### Explainable 45/25/20/10 Project Selection Engine:
Project suitability is evaluated algorithmically:
$$\text{Score} = (0.45 \times \text{Skills}) + (0.25 \times \text{Responsibilities}) + (0.20 \times \text{Tech Stack}) + (0.10 \times \text{Domain})$$
- Strictly caps selected projects to **4 projects** per resume.
- Respects candidate-specific hard rules (e.g. permanent position #2 pinning).

---

## 5. Document Rendering & Quality Assurance

### Single-Page A4 PDF Engine:
- **Engine:** ReportLab Flowable Canvas Engine.
- **Dimensions:** 595.27 × 841.89 pt (Standard ISO 216 A4).
- **Guaranteed One-Page Fit:** Deterministic spacing budget dynamically scales font sizes (9.6 pt down to 9.0 pt) and line padding to prevent overflow.
- **Design Palette:** Editorial Deep Teal (`#174A45`) and Warm Copper (`#C47A42`).

### DOCX Engine:
- **Engine:** `python-docx` Document Builder.
- **Formatting:** Clean single-column layout with Times New Roman typography, matching section dividers, and clickable hyperlinks.

---

## 6. Zero-Trust Edge Security

- **Cloudflare Access JWT Authentication:** Cryptographic validation of `Cf-Access-Jwt-Assertion` using Cloudflare's public RS256 JWKS keys.
- **Production Fail-Closed:** Rejects all unauthenticated requests to protected endpoints when `APP_ENV=production`.
- **Security Headers:** Injects Content-Security-Policy, HSTS, X-Frame-Options: DENY, X-Content-Type-Options: nosniff.
- **Rate Limiting:** Sliding-window rate limiting on generation (10 req/min), analysis (15 req/min), and export (20 req/min).
