# PRODUCT REQUIREMENTS DOCUMENT (PRD)
# CareerOS — AI-Powered Resume Builder & Tailoring Platform

**Document Version:** 1.0  
**Date:** 24 November 2026  
**Product Type:** Personal AI-powered resume management and tailoring platform  
**Working Product Name:** CareerOS  
**Primary User:** Individual job seeker  
**Design Direction:** Premium SaaS  
**Theme:** Adaptive Light / Dark  
**Status:** Backend foundation implemented; hardening and remaining product development in progress

---

# 1. PRODUCT OVERVIEW

## 1.1 Product Vision

CareerOS is an AI-powered resume management and tailoring platform that helps job seekers maintain structured candidate profiles, analyze job descriptions, generate role-specific resumes, evaluate resume relevance, and manage multiple resume versions from one centralized application.

The product should transform the existing command-line resume-generation system into a polished web application without losing its existing Python resume engine.

It should behave like a professional career productivity tool rather than a basic AI resume generator.

## 1.2 Problem Statement

Job seekers frequently face these problems:

- Maintaining multiple versions of their resumes.
- Manually modifying resumes for different job descriptions.
- Identifying which projects and skills are most relevant to a role.
- Maintaining consistent candidate information across resumes.
- Understanding whether a resume adequately addresses job requirements.
- Tracking previously generated resumes.
- Repeatedly formatting and exporting documents.

CareerOS addresses these problems through centralized profile management, AI-assisted job analysis, intelligent content selection, structured resume editing, and automated document generation.

## 1.3 Product Objectives

1. Maintain multiple candidate profiles.
2. Store education, experience, skills, projects, certifications, and achievements in a structured database.
3. Analyze job descriptions and extract relevant requirements.
4. Match candidate information against job requirements.
5. Recommend relevant projects and skills.
6. Generate tailored, ATS-friendly resumes.
7. Allow manual editing and human approval.
8. Generate downloadable PDF and DOCX files.
9. Maintain resume versions and generation history.
10. Provide transparent ATS-style evaluation and improvement suggestions.

## 1.4 Product Success Criteria

The product will be considered successful when a user can:

- Create or select a candidate profile.
- Add and update profile information.
- Submit a job description.
- Review extracted job requirements.
- Review AI-recommended resume content.
- Edit generated content manually.
- Preview the resulting document.
- Approve and export a PDF or DOCX.
- Reopen previous versions and compare them.
- Use the application reliably on desktop and mobile-sized screens.

---

# 2. TARGET USERS AND PRODUCT SCOPE

## 2.1 Primary User

An individual job seeker applying to multiple software engineering and technology roles.

The initial version is designed for personal use, but the architecture should support additional candidate profiles and future expansion.

## 2.2 User Characteristics

- Maintains multiple candidate profiles.
- Applies to different job roles and companies.
- Needs role-specific resumes.
- Wants control over AI-generated content.
- Prefers structured editing over complex drag-and-drop design.
- Needs professional, one-page resume exports.
- Values privacy and data integrity.

## 2.3 Product Scope

### In Scope — Initial Product

- Multi-profile management.
- Candidate profile CRUD.
- Structured profile sections.
- Job description submission and analysis.
- Candidate-job matching.
- AI-assisted project selection.
- Resume generation.
- Manual resume editing.
- PDF and DOCX export.
- PDF preview.
- ATS-style evaluation.
- Resume history and version management.
- Dashboard and analytics.
- Responsive interface.
- Adaptive theme.
- Secure private deployment.

### Out of Scope — Initial Release

- Public user registration.
- Multi-tenant SaaS subscriptions.
- Payment gateway.
- Public resume sharing.
- Recruiter marketplace.
- Job application automation.
- Automatic submission to job portals.
- Collaborative editing.
- Microservices architecture.
- Real-time multiplayer editing.
- Kubernetes infrastructure.

These can be considered in future versions after the core product is stable.

---

# 3. PRODUCT DESIGN AND USER EXPERIENCE

## 3.1 Design Philosophy

CareerOS must have a premium SaaS interface.

The interface should feel polished, professional, restrained, and purposeful.

Design inspiration:
- Linear: navigation and interaction quality.
- Vercel: minimalism and typography.
- Notion: structured information management.
- Modern premium SaaS dashboards: cards, spacing, responsive layouts, and visual hierarchy.

Avoid:
- Excessive gradients.
- Unnecessary glassmorphism.
- Overloaded dashboards.
- Excessive animations.
- Generic AI-generated dashboard layouts.
- Inconsistent spacing and typography.
- Too many decorative cards.

