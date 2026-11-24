# REST API Reference Manual

**API Version:** v1  
**Base Path:** `/api/v1`  
**Authentication:** Zero-Trust Cloudflare Access JWT via `Cf-Access-Jwt-Assertion` header (or `Authorization: Bearer <token>`)  
**Data Format:** JSON (`application/json`)  

---

## 1. System & Health Probes (Public)

### `GET /health`
Liveness probe for load balancers and container orchestrators.
- **Access:** Public (No authentication required)
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-11-24T16:00:00Z"
}
```

### `GET /health/ready`
Readiness probe verifying database connection pool health.
- **Access:** Public (No authentication required)
- **Response (200 OK):**
```json
{
  "status": "ready",
  "database": "connected",
  "checks": {
    "database_ping": "ok",
    "connection_pool": "healthy"
  }
}
```

### `GET /system/info`
Safe environment and platform metadata.
- **Access:** Protected (Requires valid Cloudflare Access JWT)
- **Response (200 OK):**
```json
{
  "app_name": "AI Resume Builder Platform API",
  "app_version": "1.0.0",
  "environment": "production",
  "python_version": "3.13.12",
  "platform": "Windows-11-10.0.26100-SP0",
  "storage_backend": "local"
}
```

### `GET /system/providers`
Inspect status and health across the multi-provider AI fallback cascade.
- **Access:** Protected
- **Response (200 OK):**
```json
{
  "status": "success",
  "primary_provider": "Google Gemini",
  "fallback_sequence": ["Gemini", "Groq", "Cohere", "OpenRouter", "Cloudflare", "Offline"],
  "providers": [...]
}
```

---

## 2. Candidate Profiles (`/profiles`)

### `GET /profiles`
Retrieve paginated list of candidate profiles.
- **Query Parameters:** `page` (int, default: 1), `size` (int, default: 20), `include_archived` (bool, default: false)
- **Response (200 OK):** `ProfilePaginationResponse`

### `GET /profiles/{profile_id}`
Retrieve full candidate profile by slug or UUID.
- **Response (200 OK):** Full candidate details including nested educations, experiences, skills, projects, certifications, achievements, and professional developments.

### `POST /profiles`
Register a new candidate profile.
- **Request Body:** `CandidateProfileCreate` (requires `slug`, `full_name`, `email`, `phone`)
- **Response (201 Created):** Full candidate profile record.

### `PATCH /profiles/{profile_id}`
Partially update an active candidate profile. Unmentioned fields are preserved. Rejects mutations on archived profiles with HTTP 400.
- **Request Body:** `CandidateProfileUpdate`
- **Response (200 OK):** Updated candidate profile.

### `DELETE /profiles/{profile_id}`
Soft-deletes/archives a candidate profile.
- **Response (200 OK):** `{"status": "archived", "profile_id": "...", "slug": "..."}`

### `POST /profiles/{profile_id}/restore`
Restores a previously archived candidate profile to active listings.
- **Response (200 OK):** `{"status": "restored", "profile_id": "...", "slug": "..."}`

---

## 3. Job Descriptions (`/job-descriptions`)

### `POST /job-descriptions`
Ingest a new target job description.
- **Request Body:**
```json
{
  "job_title": "Backend Software Engineer",
  "company_name": "FinTech Global",
  "raw_text": "We are looking for a Python and FastAPI engineer...",
  "profile_id": "sujal",
  "source_url": "https://careers.example.com/job/101"
}
```
- **Response (201 Created):** Created JD record with assigned UUID.

### `POST /job-descriptions/{jd_id}/analyze`
Extract structured requirements, skills, responsibilities, and technical stack.
- **Rate Limit:** 15 requests per minute
- **Query Parameter:** `profile_id` (optional, candidate slug to contextualize match)
- **Response (200 OK):** `JobDescriptionAnalysisResponse`

### `GET /job-descriptions/{jd_id}/match`
Calculate candidate compatibility and explainable 45/25/20/10 project ranking.
- **Query Parameter:** `profile_id` (mandatory, candidate slug or UUID)
- **Response (200 OK):**
```json
{
  "job_description_id": "...",
  "candidate_profile_id": "...",
  "overall_match_percentage": 85.0,
  "score_breakdown": {
    "required_skills": 90.0,
    "responsibilities": 82.5,
    "tech_stack": 85.0,
    "domain": 75.0
  },
  "recommended_projects": [
    {"project_id": "...", "title": "AI Resume Builder", "score": 92.5},
    {"project_id": "...", "title": "Bearing Fault Diagnosis", "score": 100.0, "is_fixed": true, "fixed_position": 2}
  ]
}
```

---

## 4. Resumes & Document Exports (`/resumes`)

### `POST /resumes/generate`
Generate a new tailored resume draft based on an analyzed JD.
- **Rate Limit:** 10 requests per minute
- **Request Body:**
```json
{
  "profile_id": "sujal",
  "job_description_id": "...",
  "provider_override": "offline",
  "resume_title": "Sujal Kadam - SDE Python Tailored"
}
```
- **Response (201 Created):** `ResumeResponse` (status: `"draft"`, `current_version`: 1, full `editable_manifest`).

### `PATCH /resumes/{resume_id}`
Edit resume content manifest.
- **Version Branching Behavior:** If the resume was previously `approved`, editing increments `current_version` from 1 to 2, sets `status` to `"draft"`, and creates a new `ResumeVersion` record while preserving the version 1 snapshot immutable.
- **Response (200 OK):** Updated `ResumeResponse`.

### `POST /resumes/{resume_id}/approve`
Human approval action. Locks the current draft as an approved version and enables PDF/DOCX downloads.
- **Response (200 OK):**
```json
{
  "resume_id": "...",
  "status": "approved",
  "approved_version": 1,
  "approved_at": "2026-11-24T16:00:00Z"
}
```

### `GET /resumes/{resume_id}/export/pdf`
Download ReportLab publication-grade A4 PDF (strictly 1 single page).
- **Security Guard:** Rejects unapproved resumes with HTTP 400 Bad Request.
- **Rate Limit:** 20 requests per minute
- **Response (200 OK):** Binary file stream (`application/pdf`).

### `GET /resumes/{resume_id}/export/docx`
Download python-docx Word document.
- **Security Guard:** Rejects unapproved resumes with HTTP 400 Bad Request.
- **Rate Limit:** 20 requests per minute
- **Response (200 OK):** Binary file stream (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`).

### `POST /resumes/{resume_id}/evaluate`
Execute deterministic ATS evaluation (Format 30 pts, Relevance 50 pts, Quality 20 pts).
- **Response (200 OK):** `ATSEvaluationResponse` with breakdown, keyword density, and suggestions.
