"""Plain text extraction from text files."""

from pathlib import Path
from typing import Any, Dict


def extract_from_txt(txt_path: Path) -> Dict[str, Any]:
    """Extract text from a plain text file."""
    if not txt_path.exists():
        raise FileNotFoundError(f"File not found: {txt_path}")

    with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    return {
        "file_name": txt_path.name,
        "file_path": str(txt_path),
        "page_count": 1,
        "text": text,
        "links": [],
    }
