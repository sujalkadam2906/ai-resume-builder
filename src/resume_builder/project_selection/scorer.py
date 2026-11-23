"""Project scoring engine based on weighted relevance heuristics."""

from typing import Dict, List, Set
from ..jd_analysis.keywords import normalize_term
from ..jd_analysis.models import JobDescription
from ..profile.models import ProjectItem


def compute_project_score(
    project: ProjectItem,
    jd: JobDescription,
    weights: Dict[str, float],
) -> float:
    """
    Score a project against a target JD using four weighted heuristics:
    - Required JD skills coverage (45%)
    - Responsibilities alignment (25%)
    - Tech stack similarity (20%)
    - Domain/role category relevance (10%)
    Returns a score between 0.0 and 100.0.
    """
    w_skills = weights.get("required_skills_coverage", 0.45)
    w_resp = weights.get("responsibilities_alignment", 0.25)
    w_tech = weights.get("tech_stack_similarity", 0.20)
    w_domain = weights.get("domain_relevance", 0.10)

    proj_skills_norm = {normalize_term(s) for s in project.skills}
    jd_skills_norm = {normalize_term(s) for s in jd.required_skills + jd.preferred_skills}

    # 1. Required skills coverage (0 to 100)
    matched_skills = proj_skills_norm.intersection(jd_skills_norm)
    if jd_skills_norm:
        skills_score = (len(matched_skills) / len(jd_skills_norm)) * 100.0
    else:
        skills_score = 50.0

    # 2. Responsibilities alignment (0 to 100)
    resp_matches = 0
    jd_resp_text = " ".join(jd.responsibilities).lower()
    for bullet in project.bullets:
        bullet_words = set(bullet.lower().split())
        if any(word in jd_resp_text for word in bullet_words if len(word) > 4):
            resp_matches += 1
    resp_score = (resp_matches / max(len(project.bullets), 1)) * 100.0

    # 3. Tech stack similarity (0 to 100)
    # Check languages and frameworks alignment
    tech_matches = 0
    all_jd_tech = {normalize_term(t) for t in jd.programming_languages + jd.frameworks_and_libraries + jd.databases + jd.tools}
    if all_jd_tech:
        tech_matches = len(proj_skills_norm.intersection(all_jd_tech))
        tech_score = (tech_matches / len(all_jd_tech)) * 100.0
    else:
        tech_score = 50.0

    # 4. Domain / role category relevance (0 to 100)
    domain_score = 40.0
    title_lower = jd.job_title.lower()
    for cat in project.categories:
        cat_lower = cat.lower()
        if cat_lower in title_lower or any(cat_lower in resp.lower() for resp in jd.responsibilities):
            domain_score = 90.0
            break

    total = (
        skills_score * w_skills
        + resp_score * w_resp
        + tech_score * w_tech
        + domain_score * w_domain
    )

    return round(total, 2)
