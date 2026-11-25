"""Text cleaning and formatting utility functions."""

import html
import re
from typing import List, Optional


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


def escape_xml_attr(text: str) -> str:
    """Escape text for XML attribute values (e.g. href inside ReportLab <a> tags)."""
    if not text:
        return ""
    return html.escape(text, quote=True)


def normalize_url(
    url: Optional[str],
    default_domain: Optional[str] = None,
    fallback: Optional[str] = None,
) -> str:
    """Normalize a web URL to ensure valid absolute https:// formatting for PDF/DOCX hyperlinks."""
    target = (url or "").strip()
    if not target and fallback:
        target = fallback.strip()
    if not target:
        if default_domain:
            return f"https://{default_domain}"
        return ""

    # Don't touch email or tel schemes
    if target.startswith("mailto:") or target.startswith("tel:"):
        return target

    # Strip surrounding quotes or angle brackets
    target = target.strip("<>'\"")

    # Protocol-relative URLs
    if target.startswith("//"):
        return f"https:{target}"

    # Already has scheme
    if target.startswith("http://") or target.startswith("https://"):
        return target

    # Bare username e.g. "sujalkadam2906" with default_domain "github.com"
    if "/" not in target and "." not in target and default_domain:
        target = f"{default_domain}/{target}"

    return f"https://{target}"


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