## 3.2 Adaptive Theme

Support:

1. Light mode.
2. Dark mode.
3. System preference mode.

Requirements:
- Theme switcher in the application header or settings.
- Persist the selected preference.
- Respect operating-system preference when System is selected.
- Maintain sufficient contrast in both themes.
- Apply consistent tokens across components.
- Ensure charts, forms, tables, dialogs, and PDF previews remain readable.

## 3.3 Design System

Define reusable design tokens for:

- Primary and secondary colors.
- Background and surface colors.
- Text hierarchy.
- Borders and separators.
- Success, warning, and error states.
- Typography.
- Spacing.
- Border radius.
- Shadows.
- Focus states.
- Disabled states.

Use a consistent component library.

## 3.4 Navigation Structure

Primary sidebar:

1. Overview
2. Candidate Profiles
3. Resume Builder
4. Job Descriptions
5. Resume Library
6. ATS Analysis
7. Settings

Header:

- Current page title.
- Active candidate selector.
- Theme switcher.
- Notifications or system status.
- Profile menu.

The sidebar should support compact/collapsed mode.

## 3.5 Required UI Screens

### Screen 1 — Dashboard

Purpose: Provide a centralized overview.

Components:
- Welcome/header section.
- Active candidate profile.
- Total candidate profiles.
- Total generated resumes.
- Total job descriptions analyzed.
- Recent resume activity.
- Recent job descriptions.
- Quick action: Create Resume.
- Quick action: Add Job Description.
- Recent resume list.
- Resume generation status.
- Basic application usage statistics.

Empty state:
If no resumes exist, guide the user to create their first resume.

### Screen 2 — Candidate Profiles

Purpose: Manage multiple candidate profiles.

Components:
- Profile cards/list.
- Candidate name and headline.
- Location.
- Number of projects and skills.
- Last updated information.
- Active profile indicator.
- Create profile action.
- Edit, duplicate, archive, and restore actions where appropriate.

Profile selection must update the context used by the resume builder.

### Screen 3 — Candidate Profile Editor

Use structured sections:

1. Personal information.
2. Professional headline.
3. Professional summary.
4. Education.
5. Work experience.
6. Skills.
7. Projects.
8. Certifications.
9. Achievements.
10. Professional development.
11. Research publications.
12. Custom metadata.

Requirements:
- Add, edit, and remove entries.
- Reorder supported sections.
- Validate fields.
- Save changes.
- Show unsaved changes.
- Prevent accidental data loss.
- Preserve metadata and custom fields.

### Screen 4 — Job Description Management

Purpose: Store and manage job descriptions.

Components:
- Job description list.
- Company name.
- Job title.
- Location.
- Source URL, if supplied.
- Date added.
- Analysis status.
- Match score, when available.
- Search and filtering.
- Add new job description action.

Job descriptions must remain associated with the candidate profile and generated resume where applicable.

### Screen 5 — Job Description Analysis

Purpose: Understand what the employer expects.

Display extracted information:

- Job title.
- Company.
- Required skills.
- Preferred skills.
- Technical stack.
- Responsibilities.
- Experience requirements.
- Education requirements.
- Important keywords.
- Domain requirements.
- Other qualifications.

Allow the user to review and correct extracted information before proceeding.

Do not treat AI extraction as automatically correct.

### Screen 6 — Resume Builder

This is the primary product workflow.

Use a guided multi-step interface.

Step 1: Select candidate profile.

Step 2: Add or select job description.

Step 3: Analyze job requirements.

Step 4: Review candidate-job matching.

Step 5: Select relevant projects and skills.

Step 6: Generate resume content.

Step 7: Edit and approve content.

Step 8: Preview and export.

The interface should clearly display the current step and allow navigation to previous steps without losing progress.

### Screen 7 — Resume Editor

Use a structured editor rather than unrestricted drag-and-drop.

Requirements:
- Editable professional summary.
- Editable project descriptions.
- Editable experience descriptions.
- Skill selection.
- Section visibility controls.
- Section ordering where supported.
- Character and content validation.
- Save changes.
- Preview updates.
- Human approval before export.

AI-generated content must never be exported without explicit user approval.

### Screen 8 — Resume Preview

Display the actual generated document.

Requirements:
- PDF preview.
- Zoom controls.
- Page navigation.
- One-page A4 layout as the default target.
- Download PDF.
- Download DOCX.
- Regenerate after editing.
- Display rendering or export errors clearly.

