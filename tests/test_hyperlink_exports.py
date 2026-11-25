"""Comprehensive Tests for PDF and DOCX Hyperlink Exports, Project Live Demo + GitHub Links,
and URL Normalization in FormaCV.

Verifies:
1. Project with both Live Demo and GitHub.
2. Project with only GitHub.
3. Project with only Live Demo.
4. Project with neither link.
5. Schemeless URLs correctly normalized to https://.
6. URLs containing query parameters and ampersands (&).
7. PDF clickable URI annotations (/Annots -> /A -> /URI).
8. DOCX external hyperlink relationships (r:id -> Target with TargetMode="External").
9. Correct destinations - verifying exact URI targets, not merely link presence.
10. Existing profile GitHub, LinkedIn, and portfolio hyperlinks remain functional.
11. Verified test case with exact FormaCV project links:
    - Live Demo: https://ai-resume-builder-hdy9.vercel.app
    - GitHub: https://github.com/sujalkadam2906/ai-resume-builder
"""

from pathlib import Path
import docx
import docx.opc.constants
import pypdf
import pytest

from resume_builder.content.manifest import ManifestProject, ResumeContentManifest
from resume_builder.profile.models import LinkItem, LinksProfile, PersonalInfo
from resume_builder.renderers.components import ComponentStyles, build_project_entry
from resume_builder.renderers.docx_renderer import render_docx
from resume_builder.renderers.pdf_renderer import render_pdf_guaranteed_one_page
from resume_builder.utils.text_cleaner import normalize_url, escape_xml_attr


def test_normalize_url_cases():
    """Verify normalize_url ensures valid https:// scheme across edge cases."""
    # Standard valid https
    assert normalize_url("https://github.com/sujalkadam2906") == "https://github.com/sujalkadam2906"
    # Preserves http
    assert normalize_url("http://github.com/sujalkadam2906") == "http://github.com/sujalkadam2906"
    # Schemeless domain
    assert normalize_url("github.com/sujalkadam2906") == "https://github.com/sujalkadam2906"
    assert normalize_url("www.github.com/sujalkadam2906") == "https://www.github.com/sujalkadam2906"
    assert normalize_url("ai-resume-builder-hdy9.vercel.app") == "https://ai-resume-builder-hdy9.vercel.app"
    # Whitespace stripping
    assert normalize_url("  https://github.com/sujalkadam2906  ") == "https://github.com/sujalkadam2906"
    # URL with query parameters and ampersands
    complex_url = "https://ai-resume-builder-hdy9.vercel.app?demo=1&source=resume&ref=test"
    assert normalize_url(complex_url) == complex_url
    schemeless_complex = "ai-resume-builder-hdy9.vercel.app/demo?tab=projects&mode=live"
    assert normalize_url(schemeless_complex) == f"https://{schemeless_complex}"
    # Username with default_domain
    assert normalize_url("sujalkadam2906", default_domain="github.com") == "https://github.com/sujalkadam2906"
    # Fallback from display
    assert normalize_url("", default_domain="github.com", fallback="github.com/sujalkadam2906") == "https://github.com/sujalkadam2906"
    # Empty with default_domain
    assert normalize_url("", default_domain="github.com") == "https://github.com"
    # None input
    assert normalize_url(None, default_domain="github.com") == "https://github.com"
    # Preserves mailto
    assert normalize_url("mailto:test@example.com") == "mailto:test@example.com"


