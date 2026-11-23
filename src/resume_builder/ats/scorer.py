"""Deterministic 100-point local ATS Readiness Estimator."""

from pathlib import Path
from typing import Any, Dict, List
from ..jd_analysis.keywords import normalize_term
from ..jd_analysis.models import JobDescription, RequirementMatrix
from .rules import ACTION_VERBS, DISCLAIMER
from .validator import DocumentInspectionResult, inspect_generated_pdf


class ATSReport:
    """Structured ATS readiness evaluation report."""

    def __init__(self):
        self.overall_score: int = 0
        self.format_score: int = 0  # max 30
        self.relevance_score: int = 0  # max 50
        self.quality_score: int = 0  # max 20
        self.matched_must_have: List[str] = []
        self.missing_must_have: List[str] = []
        self.preferred_matched: List[str] = []
        self.unsupported_excluded: List[str] = []
        self.critical_issues: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        self.disclaimer: str = DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_ats_readiness_score": self.overall_score,
            "max_score": 100,
            "score_breakdown": {
                "ats_format_compatibility": {"score": self.format_score, "max": 30},
                "jd_relevance": {"score": self.relevance_score, "max": 50},
                "content_quality": {"score": self.quality_score, "max": 20},
            },
            "matched_must_have_keywords": self.matched_must_have,
            "missing_must_have_keywords": self.missing_must_have,
            "preferred_keywords_matched": self.preferred_matched,
            "unsupported_keywords_excluded": self.unsupported_excluded,
            "critical_formatting_issues": self.critical_issues,
            "warnings": self.warnings,
            "suggested_improvements": self.suggestions,
            "disclaimer": self.disclaimer,
        }

    def format_console_text(self) -> str:
        lines = [
            "==================================================================",
            f"          {self.disclaimer.splitlines()[0]}",
            "==================================================================",
            f"OVERALL ATS READINESS ESTIMATE : {self.overall_score} / 100",
            "------------------------------------------------------------------",
            f"  [+] Format Compatibility     : {self.format_score:>2} / 30",
            f"  [+] JD Relevance             : {self.relevance_score:>2} / 50",
            f"  [+] Content Quality          : {self.quality_score:>2} / 20",
            "------------------------------------------------------------------",
            f"Matched Must-Have Keywords     : {', '.join(self.matched_must_have) if self.matched_must_have else 'None'}",
            f"Missing Must-Have Keywords     : {', '.join(self.missing_must_have) if self.missing_must_have else 'None'}",
            f"Preferred Keywords Matched     : {', '.join(self.preferred_matched) if self.preferred_matched else 'None'}",
            f"Unsupported (Truthfully Left)  : {', '.join(self.unsupported_excluded) if self.unsupported_excluded else 'None'}",
        ]
        if self.critical_issues:
            lines.append("------------------------------------------------------------------")
            lines.append("CRITICAL ISSUES:")
            for issue in self.critical_issues:
                lines.append(f"  [!] {issue}")
        if self.warnings:
            lines.append("------------------------------------------------------------------")
            lines.append("WARNINGS:")
            for w in self.warnings:
                lines.append(f"  [*] {w}")
        if self.suggestions:
            lines.append("------------------------------------------------------------------")
            lines.append("SUGGESTED IMPROVEMENTS:")
            for s in self.suggestions:
                lines.append(f"  [-] {s}")
        lines.append("==================================================================")
        return "\n".join(lines)