The preview should represent the actual exported document, not a visually similar but unrelated HTML mockup.

### Screen 9 — Resume Library

Purpose: Manage previously generated resumes.

Display:
- Resume title.
- Candidate profile.
- Target company.
- Target job title.
- Generation date.
- Version number.
- File type.
- ATS-style score.
- Approval status.

Actions:
- Open.
- Preview.
- Download.
- Duplicate.
- Rename.
- Archive.
- View versions.

### Screen 10 — ATS Analysis

Display:
- Overall heuristic score.
- Formatting score.
- Relevance score.
- Content quality score.
- Matched keywords.
- Missing keywords.
- Missing qualifications.
- Improvement recommendations.

Use the existing scoring methodology:

- Format: 30%.
- Relevance: 50%.
- Content quality: 20%.

Clearly label this as an internal heuristic evaluation, not a guaranteed ATS result or a prediction of recruiter selection.

### Screen 11 — Settings

Include:
- Appearance preferences.
- Default resume format.
- Default candidate profile.
- AI provider configuration status.
- Resume generation preferences.
- Storage status.
- Application health status.
- Data export and backup information.

Do not expose API keys or secrets in the frontend.

---

# 4. FUNCTIONAL REQUIREMENTS

## 4.1 Candidate Profile Management

The system must:

- Create multiple candidate profiles.
- Retrieve profiles using UUID or slug.
- Update profiles.
- Archive profiles.
- Restore archived profiles.
- Manage nested profile resources.
- Validate unique profile slugs.
- Preserve profile-specific metadata.
- Maintain strict separation between candidate records.

Profile sections:

- Education.
- Experience.
- Skills.
- Projects.
- Certifications.
- Achievements.
- Professional development.

Additional metadata:
- Research publications.
- Custom fields.
- Project ranking rules.
- Verification information.
- Reconciliation metadata.
- Synthetic profile disclaimers.

The existing fixed Bearing Fault Diagnosis project rule for the Sujal profile must be preserved at position 2.

## 4.2 Job Description Management

Users must be able to:

- Create a job description.
- Paste job description text.
- Optionally provide company, role, and source URL.
- View saved job descriptions.
- Update and delete job descriptions.
- Associate job descriptions with candidate profiles.
- Re-run analysis.
- View previous analysis results where supported.

The application should not depend on web scraping to create a job description. Manual text input must always work.

## 4.3 Job Description Analysis Engine

Use the existing AI provider abstraction.

The analysis engine should extract structured data:

- Job title.
- Company.
- Required skills.
- Preferred skills.
- Responsibilities.
- Technical stack.
- Domain.
- Experience level.
- Education requirements.
- Keywords.

Output must follow validated structured schemas.

If an AI provider fails:
- Retry where appropriate.
- Use configured fallback providers.
- Apply timeouts.
- Return useful error information.
- Never return malformed output as valid analysis.

## 4.4 Candidate-Job Matching

Compare candidate information against extracted job requirements.

The system should evaluate:

- Skill relevance.
- Responsibility alignment.
- Technical stack alignment.
- Domain relevance.
- Experience and qualification alignment.

The existing project-ranking weights should be retained unless separately evaluated and approved:

- Skills: 45%.
- Responsibilities: 25%.
- Technical stack: 20%.
- Domain: 10%.

The system should explain recommendations instead of presenting unexplained scores.

## 4.5 Project Selection

The system should:

- Recommend relevant projects.
- Rank projects based on job requirements.
- Respect the maximum four-project selection limit.
- Preserve fixed project rules.
- Explain why each project was selected.
- Allow manual selection and deselection.
- Avoid inventing project details or achievements.

The user must retain final control over project selection.

## 4.6 Resume Generation

The existing Python resume engine remains the core generation engine.

The API should:

1. Receive the selected profile.
2. Receive the job description.
3. Retrieve candidate data.
4. Analyze the job requirements.
5. Select relevant candidate information.
6. Generate structured resume content.
7. Validate the content.
8. Pass approved content to the document renderer.
9. Store the resulting document and metadata.
10. Return the generated resume details.

Generation must preserve:
- Truthful candidate information.
- Existing project details.
- Research publication metadata.
- Hyperlinks.
- ATS-friendly formatting.
- One-page A4 layout as the default.
- Existing resume themes.

Do not silently change factual information to improve keyword matching.

## 4.7 Manual Editing and Approval

AI-generated content is a draft.

The user must be able to:
- Edit content.
- Remove irrelevant content.
- Correct AI mistakes.
- Approve the final version.
- Reject and regenerate content.

