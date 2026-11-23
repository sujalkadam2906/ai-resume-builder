"""PDF text and link extraction with scanned-PDF detection."""

from pathlib import Path
from typing import Any, Dict, List
import pypdf
import pdfplumber


class ScannedPDFError(Exception):
    """Raised when a PDF contains no selectable text (scanned or image-only)."""
    pass


def extract_from_pdf(pdf_path: Path) -> Dict[str, Any]:
    """
    Extract text, metadata, page count, and embedded hyperlinks from a PDF.
    Raises ScannedPDFError if the PDF is scanned or image-only.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    links: List[Dict[str, str]] = []
    text_content = ""
    pages_text: List[str] = []

    # 1. Extract text and annotations using pypdf
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as e:
                raise PermissionError(f"PDF is password protected: {pdf_path}") from e

        page_count = len(reader.pages)
        for idx, page in enumerate(reader.pages):
            p_text = page.extract_text() or ""
            pages_text.append(p_text)
            text_content += p_text + "\n"

            # Extract link annotations
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    obj = annot.get_object()
                    if "/A" in obj and "/URI" in obj["/A"]:
                        uri = str(obj["/A"]["/URI"])
                        links.append({"page": str(idx + 1), "uri": uri})

    except Exception as e:
        if isinstance(e, (PermissionError, ScannedPDFError)):
            raise
        raise RuntimeError(f"Failed to read PDF with pypdf: {pdf_path}. Details: {e}") from e

    # Fallback to pdfplumber if pypdf extracted very little
    if len(text_content.strip()) < 100:
        try:
            with pdfplumber.open(str(pdf_path)) as plumber_pdf:
                plumber_texts = []
                for p in plumber_pdf.pages:
                    pt = p.extract_text() or ""
                    plumber_texts.append(pt)
                plumber_full = "\n".join(plumber_texts)
                if len(plumber_full.strip()) > len(text_content.strip()):
                    text_content = plumber_full
                    pages_text = plumber_texts
        except Exception:
            pass

    # Check for scanned or image-only PDF
    if len(text_content.strip()) < 50:
        raise ScannedPDFError(
            f"The PDF file '{pdf_path.name}' appears to be scanned or image-only "
            f"(extracted text is {len(text_content.strip())} characters). "
            "A text-based PDF or DOCX file is required for accurate extraction."
        )

    return {
        "file_name": pdf_path.name,
        "file_path": str(pdf_path),
        "page_count": page_count,
        "text": text_content,
        "pages_text": pages_text,
        "links": links,
    }
