# End-User Workflow & Operations Manual

**Product:** AI-Powered Resume Builder & Candidate Platform  
**Target Audience:** Job Seekers, Candidates, Career Engineers  

---

## 1. Candidate Profile Management

The platform supports multiple independent candidate profiles with complete data isolation.

### Switching Profiles:
1. In the top navigation header, locate the **Candidate Switcher** dropdown.
2. Select your desired profile (e.g., `Sujal Sunil Kadam` or `Aarav Sharma (Demo Candidate)`).
3. All dashboard metrics, target job postings, and resume drafts will instantly update to reflect the active candidate context.

### Managing Profile Evidence (`/profiles`):
Navigate to **Candidate Profiles** to manage your verified career data:
- **Overview:** Edit full name, professional headline, location, and verified contact links.
- **Projects:** Add projects with titles, descriptions, technologies used, and highlight metrics.
- **Skills:** Organize technical skills into categorized groups (Languages, Frameworks, Cloud & DevOps, Databases, Core CS).
- **Education & Experience:** Record academic degrees, GPAs, and formal employment history.
- **Credentials & Certifications:** Maintain verified professional certifications and virtual job simulations.

---

## 2. Ingesting & Analyzing Job Descriptions (`/job-descriptions`)

1. Click **Target Job Descriptions** in the sidebar.
2. Click **Add Job Description**.
3. Enter the target **Job Title**, **Company Name**, and paste the full **Job Description Raw Text**.
4. Click **Save & Analyze**.
5. The analyzer extracts:
   - Mandatory and preferred technical skills.
   - Core job responsibilities.
   - Recommended technical keywords.
6. The candidate compatibility engine compares the requirements against your profile and produces an **Explainable Match Breakdown** (Required Skills 45%, Responsibilities 25%, Tech Stack 20%, Domain Relevance 10%).

---

## 3. Tailoring & Generating a Resume Draft (`/builder`)

1. Navigate to **Resume Builder**.
2. **Step 1 — Select Target Job:** Choose your target job description from the list.
3. **Step 2 — Select Candidate:** Choose the candidate profile to tailor.
4. **Step 3 — Review Recommended Projects:** The system recommends up to 4 projects ranked by the 45/25/20/10 engine. Any candidate-specific locked projects (e.g. Bearing Fault Diagnosis in slot #2) are automatically pinned.
5. **Step 4 — Generate Draft:** Select the AI provider (or Offline Engine) and click **Generate Tailored Resume**.

---

## 4. Interactive Side-by-Side Workspace & Live Preview

Upon generation, the platform opens the interactive workspace:
- **Left Panel (Interactive Editor):**
  - Edit your professional headline and summary.
  - Reorder or toggle technical skills.
  - Fine-tune project bullet points and impact metrics.
  - Add or omit positions of responsibility.
- **Right Panel (Live A4 Document Preview):**
  - Displays a 1:1 scale preview rendered at standard A4 proportions (794px × 1123px at 96 DPI).
  - Use the **Zoom Controls** (60% to 140%) or click **Fit** to adjust canvas viewport.
  - Real-time indicator displays `v1 · Draft`.

---

## 5. Human Approval & Version Locking

To prevent accidental distribution of unfinished drafts, document export is strictly gated by human approval:
1. When satisfied with the resume content, click **Approve Resume** in the editor toolbar.
2. Review the approval confirmation modal.
3. Click **Confirm & Lock Version**.
4. The resume transitions to `Approved` status, creating an immutable **Version 1 Snapshot** in the database.

---

## 6. Downloading Certified PDF and DOCX Exports

Once approved, one-click export buttons become active:
- **Download PDF:** Generates a publication-grade ReportLab PDF guaranteed to fit on exactly one A4 page without clipping or overflow.
- **Download DOCX:** Generates a clean, editable Microsoft Word document matching the design system typography.

---

## 7. Version Branching & History (`/resumes`)

1. If you edit an already-approved resume in the builder and save changes, the platform automatically **branches to Version 2** (`current_version: 2`).
2. The status returns to `Draft` (requiring re-approval before Version 2 can be exported).
3. The previous **Version 1 Snapshot** remains immutable and permanently accessible in the **Resume Library** under **Version History**.

---

## 8. ATS Diagnostics & Heuristic Evaluation (`/ats`)

1. Click **ATS Diagnostics** in the sidebar.
2. Select any tailored resume.
3. Click **Run ATS Diagnostic**.
4. Review your **100-Point Readiness Score**:
   - **Format Compatibility (Max 30 pts):** Evaluates layout simplicity, single-column parsing, and standard headings.
   - **JD Relevance (Max 50 pts):** Measures keyword coverage and skill alignment against the target job.
   - **Content Quality (Max 20 pts):** Assesses quantifiable impact metrics, action verbs, and bullet point conciseness.
5. Inspect the detailed keyword radar to identify any high-priority missing skills before submitting your application.
