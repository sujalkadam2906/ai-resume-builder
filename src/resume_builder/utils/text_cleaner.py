"""Text cleaning and formatting utility functions."""

import html
import re
from typing import List


def clean_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    if not text:
        return ""
    # Normalize unicode spaces and hyphens
    text = text.replace('\u200b', '').replace('\ufeff', '')
    text = text.replace('—', ' — ').replace('–', ' - ')
    # Normalize multiple whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def escape_xml(text: str) -> str:
    """Escape text for XML-based flowables (e.g. ReportLab Paragraphs)."""
    if not text:
        return ""
    return html.escape(text, quote=False)


def clean_bullets(bullets: List[str]) -> List[str]:
    """Clean and normalize bullet points."""
    cleaned = []
    for b in bullets:
        b_clean = clean_text(b)
        # Strip leading bullet symbols if present
        b_clean = re.sub(r'^[\s•\-\*\u2022\u25cf\u25cb]+\s*', '', b_clean)
        if b_clean:
            cleaned.append(b_clean)
    return cleaned
