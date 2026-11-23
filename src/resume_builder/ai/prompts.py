"""Prompts with strict anti-hallucination and truthfulness constraints for Gemini."""

from typing import Any, Dict, List
from ..jd_analysis.models import JobDescription, RequirementMatrix
from ..profile.models import MasterProfile, ProjectItem


SYSTEM_PROMPT = """You are a senior ATS Resume Optimization Specialist and Technical Resume Writer.
Your task is to tailor verified resume content for the candidate for a specific Job Description (JD).

CRITICAL NON-NEGOTIABLE CONSTRAINTS:
1. TRUTHFULNESS & FACTUAL INTEGRITY:
   - NEVER invent technologies, tools, or skills the candidate does not have.
   - NEVER fabricate metrics, numbers, percentages, team sizes, revenue, or user counts.
   - Only state metrics if they appear in the verified project evidence.
   - If a technology requested by the JD is unsupported or missing, DO NOT add it.
   - NEVER mention prohibited terms or degree branches not explicitly provided in candidate records.
2. PROFESSIONAL IDENTITY:
   - Use the candidate's verified headline and summary.
   - Do NOT replace with unverified JD-specific job titles.
3. PROJECT SELECTION & ORDER:
   - You are provided exactly 4 selected projects.
   - You MUST keep all 4 projects in the EXACT order provided.
4. BULLET POINT ARCHITECTURE:
   - Each project bullet must follow: Strong Action Verb + Technical Implementation + Purpose / Technical Outcome.
   - Keep 2 concise, impactful bullets per project.
   - Avoid generic buzzwords ('quick learner', 'passionate individual', 'hardworking developer').
5. PROFESSIONAL SUMMARY:
   - 2 to 3 lines highlighting full-stack projects, core technologies, and verified leadership metrics.
"""


def build_tailoring_user_prompt(
    profile: MasterProfile,
    selected_projects: List[ProjectItem],
    jd: JobDescription,
    req_matrix: RequirementMatrix,
) -> str:
    """Build user prompt containing only verified candidate evidence and JD details."""
    # Redact personal contact information and prohibited branch terms
    edu_summaries = [f"{e.degree}, {e.institution}, {e.cgpa}" for e in profile.education]
    candidate_profile_snippet = {
        "candidate": profile.personal_info.full_name,
        "education": "; ".join(edu_summaries) if edu_summaries else "Degree",
        "verified_skills": profile.technical_skills.model_dump(),
        "verified_leadership": [l.description for l in profile.leadership_and_experience],
        "verified_certifications": profile.certifications,
    }

    projects_snippet = []
    for idx, p in enumerate(selected_projects, 1):
        projects_snippet.append({
            "position": idx,
            "id": p.id,
            "title": p.title,
            "subtitle": p.subtitle,
            "verified_bullets": p.bullets,
            "verified_metrics": p.metrics,
            "is_fixed_at_pos_2": (idx == 2),
        })

    prompt = f"""TARGET JOB DESCRIPTION:
Company: {jd.company_name}
Target Role: {jd.job_title}

Required Skills: {', '.join(jd.required_skills) if jd.required_skills else 'Software Engineering Fundamentals'}
Preferred Skills: {', '.join(jd.preferred_skills) if jd.preferred_skills else 'None specified'}
Key Responsibilities:
{chr(10).join('- ' + r for r in jd.responsibilities)}

CANDIDATE VERIFIED EVIDENCE (DO NOT EXCEED THIS TRUTHFUL BOUNDARY):
{candidate_profile_snippet}

SELECTED PROJECTS (MUST RETAIN ORDER AND IDS EXACTLY):
{projects_snippet}

JD REQUIREMENT MATRIX HIGHLIGHTS:
- Supported Must-Haves: {', '.join(req_matrix.get_matched_must_have())}
- Missing / Unsupported (MUST EXCLUDE): {', '.join(req_matrix.get_missing_must_have() + req_matrix.get_unsupported_skills())}

INSTRUCTIONS:
Generate the tailored resume content conforming to TailoredResumeContent schema.
Ensure Bearing Fault Diagnosis is strictly at position 2 in tailored_projects.
Do not fabricate any numbers or skills.
"""
    return prompt
