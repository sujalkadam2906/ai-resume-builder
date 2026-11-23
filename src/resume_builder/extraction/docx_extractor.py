"""DOCX text and hyperlink extraction."""

from pathlib import Path
from typing import Any, Dict, List
import docx


def extract_from_docx(docx_path: Path) -> Dict[str, Any]:
    """Extract text, paragraphs, tables, and hyperlinks from a DOCX file."""
    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    try:
        doc = docx.Document(str(docx_path))
    except Exception as e:
        raise RuntimeError(f"Failed to read DOCX {docx_path}: {e}") from e

    paragraphs_text = []
    links: List[Dict[str, str]] = []

    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs_text.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_texts:
                paragraphs_text.append(" | ".join(row_texts))

    full_text = "\n".join(paragraphs_text)

    # Extract hyperlinks from XML relationships
    try:
        for rel in doc.part.rels.values():
            if "hyperlink" in rel.reltype:
                links.append({"uri": rel.target_ref})
    except Exception:
        pass

    return {
        "file_name": docx_path.name,
        "file_path": str(docx_path),
        "page_count": 1,  # DOCX doesn't store explicit page count until rendered
        "text": full_text,
        "paragraphs": paragraphs_text,
        "links": links,
    }
