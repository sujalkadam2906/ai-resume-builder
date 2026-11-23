"""Unit tests for profile management, reconciliation, and project database."""

from pathlib import Path
import pytest
from resume_builder.profile.manager import ProfileManager
from resume_builder.profile.reconciler import reconcile_resumes


def test_load_master_profile_and_projects():
    pm = ProfileManager()
    profile = pm.load_profile()
    projects = pm.load_projects()

    assert profile.personal_info.full_name == "Sujal Sunil Kadam"
    assert len(profile.personal_info.phone) >= 10
    assert len(projects) >= 6, f"Expected at least 6 verified projects, got {len(projects)}"
    assert any(p.id == "spring_notes_forge" for p in projects)
    assert any(p.id == "ai_resume_builder" for p in projects)

    # Check Bearing Fault is present as verified fixed project
    bf = next((p for p in projects if p.id == "bearing_fault_diagnosis"), None)
    assert bf is not None
    assert bf.is_fixed_project is True
    assert bf.fixed_position == 2


def test_reconciliation_conflict_audit():
    dummy_r1 = {"file_name": "R1.pdf", "text": "Entry-Level Software Engineer | Java, Spring Boot"}
    dummy_r2 = {"file_name": "R2.pdf", "text": "Entry-Level SWE / SWD | Java Full-Stack"}

    profile, projects, conflicts = reconcile_resumes(dummy_r1, dummy_r2)
    assert len(conflicts) >= 3
    conflict_fields = [c["field"] for c in conflicts]
    assert "headline" in conflict_fields
    assert "projects" in conflict_fields
    assert "professional_development" in conflict_fields


def test_seven_skills_categories_and_cloud_devops():
    pm = ProfileManager()
    profile = pm.load_profile()
    skills = profile.technical_skills

    # 1. 7 technical skill categories
    assert hasattr(skills, "cloud_devops_and_deployment")
    assert len(skills.cloud_devops_and_deployment) >= 4
    assert "Docker" in skills.cloud_devops_and_deployment
    assert "Kubernetes (Fundamentals)" in skills.cloud_devops_and_deployment

    # 2. MongoDB under Databases & SQL
    assert "MongoDB" in skills.databases_and_sql

    # 3. Python basic
    assert any("Python (Basic)" in s for s in skills.languages)


def test_certifications_retention_and_no_duplication():
    pm = ProfileManager()
    profile = pm.load_profile()

    # Master profile retains all 6 candidate-supplied credentials
    assert len(profile.certifications) == 6
    assert any("Cybersecurity" in c for c in profile.certifications)

    # In manifest generation, all 6 certifications are retained including the TCS simulation
    from resume_builder.content.generator import build_resume_manifest
    from resume_builder.jd_analysis.models import JobDescription, RequirementMatrix
    from resume_builder.ai.gemini_client import generate_offline_content

    projects = pm.load_projects()
    jd = JobDescription(company_name="TestCorp", job_title="Developer", raw_text="Developer role")
    content = generate_offline_content(profile, projects[:4], jd, RequirementMatrix())
    manifest = build_resume_manifest(profile, projects[:4], content, jd, model_used="test")

    # Visible certifications must contain all 6 credentials
    assert any("cybersecurity" in c.lower() for c in manifest.certifications)
    assert len(manifest.certifications) == 6

    # All 7 categories present in manifest ordered_skills
    assert len(manifest.ordered_skills) == 7
    assert "Cloud, DevOps & Deployment" in manifest.ordered_skills


def test_editorial_teal_copper_palette():
    from resume_builder.renderers.design_system import (
        HEX_MAIN_GRAPHITE,
        HEX_PRIMARY_TEAL,
        HEX_LIGHT_DIVIDER,
        HEX_WARM_COPPER,
        HEX_SECONDARY_TEXT,
        HEX_HYPERLINK,
        COLOR_HYPERLINK,
    )
    assert HEX_PRIMARY_TEAL == "#174A45"
    assert HEX_WARM_COPPER == "#C47A42"
    assert HEX_LIGHT_DIVIDER == "#D4DFD9"
    assert HEX_MAIN_GRAPHITE == "#263238"
    assert HEX_SECONDARY_TEXT == "#475B55"
    assert HEX_HYPERLINK == "#267BF1"
    assert COLOR_HYPERLINK.hexval().lower() == "0x267bf1"

    from resume_builder.renderers.design_system import (
        COLOR_PAGE_BORDER,
        COLOR_SECTION_DIVIDER,
        PAGE_BORDER_WIDTH_PT,
        SECTION_DIVIDER_WIDTH_PT,
    )
    assert PAGE_BORDER_WIDTH_PT == 1.5
    assert COLOR_PAGE_BORDER.hexval().lower() == "0x174a45"
    assert SECTION_DIVIDER_WIDTH_PT == 1.3
    assert COLOR_SECTION_DIVIDER.hexval().lower() == "0xc47a42"

    from resume_builder.renderers.design_system import (
        COLOR_PROJECT_TECH,
        FONT_PROJECT_TECH,
        HEX_PROJECT_TECH,
    )
    assert HEX_PROJECT_TECH == "#475B55"
    assert COLOR_PROJECT_TECH.hexval().lower() == "0x475b55"
    assert 9.0 <= FONT_PROJECT_TECH <= 9.5