Only approved content can be exported as a final resume.

## 4.8 Document Export

Required output:
- PDF.
- DOCX.

Retain:
- Existing ReportLab PDF renderer.
- Existing python-docx DOCX renderer.

The system must validate:
- File generation.
- File existence.
- File type.
- File size.
- Document readability.
- Page count.
- Hyperlink preservation where supported.

PDF output should be checked after rendering.

## 4.9 ATS Evaluation

Retain the existing heuristic scoring methodology.

Provide transparent explanations for:
- Formatting.
- Relevance.
- Content quality.

Show:
- Matched requirements.
- Missing requirements.
- Keyword coverage.
- Suggested improvements.

Never claim that a score guarantees ATS compatibility or selection.

## 4.10 Resume History and Versioning

Every approved or generated resume version should have:

- Resume ID.
- Candidate profile ID.
- Job description ID.
- Version number.
- Generation timestamp.
- Content snapshot.
- Template information.
- File references.
- Evaluation reference.
- Approval state.

Users must be able to reopen and download earlier versions.

A new generation must not silently overwrite an earlier approved version.

## 4.11 Dashboard Analytics

Provide basic statistics:

- Candidate profiles.
- Job descriptions.
- Generated resumes.
- Approved resumes.
- Recent activity.
- Average heuristic score.

Avoid unnecessary analytics until sufficient data exists.

---

# 5. TECHNICAL ARCHITECTURE

## 5.1 Architecture Decision

Use a modular monolith.

Do not introduce microservices.

The existing Python resume engine remains independent of the HTTP interface and is exposed through FastAPI services.

## 5.2 Technology Stack

### Frontend

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- shadcn/ui.
- Lucide React.
- React Router.
- TanStack Query.
- React Hook Form.
- Zod.
- PDF.js or react-pdf.
- Recharts.
- Sonner.

### Backend

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy 2.x.
- Alembic.
- Existing resume-generation modules.

### Database

- PostgreSQL 16.
- UUID primary keys.
- JSONB for flexible metadata.
- Foreign-key relationships.
- Database indexes.
- Transaction management.

### Document Generation

- ReportLab.
- python-docx.

### AI Integration

Preserve the existing provider abstraction:

- Gemini.
- Groq.
- Cohere.
- OpenRouter.
- Cloudflare Workers AI.
- Offline deterministic mode.

Do not add another provider unless there is a clear requirement.

### Testing

- pytest.
- Vitest.
- React Testing Library.
- API integration tests.
- End-to-end tests using Playwright.

### Infrastructure

- Docker.
- Docker Compose.
- Vercel for frontend.
- Render or another suitable Python hosting service for backend.
- Supabase PostgreSQL.
- Private object storage.
- Cloudflare Access.

Provider free-tier limitations must be reviewed before deployment.

## 5.3 High-Level Architecture

User
↓
React + TypeScript Frontend
↓
FastAPI REST API
↓
Application Services
├── Profile Service
├── Job Description Service
├── Analysis Service
├── Matching Service
├── Resume Generation Service
├── ATS Evaluation Service
├── Resume History Service
├── Document Service
└── Storage Service

Application Services
├── PostgreSQL Database
├── Existing Python Resume Engine
├── AI Provider Abstraction
└── Private File Storage

## 5.4 Backend Folder Structure

Maintain the existing repository structure and adapt it where necessary.

Recommended logical structure:

backend/
- app/
  - api/
    - v1/
      - endpoints/
  - core/
  - database/
  - models/
  - schemas/
  - services/
  - integrations/
  - storage/
  - utils/
- alembic/
- tests/

Keep the existing resume engine in its current location unless a justified refactoring is required.

Avoid unnecessary file movement.

## 5.5 Frontend Folder Structure

frontend/
- src/
  - app/
  - components/
    - ui/
    - layout/
    - shared/
  - features/
    - dashboard/
    - profiles/
    - job-descriptions/
    - resume-builder/
    - resume-library/
    - ats-analysis/
    - settings/
  - hooks/
  - lib/
  - services/
  - types/
  - routes/
  - styles/

Organize code by feature.

Avoid giant components and duplicated API logic.

---

# 6. DATABASE REQUIREMENTS

The existing database contains 13 application tables:

1. candidate_profiles
2. educations
3. experiences
4. skills
5. projects
6. certifications
7. achievements
8. professional_developments
9. job_descriptions
10. resumes
11. resume_versions
12. ats_evaluations
13. file_assets

