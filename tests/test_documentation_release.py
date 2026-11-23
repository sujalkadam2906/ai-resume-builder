"""Automated release and documentation verification test suite."""

from pathlib import Path
import pypdf
import pytest

from resume_builder.config import PROJECT_ROOT


def test_documentation_markdown_files_exist():
    docs_dir = PROJECT_ROOT / "docs"
    assert (docs_dir / "01_TECH_STACK_INTERVIEW_GUIDE.md").is_file()
    assert (docs_dir / "02_SYSTEM_ARCHITECTURE_AND_WORKFLOW.md").is_file()
    assert (docs_dir / "03_INTERVIEW_PREPARATION.md").is_file()
    assert (docs_dir / "README.md").is_file()
    assert (PROJECT_ROOT / "README.md").is_file()


def test_documentation_pdf_exports_exist_and_selectable():
    pdf_dir = PROJECT_ROOT / "docs" / "pdf"
    expected_pdfs = [
        "01_TECH_STACK_INTERVIEW_GUIDE.pdf",
        "02_SYSTEM_ARCHITECTURE_AND_WORKFLOW.pdf",
        "03_INTERVIEW_PREPARATION.pdf",
    ]
    for pdf_name in expected_pdfs:
        pdf_path = pdf_dir / pdf_name
        assert pdf_path.is_file(), f"Missing PDF export: {pdf_name}"
        reader = pypdf.PdfReader(str(pdf_path))
        assert len(reader.pages) >= 4, f"PDF {pdf_name} has too few pages: {len(reader.pages)}"
        # Verify text selectability
        sample_text = reader.pages[0].extract_text()
        assert len(sample_text) > 100, f"PDF {pdf_name} text not selectable"


def test_documentation_assets_exist():
    assets_dir = PROJECT_ROOT / "docs" / "assets"
    assert (assets_dir / "demo_resume_preview.png").is_file()
    assert (assets_dir / "system_architecture.svg").is_file()
    assert (assets_dir / "multi_profile_isolation.svg").is_file()
    assert (assets_dir / "ats_scoring_breakdown.svg").is_file()


def test_demo_candidate_is_synthetic():
    demo_profile = PROJECT_ROOT / "profiles" / "demo_candidate" / "master_profile.json"
    demo_config = PROJECT_ROOT / "profiles" / "demo_candidate" / "profile_config.yaml"
    assert demo_profile.is_file()
    assert demo_config.is_file()

    p_text = demo_profile.read_text(encoding="utf-8")
    c_text = demo_config.read_text(encoding="utf-8")
    assert "Aarav Sharma" in p_text
    assert "FICTIONAL DEMONSTRATION DATA" in p_text
    assert "FICTIONAL DEMONSTRATION DATA" in c_text
    assert "is_synthetic: true" in c_text


def test_no_private_contacts_in_tracked_sources():
    sujal_profile = PROJECT_ROOT / "profiles" / "sujal" / "master_profile.json"
    if not sujal_profile.is_file():
        return
    import json
    data = json.loads(sujal_profile.read_text(encoding="utf-8"))
    phone = data.get("personal_info", {}).get("phone", "")
    email = data.get("personal_info", {}).get("email", "")
    if not phone or not email:
        return

    tracked_extensions = [".py", ".md", ".json", ".yaml", ".ps1", ".toml"]

    for path in (PROJECT_ROOT / "src").glob("**/*"):
        if path.is_file() and path.suffix in tracked_extensions:
            content = path.read_text(encoding="utf-8", errors="ignore")
            assert phone not in content, f"Leaked phone in {path}"
            assert email not in content, f"Leaked email in {path}"

    for path in (PROJECT_ROOT / "docs").glob("**/*.md"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert phone not in content, f"Leaked phone in {path}"
        assert email not in content, f"Leaked email in {path}"