def test_hyperlink_patch_and_six_certifications(tmp_path):
    import pypdf
    import docx
    from resume_builder.profile.manager import ProfileManager
    from resume_builder.content.generator import build_resume_manifest
    from resume_builder.ai.gemini_client import generate_offline_content
    from resume_builder.jd_analysis.models import JobDescription, RequirementMatrix
    from resume_builder.renderers.pdf_renderer import render_pdf_guaranteed_one_page
    from resume_builder.renderers.docx_renderer import render_docx

    from resume_builder.project_selection.selector import select_projects_for_jd

    pm = ProfileManager()
    profile = pm.load_profile()
    projects = pm.load_projects()

    jd = JobDescription(
        raw_text="Seeking Java Backend Developer with Spring Boot and SQL",
        company_name="Acme Corp",
        job_title="Java Developer",
        required_skills=["Java", "Spring Boot", "SQL"],
    )
    req = RequirementMatrix(must_have_skills=["Java", "Spring Boot", "SQL"])
    selected_projects, _, _ = select_projects_for_jd(projects, jd, target_count=4)
    content = generate_offline_content(profile, selected_projects, jd, req)
    manifest = build_resume_manifest(profile, selected_projects, content, jd, model_used="offline")

    # 1. Verify all 6 certifications are in manifest
    assert len(manifest.certifications) == 6
    assert any("Cybersecurity Analyst Job Simulation (TCS)" in c for c in manifest.certifications)

    # 2. Render PDF
    pdf_path = tmp_path / "test_patch.pdf"
    res = render_pdf_guaranteed_one_page(manifest, pdf_path)
    assert res == 1, "PDF must be exactly 1 page"

    # Inspect PDF text
    reader = pypdf.PdfReader(str(pdf_path))
    pdf_text = reader.pages[0].extract_text()
    assert "PROFESSIONAL DEVELOPMENT & JOB SIMULATIONS" in pdf_text
    assert "Tata Cybersecurity Security Analyst" in pdf_text
    assert "CERTIFICATIONS" in pdf_text
    assert "Cybersecurity Analyst Job Simulation (TCS)" in pdf_text
    assert "Core & Advanced Java (KG Placements)" in pdf_text
    assert "SQL Certification (Skill-Course)" in pdf_text
    assert "NPTEL Machine Learning & Deep Learning" in pdf_text
    assert "Tata" in pdf_text and "Ready Engineer Program" in pdf_text
    assert "Web Development (CodeWithHarry)" in pdf_text
    assert "EPJ Web of Conferences (2026)" in pdf_text

    # Inspect PDF annotations / links for DOI and #267BF1
    links_found = []
    if "/Annots" in reader.pages[0]:
        for annot in reader.pages[0]["/Annots"]:
            obj = annot.get_object()
            if "/A" in obj and "/URI" in obj["/A"]:
                links_found.append(obj["/A"]["/URI"])

    assert "https://doi.org/10.1051/epjconf/202635501004" in links_found
    assert any("linkedin.com" in l for l in links_found)
    assert any("github.com" in l for l in links_found)

    # 3. Render DOCX
    docx_path = tmp_path / "test_patch.docx"
    render_docx(manifest, docx_path)
    assert docx_path.exists()

    doc = docx.Document(str(docx_path))
    docx_text = "\n".join(p.text for p in doc.paragraphs)
    assert "PROFESSIONAL DEVELOPMENT & JOB SIMULATIONS" in docx_text
    assert "Cybersecurity Analyst Job Simulation (TCS)" in docx_text
    assert "EPJ Web of Conferences (2026)" in docx_text