Existing profile records must be preserved.

The database already contains:
- 2 candidate profiles.
- 2 education records.
- 2 experience records.
- 94 skills.
- 11 projects.
- 9 certifications.
- 2 achievements.
- 2 professional development records.

Total: 124 records.

Future implementation must verify whether existing models and columns adequately support the requirements below.

Do not introduce duplicate tables or migrations without inspecting the existing schema first.

## 6.1 Job Description Data

Store:
- Profile relationship.
- Job title.
- Company.
- Description text.
- Source URL.
- Extracted requirements.
- Analysis status.
- Created and updated timestamps.

## 6.2 Resume Data

Store:
- Profile relationship.
- Job description relationship.
- Resume title.
- Target role.
- Target company.
- Generation status.
- Approval status.
- Latest version reference.
- Created and updated timestamps.

## 6.3 Resume Version Data

Store:
- Resume relationship.
- Version number.
- Structured content snapshot.
- Template identifier.
- File references.
- Evaluation reference.
- Approval status.
- Generation timestamp.

## 6.4 ATS Evaluation Data

Store:
- Resume version reference.
- Overall score.
- Formatting score.
- Relevance score.
- Content quality score.
- Matched keywords.
- Missing keywords.
- Recommendations.
- Evaluation timestamp.

## 6.5 File Asset Data

Store:
- File identifier.
- Related profile or resume.
- Storage key.
- File type.
- File size.
- Checksum where practical.
- Created timestamp.

Never store private files in publicly accessible storage.

---

# 7. API REQUIREMENTS

Base URL:

/api/v1

The existing profile CRUD APIs must be preserved.

## 7.1 Existing Profile APIs

- GET /profiles
- GET /profiles/{profile_id}
- POST /profiles
- PATCH /profiles/{profile_id}
- DELETE /profiles/{profile_id}
- POST /profiles/{profile_id}/restore

Nested CRUD:
- education
- experience
- skills
- projects
- certifications
- achievements
- professional-development

Review PUT semantics during backend hardening.

## 7.2 Job Description APIs

Proposed:

- GET /job-descriptions
- POST /job-descriptions
- GET /job-descriptions/{id}
- PATCH /job-descriptions/{id}
- DELETE /job-descriptions/{id}
- POST /job-descriptions/{id}/analyze
- GET /job-descriptions/{id}/analysis

## 7.3 Matching APIs

- POST /matching/analyze
- GET /matching/{id}

Matching responses should contain scores, matched requirements, missing requirements, and project recommendations.

## 7.4 Resume APIs

- GET /resumes
- POST /resumes
- GET /resumes/{id}
- PATCH /resumes/{id}
- DELETE /resumes/{id}
- POST /resumes/{id}/generate
- POST /resumes/{id}/approve
- POST /resumes/{id}/regenerate

## 7.5 Resume Version APIs

- GET /resumes/{id}/versions
- GET /resumes/{id}/versions/{version_id}
- POST /resumes/{id}/versions/{version_id}/restore

Restoring an earlier version should create a new version rather than destructively rewriting history.

## 7.6 Export APIs

- GET /resumes/{id}/export/pdf
- GET /resumes/{id}/export/docx
- GET /files/{file_id}

Download endpoints must verify ownership and approval status.

## 7.7 ATS APIs

- POST /resumes/{id}/evaluate
- GET /resumes/{id}/evaluations
- GET /evaluations/{evaluation_id}

All API responses must use validated schemas.

Apply appropriate HTTP status codes, pagination, and consistent error responses.

---

# 8. SECURITY AND PRIVACY

Security is a release requirement, not a future enhancement.

## 8.1 Access Model

Initial release:
- No public registration.
- No public user accounts.
- One authorized application user.
- Multiple candidate profiles.
- Deployment protected through Cloudflare Access.

## 8.2 Cloudflare Access

Protect both:
- Frontend application.
- Backend API.

Do not assume that protecting the frontend automatically protects the API.

Production configuration must fail closed.

The backend must not trust arbitrary identity headers supplied by an untrusted client. Validate the Access identity through a trusted authentication mechanism or verified token.

Development may permit local access through an explicit development configuration.

Production must never run with the protection disabled.

## 8.3 Data Protection

- Never commit `.env`.
- Never expose API keys in frontend code.
- Never expose database credentials.
- Use environment variables for secrets.
- Use private file storage.
- Validate file IDs and ownership.
- Prevent cross-profile data access.
- Restrict CORS to approved origins.
- Validate uploaded files.
- Avoid logging candidate contact information or document contents unnecessarily.
- Use HTTPS in production.

