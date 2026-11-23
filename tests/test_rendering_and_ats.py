"""Integration tests for document rendering, 1-page compliance, and local ATS scoring."""

from pathlib import Path
import pytest
from resume_builder.ai.gemini_client import generate_offline_content
from resume_builder.ats.scorer import calculate_ats_readiness
from resume_builder.ats.validator import inspect_generated_pdf
from resume_builder.content.generator import build_resume_manifest
from resume_builder.jd_analysis.analyzer import JDAnalyzer
from resume_builder.profile.manager import ProfileManager
from resume_builder.project_selection.selector import select_projects_for_jd
from resume_builder.renderers.docx_renderer import render_docx
from resume_builder.renderers.pdf_renderer import render_pdf_guaranteed_one_page
from resume_builder.reports.report_writer import prepare_output_directory, write_complete_application
from resume_builder.utils.file_ops import sanitize_filename


def test_sanitize_filename():
    unsafe = 'Google: Senior / Lead "Developer" <SWE> | Kolhapur?*'
    safe = sanitize_filename(unsafe)
    assert ":" not in safe
    assert "/" not in safe
    assert '"' not in safe
    assert "<" not in safe
    assert ">" not in safe
    assert "|" not in safe
    assert "?" not in safe
    assert "*" not in safe


def test_end_to_end_one_page_rendering_and_ats_score(tmp_path):
    pm = ProfileManager()
    profile = pm.load_profile()
    projects = pm.load_projects()

    jd_text = """
    Job Title: Junior Java Developer
    Company: TechCorp Solutions
    Required Skills: Java, Spring Boot, MySQL, REST APIs, Git, JUnit
    Responsibilities:
    - Build and maintain CRUD REST APIs using Spring Boot and Hibernate
    - Write unit tests using JUnit 5
    - Optimize relational database queries in MySQL
    """
    analyzer = JDAnalyzer(profile, projects)
    jd = analyzer.analyze(jd_text)
    req_matrix = analyzer.evaluate_match(jd)

    selected_projects, scored_pool, _ = select_projects_for_jd(projects, jd, target_count=4)
    content = generate_offline_content(profile, selected_projects, jd, req_matrix)
    manifest = build_resume_manifest(profile, selected_projects, content, jd, model_used="test-engine")

    # Render PDF
    pdf_out = tmp_path / "test_resume.pdf"
    render_res = render_pdf_guaranteed_one_page(manifest, pdf_out)
    assert render_res == 1, f"Generated PDF has {render_res.page_count} pages, expected exactly 1!"
    assert render_res.vertical_utilization_pct >= 80.0, f"Vertical utilization too low: {render_res.vertical_utilization_pct}%"
    assert Path(render_res.preview_png).exists(), "Visual QA preview PNG was not generated!"

    # Render DOCX
    docx_out = tmp_path / "test_resume.docx"
    render_docx(manifest, docx_out)
    assert docx_out.exists()
    assert docx_out.stat().st_size > 1000

    # ATS Scoring from actual PDF
    ats_report = calculate_ats_readiness(pdf_out, jd, req_matrix)
    assert ats_report.overall_score >= 70, f"ATS score too low: {ats_report.overall_score}"
    assert ats_report.format_score == 30, f"Format score not max: {ats_report.format_score}"
    assert "Java" in ats_report.matched_must_have or "Spring Boot" in ats_report.matched_must_have

    # Inspect rendered PDF text
    inspection = inspect_generated_pdf(pdf_out)
    assert inspection.is_text_selectable is True
    assert inspection.page_count == 1
    assert inspection.bearing_fault_position_ok is True
    assert "SUJAL KADAM" in inspection.extracted_text
    # Professional development presence
    assert "PROFESSIONAL DEVELOPMENT" in inspection.extracted_text or "Tata Cybersecurity" in inspection.extracted_text
