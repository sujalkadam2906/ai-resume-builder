# Document 01: Technology Stack Interview Guide
## Deep-Dive Technical Reference & Software Engineering Interview Preparation

---

## 1. Introduction & Project Scope

The **AI Resume Builder** is a modular, production-grade Python application designed to solve the twin challenges of commercial ATS filtering and uncontrolled LLM hallucinations. Rather than allowing an AI model to hallucinate design, formatting, or candidate experience, the application uses **deterministic document engineering** coupled with **strictly bounded AI tailoring**.

This document serves as an exhaustive interview preparation manual, teaching how every technology in the project functions internally, why it was chosen over competing alternatives, where it lives in the codebase, and how to defend every architectural trade-off in senior engineering interviews.

---

## 2. Comprehensive Dependency Architecture

All versions match the resolved `pyproject.toml` specifications:

| Technology | Resolved Version | Primary Architectural Responsibility | Codebase Location | Selection Justification |
| :--- | :---: | :--- | :--- | :--- |
| **Python** | `3.10+` | Core programming language & execution runtime | Entire application | First-class AI SDK support, mature document processing ecosystem |
| **Pydantic** | `>=2.7.0` | Strict data validation, schema enforcement, JSON parsing | `src/resume_builder/ai/structured_schemas.py`, `profile/models.py` | Rust-backed speed, strict typing, schema generation for LLM structured output |
| **Google Gen AI SDK** | `>=2.0.0` | Official client library for Google Gemini models | `src/resume_builder/ai/providers/gemini_provider.py` | Native structured schema support (`response_schema`), low latency, long context |
| **Groq SDK** | `>=0.11.0` | Ultra-fast inference client for open weights | `src/resume_builder/ai/providers/groq_provider.py` | LPU hardware speed, highly cost-effective fallback tier |
| **Cohere SDK** | `>=5.0.0` | Enterprise LLM client for Command-R series | `src/resume_builder/ai/providers/cohere_provider.py` | Strong multi-lingual & structured JSON formatting reliability |
| **HTTPX** | `>=0.27.0` | Modern HTTP client for OpenRouter & Cloudflare | `src/resume_builder/ai/providers/openrouter_provider.py`, `cloudflare_provider.py` | Asynchronous/synchronous support, connection pooling, clean timeout handling |
| **ReportLab** | `>=4.0.0` | Programmatic PDF generation and geometry engine | `src/resume_builder/renderers/pdf_renderer.py`, `components.py` | Pixel-level canvas control, Flowables layout, strict 1-page budget calculation |
| **python-docx** | `>=1.1.0` | Programmatic Microsoft Word (.docx) generation | `src/resume_builder/renderers/docx_renderer.py` | Direct OpenXML manipulation (`w:pBdr`, `w:shd`, `w:pgBorders`) matching PDF design |
| **pypdf** | `>=4.0.0` | PDF text extraction and layout inspection | `src/resume_builder/extraction/pdf_extractor.py`, `ats/validator.py` | Lightweight pure-Python text and annotation extraction for ATS verification |
| **pdfplumber** | `>=0.11.0` | Detailed PDF coordinate inspection & table layout | `src/resume_builder/extraction/pdf_extractor.py` | Precise bounding box & character-level coordinate auditing |
| **PyYAML** | `>=6.0.0` | Human-readable configuration parsing | `src/resume_builder/config.py`, `profile/manager.py` | Clean profile-specific rule declaration (`profile_config.yaml`) |
| **python-dotenv** | `>=1.0.0` | Secure environment variable injection | `src/resume_builder/config.py` | Prevents credential leaks by reading `.env` outside source control |
| **Rich** | `>=13.0.0` | Terminal formatting, progress steps, and tables | `src/resume_builder/cli.py` | High-fidelity CLI user experience with colored progress bars and panels |
| **Pytest** | `>=8.0.0` | Automated unit, regression, and security testing | `tests/` directory (56 automated tests) | Powerful fixtures, parameterized test runs, detailed assertion diffs |

---

## 3. Technology Area A: Python Fundamentals & Modular Architecture

### Architecture in the Project
The codebase follows standard modern Python packaging standards with `src/resume_builder` layout.

