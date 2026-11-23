"""Resume content manifest generator supporting profile-specific rules, headline/summary rules, and decoupled privacy."""

from datetime import datetime
from typing import Dict, List, Optional
from ..ai.structured_schemas import TailoredResumeContent
from ..jd_analysis.models import JobDescription
from ..profile.models import EducationItem, MasterProfile, ProfileConfig, ProjectItem
from .manifest import ManifestProject, ResumeContentManifest

PERMANENT_HEADLINE = "Entry-Level Software Engineer | Full Stack Developer | ML Research Paper Publisher"
PERMANENT_SUMMARY = (
    "Developed full-stack projects using Java/Spring Boot and React/TypeScript, "
    "alongside PostgreSQL analytics and Python-based machine learning and Gemini-powered automation. "
    "Coordinated campus placement operations for 1,500+ students across 20+ recruitment drives. "
    "B.Tech graduate (2026, CGPA: 8.23/10); immediate joiner and open to relocation."
)


def validate_no_prohibited_terms(text: str, prohibited_terms: Optional[List[str]] = None, context: str = "") -> None:
    """Enforces strict candidate privacy rules: prohibited terms must never appear."""
    if prohibited_terms is None:
        prohibited = ["mechanical engineering", "mechanical engineer"]
    else:
        prohibited = [t.lower() for t in prohibited_terms if t]

    lower = text.lower()
    for term in prohibited:
        if term in lower:
            raise ValueError(f"Prohibited term '{term}' detected in {context}! Candidate rule strictly forbids this.")


def build_resume_manifest(
    profile: MasterProfile,
    selected_projects: List[ProjectItem],
    tailored_ai: TailoredResumeContent,
    jd: JobDescription,
    model_used: str,
    profile_config: Optional[ProfileConfig] = None,
) -> ResumeContentManifest:
    """
    Assemble verified Master Profile data, AI tailored summaries/bullets,
    and target JD context into a validated ResumeContentManifest.
    Respects profile-specific configuration for headline, summary, and prohibited terms.
    """
    # 1. Map projects and attach verified hyperlinks
    manifest_projects: List[ManifestProject] = []
    ai_project_map = {tp.project_id: tp for tp in tailored_ai.tailored_projects}

    fixed_rule = (
        profile_config.project_selection.fixed_project
        if profile_config and profile_config.project_selection.has_fixed_project
        else None
    )
    fixed_pos = fixed_rule.position if fixed_rule else 2

    for idx, orig_proj in enumerate(selected_projects, 1):
        # Look up AI-tailored bullets if available and truthful
        bullets = orig_proj.bullets
        if orig_proj.id in ai_project_map:
            ai_bullets = ai_project_map[orig_proj.id].bullets
            if ai_bullets and len(ai_bullets) >= 1:
                bullets = ai_bullets

        # Collect hyperlinks
        links_dict_list = [{"label": link.label, "url": link.url} for link in orig_proj.links]

        is_fixed = False
        if fixed_rule and (idx == fixed_pos):
            is_fixed = True
        elif not profile_config and (idx == 2):
            is_fixed = True

        manifest_projects.append(
            ManifestProject(
                id=orig_proj.id,
                title=orig_proj.title,
                subtitle=orig_proj.subtitle,
                is_fixed=is_fixed,
                bullets=bullets,
                links=links_dict_list,
            )
        )

    # 2. Build ordered skills dictionary - Include non-empty categories
    ordered_skills_dict = {}
    category_mappings = [
        ("Languages", profile.technical_skills.languages),
        ("Backend & Java", profile.technical_skills.backend_and_java),
        ("Databases & SQL", profile.technical_skills.databases_and_sql),
        ("Cloud, DevOps & Deployment", profile.technical_skills.cloud_devops_and_deployment),
        ("Frontend", profile.technical_skills.frontend),
        ("Core CS & ML", profile.technical_skills.core_cs_and_ml),
        ("Testing & Tools", profile.technical_skills.testing_and_tools),
    ]
    for cat_name, cat_skills in category_mappings:
        if cat_skills:
            ordered_skills_dict[cat_name] = cat_skills

    # 3. Clean education - Respect candidate's degree and prohibited terms
    prohibited_list = (
        profile_config.prohibited_terms
        if profile_config is not None
        else ["mechanical engineering", "mechanical engineer"]
    )

    cleaned_education = []
    for edu in profile.education:
        degree_clean = edu.degree
        for p_term in prohibited_list:
            degree_clean = degree_clean.replace(f"in {p_term.title()}", "").replace(p_term.title(), "").replace(f"in {p_term}", "").replace(p_term, "").strip()
        if not degree_clean:
            degree_clean = "B.Tech"
        cgpa_str = edu.cgpa if "/" in edu.cgpa else f"{edu.cgpa}/10"
        cleaned_education.append(
            EducationItem(
                degree=degree_clean,
                institution=edu.institution,
                duration=edu.duration,
                start_year=edu.start_year,
                end_year=edu.end_year,
                cgpa=cgpa_str,
                score=edu.score,
                scale=edu.scale,
                source=edu.source,
            )
        )

    # 4. Resolve headline and summary based on profile rules
    if profile_config and profile_config.headline_rule.mode == "permanent" and profile_config.headline_rule.permanent_headline:
        final_headline = profile_config.headline_rule.permanent_headline
    elif tailored_ai.professional_headline:
        final_headline = tailored_ai.professional_headline
    elif profile.headlines:
        final_headline = profile.headlines[0]
    else:
        final_headline = PERMANENT_HEADLINE

    if profile_config and profile_config.summary_rule.mode == "permanent" and profile_config.summary_rule.permanent_summary:
        final_summary = profile_config.summary_rule.permanent_summary
    elif tailored_ai.professional_summary:
        final_summary = tailored_ai.professional_summary
    elif profile.summaries:
        final_summary = profile.summaries[0]
    else:
        final_summary = PERMANENT_SUMMARY

    # Validate prohibited terms
    validate_no_prohibited_terms(final_headline, prohibited_list, context="Headline")
    validate_no_prohibited_terms(final_summary, prohibited_list, context="Professional Summary")
    for edu in cleaned_education:
        validate_no_prohibited_terms(edu.degree, prohibited_list, context="Education Degree")

    # 5. Visible certifications - Include all candidate certifications
    visible_certifications = list(profile.certifications)

    # 6. Assemble manifest
    return ResumeContentManifest(
        target_company=jd.company_name,
        target_role=jd.job_title,
        model_used=model_used,
        personal_info=profile.personal_info,
        links=profile.links,
        headline=final_headline,
        summary=final_summary,
        ordered_skills=ordered_skills_dict,
        projects=manifest_projects,
        leadership=profile.leadership_and_experience,
        professional_development=profile.professional_development,
        education=cleaned_education,
        achievements=profile.achievements,
        research_publications=profile.research_publications,
        certifications=visible_certifications,
        tailoring_notes=tailored_ai.change_summary_notes,
        created_at=datetime.now().isoformat(),
    )
