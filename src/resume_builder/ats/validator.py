"""Inspection and validation of the ACTUAL generated PDF document with profile-specific rules."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pypdf
import pdfplumber

from ..jd_analysis.keywords import normalize_term
from ..jd_analysis.models import JobDescription, RequirementMatrix
from ..profile.models import ProfileConfig
from .rules import STANDARD_HEADINGS

KNOWN_PROJECT_KEYWORDS = [
    "SpringNotes",
    "Opportunity Radar",
    "Employee Management",
    "Online Bookstore",
    "Bearing Fault",
    "Vogue Vault",
    "CloudCanvas",
    "CryptoPulse",
    "FormForge",
    "PortfolioForge",
]


class DocumentInspectionResult:
    """Carries deterministic inspection results from the rendered PDF."""

    def __init__(self):
        self.is_text_selectable: bool = False
        self.extracted_text: str = ""
        self.extracted_char_count: int = 0
        self.page_count: int = 0
        self.headings_found: List[str] = []
        self.missing_headings: List[str] = []
        self.has_contact_in_body: bool = False
        self.bearing_fault_position_ok: bool = False
        self.detected_project_count: int = 0
        self.critical_issues: List[str] = []
        self.warnings: List[str] = []


def inspect_generated_pdf(
    pdf_path: Path,
    expected_projects_count: int = 4,
    profile_config: Optional[ProfileConfig] = None,
) -> DocumentInspectionResult:
    """
    Extracts text from the generated PDF and performs structural compliance checks:
    - Text selectability
    - Actual page count
    - Standard headings presence
    - Contact details presence in document body
    - Candidate-specific project rules
    """
    res = DocumentInspectionResult()

    if not pdf_path.exists():
        res.critical_issues.append(f"Generated PDF file does not exist: {pdf_path}")
        return res

    # 1. Page count and text extraction via pypdf
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        res.page_count = len(reader.pages)
        if res.page_count != 1:
            res.critical_issues.append(
                f"Page count violation: Document is {res.page_count} page(s), must be exactly 1 page."
            )

        extracted_parts = []
        for p in reader.pages:
            t = p.extract_text() or ""
            extracted_parts.append(t)
        res.extracted_text = "\n".join(extracted_parts)
        res.extracted_char_count = len(res.extracted_text.strip())
    except Exception as e:
        res.critical_issues.append(f"Failed to read PDF pages: {e}")
        return res

    # 2. Text selectability check
    if res.extracted_char_count > 300:
        res.is_text_selectable = True
    else:
        res.critical_issues.append("PDF text is not selectable or character count is abnormally low.")

    # 3. Standard Headings check
    text_upper = res.extracted_text.upper()
    for h in STANDARD_HEADINGS:
        if h in text_upper:
            res.headings_found.append(h)
        else:
            first_word = h.split()[0]
            if first_word in text_upper:
                res.headings_found.append(h)
            else:
                res.missing_headings.append(h)

    # 4. Contact in body
    if "@" in res.extracted_text and ("+" in res.extracted_text or any(c.isdigit() for c in res.extracted_text)):
        res.has_contact_in_body = True
    else:
        res.warnings.append("Contact information (phone/email) not detected cleanly in body text.")

    # 5. Fixed project rule check
    has_fixed = profile_config.project_selection.has_fixed_project if profile_config else True
    if has_fixed:
        fx_rule = profile_config.project_selection.fixed_project if profile_config else None
        fx_id = fx_rule.id.lower() if fx_rule else "bearing"
        fx_pos = fx_rule.position if fx_rule else 2

        projects_text = ""
        if "PROJECTS" in text_upper:
            after_proj = res.extracted_text[text_upper.find("PROJECTS"):]
            end_idx = len(after_proj)
            for stop_heading in ["PROFESSIONAL DEVELOPMENT", "LEADERSHIP", "EDUCATION", "CERTIFICATIONS"]:
                pos = after_proj.upper().find(stop_heading)
                if pos != -1 and pos < end_idx:
                    end_idx = pos
            projects_text = after_proj[:end_idx]

        detected_projects = []
        for line in projects_text.split("\n"):
            line_clean = line.strip()
            if any(kw.lower() in line_clean.lower() for kw in KNOWN_PROJECT_KEYWORDS):
                detected_projects.append(line_clean)

        res.detected_project_count = len(detected_projects)
        if len(detected_projects) >= fx_pos:
            target_proj_line = detected_projects[fx_pos - 1].lower()
            if fx_id in target_proj_line or "bearing" in target_proj_line:
                res.bearing_fault_position_ok = True
            else:
                res.critical_issues.append(
                    f"Fixed project rule violated in rendered text! Slot {fx_pos} is: '{detected_projects[fx_pos - 1]}'"
                )
        elif "bearing" in projects_text.lower():
            res.bearing_fault_position_ok = True
    else:
        # Dynamic project selection - no fixed project required
        res.bearing_fault_position_ok = True

    # 6. Prohibited Term Validation
    prohibited_terms = profile_config.prohibited_terms if profile_config else ["mechanical engineering", "mechanical engineer"]
    lower_text = res.extracted_text.lower()
    for term in prohibited_terms:
        if term.lower() in lower_text:
            res.critical_issues.append(f"Prohibited term '{term}' detected in resume body!")

    # 7. Permanent Headline Validation
    if profile_config and profile_config.headline_rule.mode == "permanent":
        target_hl = profile_config.headline_rule.permanent_headline
        if target_hl and target_hl.lower() not in lower_text:
            first_segment = target_hl.split("|")[0].strip().lower()
            if first_segment not in lower_text and "entry-level" not in lower_text:
                res.critical_issues.append("Permanent candidate headline was altered or missing!")
    elif profile_config is None:
        permanent_headline = "Entry-Level Software Engineer | Full Stack Developer | ML Research Paper Publisher"
        if permanent_headline.lower() not in lower_text:
            if "entry-level" not in lower_text and "software engineer" not in lower_text:
                res.critical_issues.append("Permanent candidate headline was altered or missing!")

    # 8. Correct Employee Management Repository Link Check (only for Sujal)
    if profile_config is None or profile_config.profile_id == "sujal":
        if "employee-management-rest-api" in lower_text:
            res.critical_issues.append("Outdated employee repository link 'employee-management-rest-api' detected! Must use 'employee-management-springboot'.")

    return res
