"""Generation of human-readable Change_Summary.md."""

from typing import List, Tuple
from ..ats.scorer import ATSReport
from ..content.manifest import ResumeContentManifest
from ..jd_analysis.models import JobDescription, RequirementMatrix
from ..profile.models import ProjectItem


def generate_change_summary(
    manifest: ResumeContentManifest,
    jd: JobDescription,
    req_matrix: RequirementMatrix,
    ats_report: ATSReport,
    selected_projects: List[ProjectItem],
    scored_pool: List[Tuple[ProjectItem, float]],
) -> str:
    """Creates a markdown document detailing all tailoring decisions."""
    lines = [
        f"# ATS Tailoring & Change Summary — {manifest.target_company} ({manifest.target_role})",
        "",
        f"- **Candidate:** {manifest.personal_info.full_name}",
        f"- **Date:** {manifest.created_at}",
        f"- **Model Used:** {manifest.model_used}",
        f"- **Estimated ATS Readiness Score:** {ats_report.overall_score} / 100",
        "",
        "## 1. Professional Alignment & Headline",
        f"- **Tailored Headline:** `{manifest.headline}`",
        f"- **Tailored Summary:** {manifest.summary}",
        "",
        "## 2. Project Selection Rationale (4-Project Rule)",
        "Permanent Rule: Bearing Fault Detection is strictly fixed at position 2.",
        "",
        "| Slot | Position | Project Title | Selection Type |",
        "|---|---|---|---|",
    ]

    for idx, p in enumerate(manifest.projects, 1):
        rule_desc = "PERMANENT RULE (Fixed Slot 2)" if idx == 2 else f"Dynamic Slot (Ranked #{1 if idx==1 else idx-1})"
        lines.append(f"| #{idx} | {p.id} | {p.title} | {rule_desc} |")

    lines.extend([
        "",
        "### Project Pool Scoring Heuristics:",
        "",
    ])
    for p, score in scored_pool:
        lines.append(f"- **{p.title}**: Relevance Score `{score:.1f}/100`")

    lines.extend([
        "",
        "## 3. JD Requirement Coverage Matrix",
        f"- **Match Percentage:** {req_matrix.match_percentage}%",
        f"- **Strong Matches ({req_matrix.strong_match_count}):** Supported directly by candidate profile.",
        f"- **Partial Matches ({req_matrix.partial_match_count}):** Supported by related project work.",
        f"- **Missing ({req_matrix.missing_count}):** Genuine skills required by JD that candidate does not claim.",
        f"- **Unsupported ({req_matrix.unsupported_count}):** Excluded truthfully to prevent false claims.",
        "",
        "### Must-Have Skills Matched:",
    ])
    for s in ats_report.matched_must_have:
        lines.append(f"- [x] **{s}**")

    if ats_report.missing_must_have:
        lines.extend([
            "",
            "### Missing Must-Have Skills (Truthfully Omitted):",
        ])
        for s in ats_report.missing_must_have:
            lines.append(f"- [ ] {s}")

    lines.extend([
        "",
        "## 4. ATS Validation Summary",
        f"- **Format Compatibility:** {ats_report.format_score}/30",
        f"- **JD Relevance:** {ats_report.relevance_score}/50",
        f"- **Content Quality:** {ats_report.quality_score}/20",
        "",
        "### Tailoring Decisions & Notes:",
    ])
    for note in manifest.tailoring_notes:
        lines.append(f"- {note}")

    return "\n".join(lines) + "\n"