```
src/resume_builder/
├── config.py             # Global constants, paths, and AppConfig singleton
├── cli.py                # Command-line interface orchestration
├── ai/                   # Multi-provider cascade and structured prompt schemas
├── ats/                  # Text extraction and 3-pillar scoring engine
├── content/              # Compression engine and manifest builder
├── extraction/           # PDF, DOCX, and text ingestion
├── jd_analysis/          # Keyword taxonomy, synonyms, and requirement matrix
├── profile/              # Directory isolation, migration, and models
├── project_selection/    # Algorithmic ranking and fixed-position rules
├── renderers/            # ReportLab (PDF) and python-docx (DOCX) engines
├── reports/              # Versioned file output and audit package generation
└── utils/                # Atomic file writing, logging, text cleaning
```

### Key Python Concepts Used
1. **Pydantic v2 Models vs Dataclasses:**
   - While Python standard library `dataclasses` provide basic structure, `pydantic.BaseModel` provides runtime type coercion, field constraints (`Field(ge=0, le=100)`), custom validators (`@field_validator`), and automatic JSON Schema generation needed by LLMs.
2. **Context Managers & Atomic File Writing (`src/resume_builder/utils/file_ops.py`):**
   - Writing files directly can corrupt documents if the process terminates abruptly. The application uses atomic writing: write to a temporary file (`.tmp`) in the destination directory, flush and sync, then call `os.replace()` for an atomic filesystem operation.
3. **Robust Exception Hierarchy:**
   - Custom exceptions (`ProfileNotFoundError`, `ScannedPDFError`, `AllProvidersFailedError`) decouple error identification from error presentation.
4. **Environment Configuration via Singleton (`AppConfig`):**
   - `config.py` wraps configuration in an `AppConfig` class that validates environment variables, fallback priorities, and default thresholds upon import.

---

## 4. Technology Area B: AI Integration & Fallback Cascade

### Architecture in the Project
The system abstracts AI communication behind a clean interface:
```python
class BaseProvider(ABC):
    @abstractmethod
    def generate_tailored_content(
        self, profile: MasterProfile, projects: List[ProjectItem],
        jd: JobDescription, req_matrix: RequirementMatrix
    ) -> Tuple[TailoredResumeContent, str]:
        pass
```

### The Multi-Provider Priority Cascade
The application defines a strict priority chain in `data/config.yaml`:
$$\text{Gemini} \longrightarrow \text{Groq} \longrightarrow \text{Cohere} \longrightarrow \text{OpenRouter} \longrightarrow \text{Cloudflare} \longrightarrow \text{Offline Python Engine}$$

1. **Google Gemini (`gemini_provider.py`):**
   - Uses `google-genai` SDK v2.0+.
   - Model: `gemini-2.5-flash` (fast, cost-effective, high quality).
   - Structured Output: Leverages Gemini's native `response_schema=TailoredResumeContent` and `response_mime_type="application/json"` to guarantee schema conformance at the inference engine level.
2. **Groq (`groq_provider.py`):**
   - Uses `groq` Python SDK with `llama-3.3-70b-versatile`.
   - Ultra-low latency fallback; uses JSON object response mode with client-side Pydantic validation.
3. **Cohere (`cohere_provider.py`):**
   - Uses `cohere` SDK v2 with `command-r-plus-08-2024`.
   - Strong instruction following and enterprise JSON response modes.
4. **OpenRouter & Cloudflare (`openrouter_provider.py`, `cloudflare_provider.py`):**
   - Uses `httpx.Client` for standardized HTTP REST requests with connection pooling and explicit timeouts (25-30 seconds).
5. **Offline Python Engine (`offline_provider.py`):**
   - Completely deterministic, zero-network fallback.
   - Extracts exact candidate evidence matching JD keywords using rule-based algorithmic ranking. Guarantees 100% availability even during total Internet failure.

### Privacy Sanitizer
Before any candidate data is sent to an external provider:
`sanitize_candidate_evidence_for_privacy()` strips candidate phone numbers, personal emails, residential addresses, and personal URLs.

---

## 5. Technology Area C: Multi-Profile Architecture & Isolation

### Directory Boundaries
Each candidate exists within an isolated directory:
`profiles/{profile_id}/` containing:
- `master_profile.json`: Verified candidate history.
- `projects.json`: Candidate's verified project portfolio.
- `profile_config.yaml`: Candidate-specific rules (permanent headline, fixed project slots, prohibited terms).
- `source_resumes/`: Original candidate source documents.
- `audit/`: SHA-256 migration integrity logs.