## 8.4 AI Data Privacy

Before transmitting candidate data to an external AI provider:

- Send only the information required for the task.
- Avoid unnecessary personal contact information.
- Keep provider credentials on the backend.
- Document provider data-handling considerations.
- Provide an offline deterministic mode where supported.

## 8.5 Database Safety

- Use parameterized ORM operations.
- Validate all inputs.
- Use transactions.
- Maintain backups.
- Verify restoration procedures.
- Prevent accidental deletion of candidate data.

---

# 9. NON-FUNCTIONAL REQUIREMENTS

## 9.1 Performance

Target:
- Dashboard loads quickly under normal network conditions.
- Profile pages use efficient database queries.
- Pagination is implemented for growing lists.
- PDF generation reports progress or status clearly.
- AI requests use timeouts and retry limits.
- Long-running operations do not block unrelated API requests unnecessarily.

Do not optimize prematurely.

## 9.2 Reliability

- Clear error handling.
- Database transaction integrity.
- AI provider fallback.
- Retry handling for temporary provider failures.
- Persistent file storage.
- No silent resume overwrites.
- Graceful handling of unavailable services.

## 9.3 Maintainability

- Modular frontend features.
- Separate API services and business logic.
- Reusable UI components.
- Type-safe frontend.
- Validated backend schemas.
- Automated tests.
- Documented setup and deployment.

## 9.4 Accessibility

- Keyboard navigation.
- Visible focus indicators.
- Appropriate contrast.
- Accessible form labels.
- Useful error messages.
- Responsive layouts.

## 9.5 Responsive Design

Prioritize:
1. Desktop.
2. Laptop.
3. Tablet.
4. Mobile.

The resume editor and PDF preview should adapt to smaller screens without losing essential functionality.

---

# 10. TESTING AND QUALITY ASSURANCE

## 10.1 Backend Testing

Use pytest.

Existing regression baseline: 100 passing tests reported after Milestone 2B.3.

Maintain tests for:
- Resume engine.
- Database connections.
- Health endpoints.
- Profile ingestion.
- Profile CRUD.
- Cross-profile isolation.
- Fixed project protection.
- Partial updates.
- Archive and restore.

Add tests for:
- Job description CRUD.
- AI analysis.
- Provider fallback.
- Matching.
- Project selection.
- Resume generation.
- Content approval.
- PDF export.
- DOCX export.
- Version history.
- ATS evaluation.
- File access.
- Transaction rollback.

## 10.2 Frontend Testing

Use Vitest and React Testing Library.

Test:
- Routing.
- Theme switching.
- Profile selection.
- Forms.
- Validation.
- API loading states.
- Error states.
- Resume editor.
- Approval flow.
- Preview rendering.
- Download behavior.

## 10.3 End-to-End Testing

Use Playwright.

Critical user journey:

1. Open application.
2. Select candidate profile.
3. Add job description.
4. Analyze job description.
5. Review matching results.
6. Select recommended projects.
7. Generate resume.
8. Edit generated content.
9. Approve resume.
10. Preview PDF.
11. Download PDF.
12. Download DOCX.
13. Reopen resume from history.
14. Verify earlier version remains accessible.

## 10.4 Document Quality Testing

Validate:
- PDF opens successfully.
- DOCX opens successfully.
- Correct candidate information.
- No fabricated information.
- No clipped text.
- No broken hyperlinks.
- Correct page dimensions.
- One-page output where content permits.
- Consistent formatting.

## 10.5 Regression Testing

Run the complete backend and frontend suites before release.

No existing functionality should break during frontend integration.

---

# 11. DEPLOYMENT ARCHITECTURE

## 11.1 Local Development

Use Docker Compose for local PostgreSQL and supporting services.

Frontend:
- React + Vite.

Backend:
- FastAPI.

Database:
- PostgreSQL 16.

Storage:
- Local filesystem through a storage abstraction.

AI:
- Existing provider configuration.

## 11.2 Production Deployment

Proposed deployment:

| Component | Service |
|---|---|
| Frontend | Vercel |
| Backend | Render or equivalent Python hosting |
| Database | Supabase PostgreSQL |
| File storage | Private Supabase Storage |
| Access protection | Cloudflare Access |
| Source control | GitHub |

Evaluate free-tier restrictions before choosing final providers.

Potential limitations:
- Backend sleep and cold starts.
- Database inactivity or project-pause policies.
- Storage limits.
- AI provider quotas.
- Request and execution timeouts.

