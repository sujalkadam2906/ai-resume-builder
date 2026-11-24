"""Converter between PostgreSQL CandidateProfile database models and Python Resume Engine models."""

from typing import Any, Dict, List, Optional, Tuple
from backend.app.models.candidate import CandidateProfile, Project as DBProject
from src.resume_builder.profile.models import (
    AchievementItem,
    EducationItem,
    FixedProjectRule,
    HeadlineRule,
    LeadershipItem,
    LinkItem,
    LinksProfile,
    MasterProfile,
    PersonalInfo,
    ProfessionalDevelopmentItem,
    ProfileConfig,
    ProjectItem,
    ProjectLink,
    ProjectSelectionConfig,
    ResearchPublication,
    SummaryRule,
    TechnicalSkills,
)


def db_candidate_to_engine_profile(
    candidate: CandidateProfile,
) -> Tuple[MasterProfile, List[ProjectItem], ProfileConfig]:
    """Convert SQLAlchemy CandidateProfile into MasterProfile, ProjectItems, and ProfileConfig."""
    # 1. Personal Info
    personal_info = PersonalInfo(
        full_name=candidate.full_name,
        display_name=candidate.display_name or candidate.full_name,
        phone=candidate.phone or "+91 0000000000",
        email=candidate.email or "candidate@example.com",
        location=candidate.location or "India",
        open_to_relocate=candidate.open_to_relocate,
        immediate_joiner=candidate.immediate_joiner,
    )

    # 2. Links
    links_data = candidate.links or {}
    linkedin_raw = links_data.get("linkedin", {})
    github_raw = links_data.get("github", {})
    portfolio_raw = links_data.get("portfolio", {})

    links_profile = LinksProfile(
        linkedin=LinkItem(
            url=linkedin_raw.get("url", "https://linkedin.com"),
            display=linkedin_raw.get("display", "linkedin.com/in/profile"),
        ),
        github=LinkItem(
            url=github_raw.get("url", "https://github.com"),
            display=github_raw.get("display", "github.com/profile"),
        ),
        portfolio=LinkItem(
            url=portfolio_raw.get("url", "https://example.com"),
            display=portfolio_raw.get("display", "portfolio.dev"),
        ),
    )

    # 3. Educations
    educations = [
        EducationItem(
            degree=e.degree,
            institution=e.institution,
            duration=e.duration or f"{e.start_year or 2022} – {e.end_year or 2026}",
            start_year=e.start_year or 2022,
            end_year=e.end_year or 2026,
            cgpa=e.cgpa or (f"{e.score} / {e.scale}" if e.score and e.scale else "8.23 / 10"),
            score=e.score or "8.23",
            scale=e.scale or "10",
            source=e.source or "verified_both",
        )
        for e in candidate.educations
    ]

    # 4. Technical Skills by category
    skills_by_category: Dict[str, List[str]] = {
        "languages": [],
        "backend_and_java": [],
        "databases_and_sql": [],
        "cloud_devops_and_deployment": [],
        "frontend": [],
        "core_cs_and_ml": [],
        "testing_and_tools": [],
    }
    for sk in candidate.skills:
        cat = sk.category.lower().strip()
        if cat in skills_by_category:
            skills_by_category[cat].append(sk.skill_name)
        elif "lang" in cat:
            skills_by_category["languages"].append(sk.skill_name)
        elif "back" in cat or "java" in cat:
            skills_by_category["backend_and_java"].append(sk.skill_name)
        elif "data" in cat or "sql" in cat:
            skills_by_category["databases_and_sql"].append(sk.skill_name)
        elif "cloud" in cat or "devops" in cat or "deploy" in cat:
            skills_by_category["cloud_devops_and_deployment"].append(sk.skill_name)
        elif "front" in cat or "web" in cat:
            skills_by_category["frontend"].append(sk.skill_name)
        elif "ml" in cat or "ai" in cat or "cs" in cat:
            skills_by_category["core_cs_and_ml"].append(sk.skill_name)
        else:
            skills_by_category["testing_and_tools"].append(sk.skill_name)

    tech_skills = TechnicalSkills(
        languages=skills_by_category["languages"],
        backend_and_java=skills_by_category["backend_and_java"],
        databases_and_sql=skills_by_category["databases_and_sql"],
        cloud_devops_and_deployment=skills_by_category["cloud_devops_and_deployment"],
        frontend=skills_by_category["frontend"],
        core_cs_and_ml=skills_by_category["core_cs_and_ml"],
        testing_and_tools=skills_by_category["testing_and_tools"],
    )

    # 5. Leadership & Experience
    experiences = [
        LeadershipItem(
            id=str(exp.id),
            role=exp.role,
            organization=exp.organization,
            duration=exp.duration or "2024 – 2026",
            metrics=exp.metrics,
            description=exp.description or exp.role,
            bullets=exp.bullets or [],
            source=exp.source or "verified_both",
        )
        for exp in candidate.experiences
    ]

    # 6. Professional Development
    prof_devs = [
        ProfessionalDevelopmentItem(
            id=str(pd.id),
            title=pd.title,
            organization=pd.organization,
            date=pd.date,
            bullets=pd.bullets or [],
            source=pd.source or "verified",
            conflict_note=pd.conflict_note,
        )
        for pd in candidate.professional_developments
    ]

    # 7. Achievements
    achievements = [
        AchievementItem(
            id=str(ach.id),
            title=ach.title,
            description=ach.description or ach.title,
            bullets=ach.bullets or [],
            source=ach.source or "verified_both",
        )
        for ach in candidate.achievements
    ]

    # 8. Research Publications from config_rules
    rules = candidate.config_rules or {}
    raw_pubs = rules.get("research_publications", [])
    research_pubs = []
    for pub in raw_pubs:
        if isinstance(pub, dict):
            research_pubs.append(
                ResearchPublication(
                    title=pub.get("title", "Research Publication"),
                    venue=pub.get("venue", "Conference/Journal"),
                    year=pub.get("year", 2026),
                    doi=pub.get("doi"),
                    doi_url=pub.get("doi_url"),
                )
            )

    # 9. Certifications
    certifications = [c.name for c in candidate.certifications]

    # 10. Assemble MasterProfile
    master_profile = MasterProfile(
        personal_info=personal_info,
        links=links_profile,
        headlines=candidate.headlines or {},
        summaries=candidate.summaries or {},
        education=educations,
        technical_skills=tech_skills,
        leadership_and_experience=experiences,
        professional_development=prof_devs,
        achievements=achievements,
        research_publications=research_pubs,
        certifications=certifications,
        reconciliation_metadata=rules.get("reconciliation_metadata"),
    )

    # 11. Convert Projects
    engine_projects = [
        ProjectItem(
            id=p.slug,
            title=p.title,
            subtitle=p.subtitle or "",
            notice=p.notice,
            is_fixed_project=p.is_fixed_project,
            fixed_position=p.fixed_position,
            categories=p.categories or [],
            skills=p.skills or [],
            links=[
                ProjectLink(
                    label=lnk.get("label", "Link"),
                    url=lnk.get("url", ""),
                )
                for lnk in (p.links or [])
                if isinstance(lnk, dict) and "url" in lnk
            ],
            bullets=p.bullets or [],
            metrics=p.metrics or [],
            evidence_source=p.evidence_source or "verified",
            verification_status=p.verification_status,
        )
        for p in candidate.projects
    ]

    # 12. Reconstruct ProfileConfig
    ps_conf = rules.get("project_selection") or {}
    has_fixed = ps_conf.get("has_fixed_project", True if candidate.slug == "sujal" else False)
    target_count = ps_conf.get("target_count", 4)
    weights = ps_conf.get(
        "weights",
        {
            "required_skills_coverage": 0.45,
            "responsibilities_alignment": 0.25,
            "tech_stack_similarity": 0.20,
            "domain_relevance": 0.10,
        },
    )

    fixed_rule = None
    if has_fixed:
        fixed_raw = ps_conf.get("fixed_project") or {}
        fixed_rule = FixedProjectRule(
            id=fixed_raw.get("id", "bearing_fault_diagnosis"),
            title=fixed_raw.get("title", "Bearing Fault Diagnosis Using Machine Learning"),
            position=fixed_raw.get("position", 2),
        )

    headline_rule_data = rules.get("headline_rule")
    headline_rule = HeadlineRule(**headline_rule_data) if isinstance(headline_rule_data, dict) else HeadlineRule()

    summary_rule_data = rules.get("summary_rule")
    summary_rule = SummaryRule(**summary_rule_data) if isinstance(summary_rule_data, dict) else SummaryRule()

    profile_config = ProfileConfig(
        profile_id=candidate.slug,
        display_name=candidate.display_name or candidate.full_name,
        is_synthetic=candidate.is_synthetic,
        headline_rule=headline_rule,
        summary_rule=summary_rule,
        project_selection=ProjectSelectionConfig(
            target_count=target_count,
            has_fixed_project=has_fixed,
            fixed_project=fixed_rule,
            weights=weights,
        ),
        prohibited_terms=rules.get("prohibited_terms", ["mechanical engineering", "mechanical engineer"]),
    )

    return master_profile, engine_projects, profile_config