### Security Defenses
1. **Path Traversal Protection (`src/resume_builder/config.py`):**
   ```python
   def get_profile_dir(profile_id: str) -> Path:
       if not re.match(r"^[a-zA-Z0-9_\-]+$", profile_id) or ".." in profile_id or "/" in profile_id or "\\" in profile_id:
           raise ValueError(f"Invalid profile ID: '{profile_id}'")
       return PROFILES_DIR / profile_id
   ```
2. **Synthetic Demo Candidate:**
   - `profiles/demo_candidate/` contains fictional data (Aarav Sharma) marked `is_synthetic: true`.
   - Tested with automated marker injection to ensure 0% cross-profile leakage.

---

## 6. Technology Area D: PDF & DOCX Document Engineering

### ReportLab Programmatic PDF Generation
1. **A4 Page Geometry:** Standard A4 size is $595.27 \times 841.89$ points ($8.27 \times 11.69$ inches).
2. **Usable Content Area:**
   - Margins: Top/Bottom $32\text{ pt}$, Left/Right $36\text{ pt}$.
   - Usable Width: $595.27 - (36 \times 2) = 523.27\text{ pt}$.
   - Usable Height: $841.89 - (32 \times 2) = 777.89\text{ pt}$.
3. **The 1-Page Guarantee (`compression_engine.py`):**
   - Calculates the height of every flowable.
   - If total height exceeds 777 pt, activates deterministic scaling:
     - Font size scales from 9.6 pt down to 9.0 pt.
     - Spacers and padding compress by 10-15%.
   - Prevents multi-page spillover deterministically.
4. **Visual Styling:**
   - 1.5 pt Deep Teal (`#174A45`) rectangular border drawn on Canvas.
   - Shaded table headings (`#E9F0ED`) with a 2.5 pt Warm Copper (`#C47A42`) left border and 1.3 pt copper divider line.
   - Clickable `#267BF1` hyperlinks via `<a href="..." color="#267BF1"><u>...</u></a>`.

### python-docx Matching Implementation
- Replicates the exact PDF styling in Microsoft Word format:
  - Custom XML page borders (`w:pgBorders`) with Deep Teal `#174A45` (`sz="12"`).
  - Heading background shading (`w:shd`) with Pale Mint `#E9F0ED`.
  - Heading bottom border (`w:bottom`) with Warm Copper `#C47A42`.
  - True document hyperlinks using document relationship IDs (`w:hyperlink`).

---

## 7. Technology Area E: ATS Validation & Scoring

The local ATS scoring engine operates on the **actual rendered PDF text**, not internal data structures, verifying real-world ATS readability:

$$\text{ATS Total Score} = \text{Format Compatibility (30)} + \text{JD Relevance (50)} + \text{Content Quality (20)}$$

1. **Format Compatibility (30 points):**
   - Single-column structure check (+5)
   - Exact 1-page fit (+8)
   - Complete contact row (+5)
   - Standard uppercase section headings (+4)
   - Selectable text extraction (+4)
   - Zero prohibited terms (+4)
2. **JD Relevance (50 points):**
   - Must-have technical skills match (+35 max, proportional to coverage)
   - Preferred technical skills match (+10 max)
   - Keyword density ratio (+5)
   - Unsupported skills are **truthfully omitted** to prevent fabrication penalties.
3. **Content Quality (20 points):**
   - Strong action verbs at bullet starts (+8)
   - Quantifiable numerical metrics (+6)
   - Bullet conciseness (+3)
   - Evidence verification from database (+3)

---

## 8. Technology Area F: CLI & User Experience

- **PowerShell Wrapper (`resume.ps1`):** Native Windows interface with parameters (`-Profile`, `-JDPath`, `-Offline`, `-CheckProviders`, `-ValidateProfile`, `-ListProfiles`).
- **Rich Terminal Interface (`cli.py`):** Provides a 7-step progressive status workflow:
  - `[1/7]` Reading candidate profile
  - `[2/7]` Analyzing job description
  - `[3/7]` Mapping requirements to evidence
  - `[4/7]` Selecting projects
  - `[5/7]` Generating tailored content
  - `[6/7]` Rendering 1-page PDF and DOCX
  - `[7/7]` Running ATS validation