def test_formacv_live_demo_and_github_hyperlinks(tmp_path: Path):
    """Verify independent Live Demo and GitHub links in both PDF and DOCX using exact FormaCV test case."""
    formacv_live_demo = "https://ai-resume-builder-hdy9.vercel.app"
    formacv_github = "https://github.com/sujalkadam2906/ai-resume-builder"
    bearing_fault_github = "https://github.com/sujalkadam2906/bearing-fault-diagnosis"
    cloud_scale_demo = "https://cloud-scale.demo.app?env=prod&ref=cv"

    manifest = ResumeContentManifest(
        target_company="Stripe",
        target_role="Full Stack Software Engineer",
        model_used="test",
        personal_info=PersonalInfo(
            full_name="Sujal Kadam",
            display_name="SUJAL KADAM",
            phone="+91 9876543210",
            email="sujal@example.com",
            location="Pune, India",
        ),
        links=LinksProfile(
            linkedin=LinkItem(url="https://linkedin.com/in/sujalkadam", display="linkedin.com/in/sujalkadam"),
            github=LinkItem(url="https://github.com/sujalkadam2906", display="github.com/sujalkadam2906"),
            portfolio=LinkItem(url="https://sujalkadam.dev", display="sujalkadam.dev"),
        ),
        headline="Full Stack Software Engineer | Distributed Systems & Web Architect",
        summary="Software engineer with experience building scalable web architectures, AI-integrated workflows, and reliable backend systems.",
        ordered_skills={
            "Languages": ["Python", "TypeScript", "Java", "SQL"],
            "Backend & Frameworks": ["FastAPI", "React", "Node.js", "PostgreSQL"],
        },
        projects=[
            # 1. Project with BOTH Live Demo and GitHub (FormaCV test case)
            ManifestProject(
                id="formacv-project",
                title="FormaCV — AI-Powered Resume Builder",
                subtitle="FastAPI · React 18 · TypeScript · PostgreSQL · Supabase",
                bullets=[
                    "Engineered multi-tenant resume building platform with deterministic ATS grading and PDF/DOCX export.",
                    "Implemented zero-trust tenant isolation with Supabase RLS and token-verified authorization.",
                ],
                links=[
                    {"label": "Live Demo", "url": formacv_live_demo},
                    {"label": "GitHub", "url": formacv_github},
                ],
            ),
            # 2. Project with ONLY GitHub
            ManifestProject(
                id="bearing-fault-project",
                title="Bearing Fault Diagnosis System",
                subtitle="PyTorch · Signal Processing · 1D-CNN · CWRU Dataset",
                bullets=[
                    "Developed vibration diagnostic engine achieving 99.8% classification accuracy.",
                    "Published research paper in EPJ Web of Conferences on industrial vibration detection.",
                ],
                links=[
                    {"label": "GitHub", "url": bearing_fault_github},
                ],
            ),
            # 3. Project with ONLY Live Demo (and complex URL with query params & ampersand)
            ManifestProject(
                id="cloud-scale-project",
                title="CloudScale Real-Time Telemetry",
                subtitle="Go · Redis · WebSockets · Docker",
                bullets=[
                    "Built real-time telemetry streaming engine processing 50k events/sec.",
                    "Reduced pipeline latency by 45% using Redis pub/sub buffers.",
                ],
                links=[
                    {"label": "Live Demo", "url": cloud_scale_demo},
                ],
            ),
            # 4. Project with NEITHER link
            ManifestProject(
                id="internal-engine-project",
                title="Internal Cryptographic Ledger",
                subtitle="Rust · SQLite · SHA-256",
                bullets=[
                    "Designed zero-dependency append-only verifiable cryptographic ledger.",
                    "Benchmarked at 120,000 transaction signatures per second.",
                ],
                links=[],
            ),
        ],
        leadership=[],
        professional_development=[],
        education=[],
        achievements=[],
        research_publications=[],
        certifications=["AWS Certified Developer"],
    )

    # =========================================================================
    # PART A: PDF EXPORT & ANNOTATION VERIFICATION
    # =========================================================================
    pdf_out = tmp_path / "test_formacv_links.pdf"
    render_pdf_guaranteed_one_page(manifest, pdf_out)
    assert pdf_out.exists(), "PDF file was not created!"
    assert pdf_out.stat().st_size > 5000, "PDF file is suspiciously small or empty!"

    # Parse PDF annotations using pypdf
    reader = pypdf.PdfReader(str(pdf_out))
    assert len(reader.pages) == 1, f"Expected strictly 1 page, got {len(reader.pages)}"
    page = reader.pages[0]
    annots = page.get("/Annots", [])
    assert len(annots) >= 7, f"Expected at least 7 clickable annotations, got {len(annots)}"

    extracted_pdf_uris = []
    for a in annots:
        action = a.get_object().get("/A", {})
        uri = action.get("/URI")
        if uri:
            extracted_pdf_uris.append(str(uri))

    print("Extracted PDF URIs:", extracted_pdf_uris)

    # 1. Verify FormaCV Live Demo destination in PDF
    assert formacv_live_demo in extracted_pdf_uris, (
        f"FormaCV Live Demo destination '{formacv_live_demo}' missing from PDF annotations!"
    )
    # 2. Verify FormaCV GitHub destination in PDF
    assert formacv_github in extracted_pdf_uris, (
        f"FormaCV GitHub destination '{formacv_github}' missing from PDF annotations!"
    )
    # 3. Verify Project with only GitHub destination in PDF
    assert bearing_fault_github in extracted_pdf_uris, (
        f"Bearing Fault GitHub '{bearing_fault_github}' missing from PDF annotations!"
    )
    # 4. Verify Project with only Live Demo (and & parameter) in PDF
    assert cloud_scale_demo in extracted_pdf_uris, (
        f"CloudScale Live Demo '{cloud_scale_demo}' with query params missing from PDF annotations!"
    )
    # 5. Verify Profile links in PDF
    assert "https://linkedin.com/in/sujalkadam" in extracted_pdf_uris
    assert "https://github.com/sujalkadam2906" in extracted_pdf_uris
    assert "https://sujalkadam.dev" in extracted_pdf_uris

    # =========================================================================
    # PART B: DOCX EXPORT & RELATIONSHIP VERIFICATION
    # =========================================================================
    docx_out = tmp_path / "test_formacv_links.docx"
    render_docx(manifest, docx_out)
    assert docx_out.exists(), "DOCX file was not created!"
    assert docx_out.stat().st_size > 5000, "DOCX file is suspiciously small or empty!"

    doc = docx.Document(str(docx_out))
    # Extract external hyperlink relationships
    external_rels = [
        rel.target_ref
        for rel in doc.part.rels.values()
        if rel.reltype == docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK
    ]
    print("Extracted DOCX External Relationships:", external_rels)

    # 1. Verify FormaCV Live Demo destination in DOCX
    assert formacv_live_demo in external_rels, (
        f"FormaCV Live Demo destination '{formacv_live_demo}' missing from DOCX relationships!"
    )
    # 2. Verify FormaCV GitHub destination in DOCX
    assert formacv_github in external_rels, (
        f"FormaCV GitHub destination '{formacv_github}' missing from DOCX relationships!"
    )
    # 3. Verify Project with only GitHub in DOCX
    assert bearing_fault_github in external_rels, (
        f"Bearing Fault GitHub '{bearing_fault_github}' missing from DOCX relationships!"
    )
    # 4. Verify Project with only Live Demo in DOCX
    assert cloud_scale_demo in external_rels, (
        f"CloudScale Live Demo '{cloud_scale_demo}' missing from DOCX relationships!"
    )
    # 5. Verify Profile links in DOCX
    assert "https://linkedin.com/in/sujalkadam" in external_rels
    assert "https://github.com/sujalkadam2906" in external_rels
    assert "https://sujalkadam.dev" in external_rels

    # Verify DOCX paragraph run text formatting: "Live Demo | GitHub"
    all_doc_text = " ".join(p.text for p in doc.paragraphs)
    assert "FormaCV — AI-Powered Resume Builder" in all_doc_text
    assert "Live Demo" in all_doc_text
    assert "GitHub" in all_doc_text
    assert "|" in all_doc_text