Do not promise permanent free hosting or uninterrupted availability.

## 11.3 Environment Configuration

Maintain separate configurations for:
- Local development.
- Testing.
- Production.

Required settings may include:
- DATABASE_URL.
- AI provider credentials.
- Storage credentials.
- CORS origins.
- Cloudflare Access configuration.
- Application environment.
- File storage location.

Never include actual secrets in source code or documentation.

## 11.4 Production Release Checklist

- All tests passing.
- Production database configured.
- Migrations applied.
- Full database backup created.
- Private storage verified.
- API protected.
- Frontend protected.
- HTTPS enabled.
- CORS configured.
- Secrets configured.
- Health endpoints verified.
- PDF generation verified.
- DOCX generation verified.
- Data persistence verified.
- Backup restoration tested.
- No private candidate data exposed.
- Deployment logs reviewed.

---

# 12. DEVELOPMENT ROADMAP

The following roadmap assumes the existing implementation is retained and extended rather than rebuilt.

## Phase 1 — Foundation

### Milestone 1: Existing CLI and Resume Engine
Status: Implemented.

Includes:
- Python resume engine.
- AI provider abstraction.
- Offline deterministic mode.
- Structured output.
- JD analysis.
- Project ranking.
- ATS heuristic scoring.
- PDF and DOCX generation.
- Existing regression tests.

### Milestone 2A: PostgreSQL Foundation
Status: Implemented.

Includes:
- PostgreSQL.
- SQLAlchemy.
- Alembic.
- Database models.
- Health endpoints.
- Initial migration.

### Milestone 2B.1: Profile Ingestion Preparation
Status: Implemented.

Includes:
- Field mapping.
- Validation.
- Dry-run.
- Duplicate checks.

### Milestone 2B.2: Controlled Profile Import
Status: Implemented.

Includes:
- Transactional import.
- Two profiles.
- 124 records.
- Integrity verification.

### Milestone 2B.3: Profile CRUD APIs
Status: Reported completed.

Includes:
- Profile endpoints.
- Nested child CRUD.
- Pydantic schemas.
- Service layer.
- Ownership validation.
- Archive and restore.
- Fixed project protection.
- 100 reported passing tests.

### Milestone 2B.4: Backend Hardening
Status: Next.

Includes:
- Security audit.
- API route reconciliation.
- PUT/PATCH semantics.
- Transaction verification.
- Archival consistency.
- Full database backup.
- Additional regression tests.

## Phase 2 — Core Backend Features

### Milestone 2C: Job Description and Matching APIs

Implement:
- Job description CRUD.
- Structured JD analysis.
- Candidate-job matching.
- Project recommendations.
- Skill matching.
- Provider failure handling.

### Milestone 2D: Resume Generation APIs

Implement:
- Resume creation.
- Resume generation.
- Structured editing.
- Approval.
- PDF export.
- DOCX export.
- Generation status.

### Milestone 2E: Resume History and Storage

Implement:
- Resume versions.
- Content snapshots.
- File metadata.
- Private storage.
- Download APIs.
- Historical version restoration.
- ATS evaluation persistence.

## Phase 3 — Design and Frontend

### Milestone 3A: Stitch Design System

Create:
- Application design system.
- Dashboard.
- Profile management.
- Profile editor.
- JD analysis.
- Resume builder.
- Resume editor.
- PDF preview.
- Resume library.
- ATS analysis.
- Settings.

Export design references and design rules.

Use Stitch output as the visual reference, not as a replacement for the production architecture.

### Milestone 3B: React Frontend Foundation

Implement:
- Vite setup.
- React and TypeScript.
- Tailwind.
- shadcn/ui.
- Routing.
- Layout.
- Sidebar.
- Header.
- Theme switching.
- API client.
- Query management.
- Error handling.

### Milestone 3C: Profile and Dashboard Integration

Implement:
- Dashboard.
- Profile selector.
- Candidate profile list.
- Profile creation.
- Profile editing.
- Child resource management.

### Milestone 3D: Resume Builder Integration

Implement:
- JD submission.
- JD analysis.
- Matching results.
- Project selection.
- Resume generation.
- Structured editing.
- Human approval.

### Milestone 3E: Preview and Resume Library

Implement:
- PDF preview.
- DOCX download.
- Resume history.
- Version comparison.
- ATS score visualization.
- Resume management.

### Milestone 3F: Settings and Responsive Refinement

Implement:
- Theme preferences.
- Application settings.
- Error and empty states.
- Mobile responsiveness.
- Accessibility refinements.

