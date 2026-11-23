"""Extraction package exports."""

from pathlib import Path
from typing import Any, Dict
from .discovery import find_resume_files, validate_discovered_files
from .pdf_extractor import extract_from_pdf, ScannedPDFError
from .docx_extractor import extract_from_docx
from .txt_extractor import extract_from_txt


def extract_resume(file_path: Path) -> Dict[str, Any]:
    """Extract content from any supported file type (.pdf, .docx, .txt)."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_from_pdf(file_path)
    elif suffix == ".docx":
        return extract_from_docx(file_path)
    elif suffix in (".txt", ".md"):
        return extract_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Supported: .pdf, .docx, .txt")


__all__ = [
    "find_resume_files",
    "validate_discovered_files",
    "extract_from_pdf",
    "extract_from_docx",
    "extract_from_txt",
    "extract_resume",
    "ScannedPDFError",
]