def test_schemeless_project_links_auto_normalization(tmp_path: Path):
    """Verify schemeless project links e.g. 'github.com/...' and 'mysite.app' get normalized to https://."""
    manifest = ResumeContentManifest(
        target_company="Acme Corp",
        target_role="Software Engineer",
        model_used="test",
        personal_info=PersonalInfo(
            full_name="Alice Smith",
            display_name="ALICE SMITH",
            phone="+1 555-0100",
            email="alice@example.com",
            location="San Francisco, CA",
        ),
        links=LinksProfile(
            linkedin=LinkItem(url="linkedin.com/in/alicesmith", display="alicesmith"),
            github=LinkItem(url="github.com/alicesmith", display="alicesmith"),
            portfolio=LinkItem(url="alicesmith.io", display="alicesmith.io"),
        ),
        headline="Frontend Engineer",
        summary="Frontend engineer focused on accessible, high-performance web applications.",
        ordered_skills={"Languages": ["TypeScript", "JavaScript"]},
        projects=[
            ManifestProject(
                id="p1",
                title="Accessible Design System",
                subtitle="React · Tailwind · Storybook",
                bullets=["Built 30 WCAG-compliant accessible components."],
                links=[
                    {"label": "Live Demo", "url": "design-system.alicesmith.io"},
                    {"label": "GitHub", "url": "github.com/alicesmith/design-system"},
                ],
            )
        ],
        leadership=[],
        education=[],
        achievements=[],
        research_publications=[],
        certifications=[],
    )

    pdf_out = tmp_path / "test_schemeless.pdf"
    render_pdf_guaranteed_one_page(manifest, pdf_out)

    reader = pypdf.PdfReader(str(pdf_out))
    annots = reader.pages[0].get("/Annots", [])
    extracted_uris = [str(a.get_object().get("/A", {}).get("/URI")) for a in annots if a.get_object().get("/A", {}).get("/URI")]

    assert "https://design-system.alicesmith.io" in extracted_uris
    assert "https://github.com/alicesmith/design-system" in extracted_uris
    # Ensure none of the extracted URIs are missing https://
    for u in extracted_uris:
        if "design-system" in u:
            assert u.startswith("https://")
