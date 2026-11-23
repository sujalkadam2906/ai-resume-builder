"""Unit tests for file discovery and text extraction."""

from pathlib import Path
import pytest
from resume_builder.config import PROJECT_ROOT
from resume_builder.extraction.discovery import find_resume_files, validate_discovered_files
from resume_builder.extraction.pdf_extractor import extract_from_pdf, ScannedPDFError


def test_discovery_finds_both_resumes():
    found = find_resume_files(PROJECT_ROOT)
    assert found.get("r1") is not None, "Failed to discover Sujal_Kadam_Resume"
    assert found.get("r2") is not None, "Failed to discover Sujal_Kadam_Resume_new"
    r1, r2 = validate_discovered_files(found)
    assert r1.exists()
    assert r2.exists()


def test_extract_from_pdf_success():
    found = find_resume_files(PROJECT_ROOT)
    r1_path = found["r1"]
    data = extract_from_pdf(r1_path)
    assert len(data["text"]) > 500
    assert "SUJAL KADAM" in data["text"]
    assert len(data["links"]) > 0


def test_scanned_pdf_error(tmp_path):
    # Create empty PDF file
    from reportlab.pdfgen import canvas
    empty_pdf = tmp_path / "scanned_sim.pdf"
    c = canvas.Canvas(str(empty_pdf))
    c.drawString(100, 100, "Hi")  # very short text, < 50 chars
    c.save()

    with pytest.raises(ScannedPDFError):
        extract_from_pdf(empty_pdf)