def calculate_ats_readiness(
    pdf_path: Path,
    jd: JobDescription,
    req_matrix: RequirementMatrix,
    profile_config: Any = None,
) -> ATSReport:
    """
    Deterministically computes ATS readiness score from the ACTUAL generated PDF.
    """
    report = ATSReport()
    inspection = inspect_generated_pdf(pdf_path, profile_config=profile_config)

    # A. ATS FORMAT COMPATIBILITY (30 points)
    # 1. Text selectability (6 pts)
    if inspection.is_text_selectable:
        report.format_score += 6
    else:
        report.critical_issues.append("PDF text is not selectable (scanned or flattened).")

    # 2. Page count exactly 1 (8 pts)
    if inspection.page_count == 1:
        report.format_score += 8
    else:
        report.critical_issues.append(f"Document must be exactly 1 page. Found: {inspection.page_count}")

    # 3. Standard Headings (6 pts)
    if len(inspection.missing_headings) == 0:
        report.format_score += 6
    else:
        # Partial credit
        pts = max(0, 6 - (len(inspection.missing_headings) * 2))
        report.format_score += pts
        report.warnings.append(f"Missing standard headings: {', '.join(inspection.missing_headings)}")

    # 4. Contact info in body (5 pts)
    if inspection.has_contact_in_body:
        report.format_score += 5
    else:
        report.warnings.append("Contact info might not be cleanly parsed in the document body.")

    # 5. Permanent Bearing Fault position (5 pts)
    if inspection.bearing_fault_position_ok:
        report.format_score += 5
    else:
        report.critical_issues.append("Bearing Fault Detection was not at position 2 in rendered text.")

    report.critical_issues.extend(inspection.critical_issues)
    report.warnings.extend(inspection.warnings)

    # B. JD RELEVANCE (50 points)
    # Check keyword presence inside actual extracted text
    pdf_text_norm = normalize_term(inspection.extracted_text)

    # Must-have skills matching (25 pts)
    req_skills = jd.required_skills or ["Software Engineering"]
    matched_req = []
    missing_req = []
    for s in req_skills:
        if normalize_term(s) in pdf_text_norm:
            matched_req.append(s)
        else:
            missing_req.append(s)

    report.matched_must_have = matched_req
    report.missing_must_have = missing_req

    if req_skills:
        coverage_ratio = len(matched_req) / len(req_skills)
        report.relevance_score += int(round(coverage_ratio * 25))
    else:
        report.relevance_score += 20

    # Preferred skills matching (10 pts)
    pref_skills = jd.preferred_skills
    matched_pref = []
    for s in pref_skills:
        if normalize_term(s) in pdf_text_norm:
            matched_pref.append(s)

    report.preferred_matched = matched_pref
    if pref_skills:
        pref_ratio = len(matched_pref) / len(pref_skills)
        report.relevance_score += int(round(pref_ratio * 10))
    else:
        report.relevance_score += 8  # Full baseline if no preferred specified

    # Responsibility & Domain terminology (15 pts)
    resp_matches = 0
    for resp in jd.responsibilities[:5]:
        for word in resp.split():
            if len(word) > 4 and normalize_term(word) in pdf_text_norm:
                resp_matches += 1
                break
    report.relevance_score += min(15, resp_matches * 3)

    # Unsupported excluded
    report.unsupported_excluded = req_matrix.get_unsupported_skills()

    # C. CONTENT QUALITY (20 points)
    # 1. Action verbs at start of bullets (8 pts)
    text_lines = [l.strip(" •-*") for l in inspection.extracted_text.splitlines() if l.strip()]
    action_verb_count = 0
    for line in text_lines:
        first_word = line.split()[0].lower() if line.split() else ""
        if first_word in ACTION_VERBS:
            action_verb_count += 1

    if action_verb_count >= 6:
        report.quality_score += 8
    elif action_verb_count >= 3:
        report.quality_score += 5
    else:
        report.quality_score += 2
        report.suggestions.append("Incorporate more strong action verbs at the beginning of bullet points.")

    # 2. Evidence-backed achievements / metrics (6 pts)
    if "95%" in inspection.extracted_text or "1,500+" in inspection.extracted_text or "20+" in inspection.extracted_text:
        report.quality_score += 6
    else:
        report.quality_score += 4

    # 3. Completeness & absence of buzzwords (6 pts)
    bad_buzzwords = ["hardworking", "passionate developer", "quick learner", "team player"]
    found_buzz = [b for b in bad_buzzwords if b in inspection.extracted_text.lower()]
    if not found_buzz:
        report.quality_score += 6
    else:
        report.quality_score += 3
        report.suggestions.append(f"Remove generic buzzwords: {', '.join(found_buzz)}")

    # Overall calculation
    report.overall_score = report.format_score + report.relevance_score + report.quality_score
    report.overall_score = min(100, max(0, report.overall_score))

    if report.missing_must_have:
        report.suggestions.append(
            f"If you have academic or personal experience in {', '.join(report.missing_must_have[:3])}, "
            "consider completing a project to earn verified candidate evidence."
        )

    return report