- **Exit Codes:** Returns 0 on success, 1 on validation or configuration failure.

---

## 9. Technology Area G: Automated Testing & Validation

The project is backed by **56 automated Pytest tests** organized across 8 test suites:

1. `test_extraction.py` (3 tests): Validates PDF text extraction, discovery, and scanned PDF error detection.
2. `test_gemini_fallback.py` (3 tests): Tests error classification, offline engine, and fallback cascade.
3. `test_jd_analysis.py` (3 tests): Validates keyword taxonomy, canonical synonyms, and requirement matrix.
4. `test_multi_profile_isolation.py` (24 tests): Tests registry integrity, directory isolation, marker injection, path traversal attacks, and dynamic vs. fixed project rules.
5. `test_multi_provider.py` (10 tests): Tests privacy sanitizer, mock provider adapters, priority chain overrides, and bearing fault safeguard.
6. `test_profile_and_reconciliation.py` (6 tests): Validates master profile loading, 7 skill categories, 6 certifications, design palette, and hyperlink patch.
7. `test_project_selection.py` (5 tests): Tests fixed-position placement across diverse JDs and deduplication.
8. `test_rendering_and_ats.py` (2 tests): End-to-end integration test validating exact 1-page PDF rendering and maximum Format Compatibility (30/30).

---

## 10. Senior Interview Questions & Technically Defensible Answers

### Question 1: Why did you choose ReportLab over browser-based HTML-to-PDF converters (like Puppeteer, WeasyPrint, or Playwright)?
**Answer:**
"Browser-based tools introduce massive external dependencies (Chromium binaries exceeding 300MB), non-deterministic font rendering across operating systems, and unpredictable page breaks. ReportLab is a pure Python programmatic layout engine that computes flowable heights down to points ($1/72$ of an inch). This allows us to calculate the exact vertical point budget ($777.89\text{ pt}$) before rendering and adjust font sizes deterministically to guarantee that the resume fits on exactly one page."

### Question 2: How do you prevent LLMs from hallucinating skills or inflating candidate metrics?
**Answer:**
"We implement a three-layer defense:
1. **Evidence-Bounded Context:** The LLM prompt is injected *only* with verified project bullets and approved skill taxonomies from `projects.json`.
2. **Negative Constraint Prompts:** The system explicitly instructs the model that any JD skill missing from candidate records must be classified as 'unsupported' and omitted from the resume.
3. **Deterministic Output Validation:** We parse the response into Pydantic models. Our validator cross-references every generated skill against the candidate's verified skill database. If an unverified claim appears, the system rejects it."

### Question 3: How does your multi-provider fallback handle cascading failures during an API outage?
**Answer:**
"We implement an abstracted `ProviderManager` with a priority cascade: Gemini $\to$ Groq $\to$ Cohere $\to$ OpenRouter $\to$ Cloudflare $\to$ Offline Engine. Each adapter catches transient HTTP errors (429 rate limits, 500/503 server disruptions, timeouts) and applies exponential backoff with jitter up to 3 retries. Non-retryable errors (such as 401 invalid key) immediately fail-over to the next provider. If all external APIs fail, the pipeline falls back to our local Offline Python Engine, guaranteeing that document generation never crashes."

### Question 4: How do you enforce security and prevent cross-profile data leakage?
**Answer:**
"Candidate profiles are stored in isolated directories under `profiles/{profile_id}/`. We protect against path traversal attacks by validating all profile IDs against the strict regex `^[a-zA-Z0-9_\-]+$`, instantly rejecting paths containing `../` or slashes. Furthermore, we maintain comprehensive Pytest suites using synthetic UUID marker injection: a unique token injected into one candidate profile is verified to have 0% occurrence across any other candidate's generated documents or manifest files."

### Question 5: Why is your ATS readiness score deterministic rather than AI-generated?
**Answer:**
"LLM-generated ATS scores are notoriously non-deterministic, giving different ratings on repeated runs for the same document. In contrast, our ATS validator parses the *actual binary PDF* using `pypdf`, extracts the plain text stream, and executes deterministic rule-based checks: verifying standard heading presence, calculating must-have keyword density against the JD, checking bullet point action verb counts, and verifying that the page count is exactly 1. This gives the candidate an objective, reproducible audit."