## Phase 4 — Quality and Release

### Milestone 4A: Backend and Frontend Integration Testing

Validate every major workflow.

### Milestone 4B: End-to-End Testing

Run the full user journey through Playwright.

### Milestone 4C: Security and Data Integrity Audit

Verify:
- Access protection.
- Database isolation.
- Private file access.
- Secrets handling.
- Backups.
- Restoration.

### Milestone 4D: Production Deployment

Deploy frontend, backend, database, and storage.

### Milestone 4E: Production Verification

Test:
- Application access.
- API connectivity.
- Database persistence.
- AI generation.
- PDF and DOCX exports.
- Resume history.
- Error handling.
- Production security.

---

# 13. ACCEPTANCE CRITERIA

The project is ready for its initial release when all of the following are satisfied.

## Candidate Management
- Multiple profiles can be created and managed.
- Profile data persists after restart.
- Child resources remain associated with the correct profile.
- Cross-profile access is rejected.
- Existing profile data is preserved.

## Job Description
- Job descriptions can be created, edited, retrieved, and deleted.
- AI analysis produces validated structured output.
- Provider failures are handled.
- Analysis results can be reviewed.

## Resume Generation
- A selected profile can be combined with a job description.
- Matching results are available.
- Project recommendations are explainable.
- Resume content is editable.
- User approval is required.
- No unsupported candidate facts are introduced.

## Document Export
- PDF and DOCX generation work.
- Documents contain correct information.
- PDF preview reflects the actual generated file.
- Earlier approved versions remain accessible.

## ATS Evaluation
- Evaluation is persisted.
- Score breakdown is visible.
- Recommendations are understandable.
- No ATS guarantee is claimed.

## Frontend
- All primary screens are implemented.
- Adaptive theme works.
- API integration is functional.
- Loading, empty, success, and error states exist.
- Responsive layouts are usable.

## Security
- Production access is protected.
- Backend API is not publicly exposed without protection.
- Private storage is enforced.
- Secrets are not exposed.
- Candidate records remain isolated.

## Deployment
- Application works on production infrastructure.
- Database persistence is verified.
- Document generation is verified.
- Backups are available.
- Production smoke tests pass.

---

# 14. RISKS AND MITIGATION

| Risk | Mitigation |
|---|---|
| AI-generated inaccurate information | Human review and approval |
| AI provider rate limits | Retry, fallback, offline mode |
| Database corruption or accidental deletion | Full backups and restore testing |
| Cross-profile data exposure | Ownership checks and isolation tests |
| Public file exposure | Private storage and authorized downloads |
| Backend free-tier sleep | Clear deployment expectations and later hosting upgrade |
| PDF formatting errors | Automated rendering and document validation |
| Large frontend components | Feature-based architecture |
| Stitch export incompatibility | Treat exports as references; implement reusable React components |
| Scope expansion | Complete core workflows before optional features |

---

# 15. PRODUCT DEVELOPMENT PRINCIPLES

All future implementation work must follow these principles:

1. Preserve existing working functionality.
2. Inspect the existing code before modifying it.
3. Avoid unnecessary rewrites.
4. Prefer simple architecture over unnecessary complexity.
5. Keep the Python resume engine as the source of document-generation logic.
6. Keep frontend and backend responsibilities separate.
7. Use typed request and response contracts.
8. Keep database migrations deliberate and reviewed.
9. Never silently overwrite approved resume versions.
10. Never fabricate candidate experience, skills, metrics, or achievements.
11. Require human approval before final export.
12. Keep candidate information private.
13. Add automated tests for every major feature.
14. Do not introduce infrastructure without a demonstrated need.
15. Verify each milestone before starting the next.

---

# 16. FINAL PRODUCT DEFINITION

CareerOS is a private, AI-assisted career management application that converts structured candidate information and job descriptions into editable, role-specific, ATS-conscious resumes.

Its primary value is not simply generating a resume with AI.

Its value is combining:

- Structured candidate data.
- Intelligent job description analysis.
- Explainable candidate-job matching.
- Relevant project selection.
- AI-assisted content generation.
- Human-controlled editing and approval.
- Professional document generation.
- Resume history and version management.
- Private and reliable data storage.

The initial release should prioritize correctness, usability, privacy, and a complete end-to-end workflow over unnecessary feature count.

**Final product objective:** A user should be able to go from selecting a candidate profile to downloading a professionally formatted, role-tailored, approved resume through one polished web application.

**End of PRD.**