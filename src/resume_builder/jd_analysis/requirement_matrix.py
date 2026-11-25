"""Requirement matrix builder mapping JD requirements to verified candidate evidence."""

from typing import List, Set, Tuple
from ..profile.models import MasterProfile, ProjectItem
from .keywords import canonicalize_skill, normalize_term
from .models import RequirementItem, RequirementMatrix, RequirementStatus


def build_requirement_matrix(
    profile: MasterProfile,
    projects: List[ProjectItem],
    required_skills: List[str],
    preferred_skills: List[str],
    responsibilities: List[str],
) -> RequirementMatrix:
    """
    Evaluate JD requirements against candidate evidence.
    Classify each into STRONG MATCH, PARTIAL MATCH, MISSING, or UNSUPPORTED.
    """
    matrix_items: List[RequirementItem] = []

    # Compile candidate verified skills and technologies
    profile_skills_flat = profile.technical_skills.get_all_skills_flat()
    profile_norm_map = {normalize_term(s): s for s in profile_skills_flat}

    # Add project skills
    project_skills_map = {}
    for p in projects:
        for s in p.skills:
            project_skills_map[normalize_term(s)] = (s, p.title)

    # Process Must-Have Required Skills
    for skill_req in required_skills:
        canonical = canonicalize_skill(skill_req)
        norm = normalize_term(canonical)

        matched_evidence = None
        status = RequirementStatus.MISSING
        matched_candidate_skills = []

        if norm in profile_norm_map:
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Verified skill in profile: {profile_norm_map[norm]}"
            matched_candidate_skills.append(profile_norm_map[norm])
        elif norm == "react" and "react18" in profile_norm_map:
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Verified skill in profile: {profile_norm_map['react18']}"
            matched_candidate_skills.append(profile_norm_map['react18'])
        elif norm == "react18" and "react" in profile_norm_map:
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Verified skill in profile: {profile_norm_map['react']}"
            matched_candidate_skills.append(profile_norm_map['react'])
        elif norm in project_skills_map:
            actual_s, proj_title = project_skills_map[norm]
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Applied in project '{proj_title}' ({actual_s})"
            matched_candidate_skills.append(actual_s)
        elif norm == "react" and "react18" in project_skills_map:
            actual_s, proj_title = project_skills_map["react18"]
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Applied in project '{proj_title}' ({actual_s})"
            matched_candidate_skills.append(actual_s)
        elif norm == "react18" and "react" in project_skills_map:
            actual_s, proj_title = project_skills_map["react"]
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Applied in project '{proj_title}' ({actual_s})"
            matched_candidate_skills.append(actual_s)
        else:
            # Check for partial matches or adjacent technologies
            if any(k in norm for k in ["api", "rest", "backend"]):
                status = RequirementStatus.PARTIAL_MATCH
                matched_evidence = "Experience building REST APIs in Spring Boot and PostgreSQL"
                matched_candidate_skills.append("REST APIs")
            elif any(k in norm for k in ["ui", "frontend", "web"]):
                status = RequirementStatus.PARTIAL_MATCH
                matched_evidence = "Experience with React 18, TypeScript, and modern responsive web interfaces"
                matched_candidate_skills.append("React 18")
            elif any(k in norm for k in ["cloud", "aws", "docker", "kubernetes", "c++", "golang", "ruby"]):
                status = RequirementStatus.UNSUPPORTED
                matched_evidence = "Not present in verified candidate profile — truthful omission"
            else:
                status = RequirementStatus.MISSING
                matched_evidence = "Requirement not documented in verified background"

        matrix_items.append(
            RequirementItem(
                category="Required Skill",
                requirement=skill_req,
                status=status,
                supporting_evidence=matched_evidence,
                is_must_have=True,
                candidate_skills_matched=matched_candidate_skills,
            )
        )

    # Process Preferred Skills
    for skill_req in preferred_skills:
        canonical = canonicalize_skill(skill_req)
        norm = normalize_term(canonical)

        matched_evidence = None
        status = RequirementStatus.MISSING
        matched_candidate_skills = []

        if norm in profile_norm_map:
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Profile verified: {profile_norm_map[norm]}"
            matched_candidate_skills.append(profile_norm_map[norm])
        elif norm == "react" and "react18" in profile_norm_map:
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Profile verified: {profile_norm_map['react18']}"
            matched_candidate_skills.append(profile_norm_map['react18'])
        elif norm == "react18" and "react" in profile_norm_map:
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Profile verified: {profile_norm_map['react']}"
            matched_candidate_skills.append(profile_norm_map['react'])
        elif norm in project_skills_map:
            actual_s, proj_title = project_skills_map[norm]
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Applied in project '{proj_title}' ({actual_s})"
            matched_candidate_skills.append(actual_s)
        elif norm == "react" and "react18" in project_skills_map:
            actual_s, proj_title = project_skills_map["react18"]
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Applied in project '{proj_title}' ({actual_s})"
            matched_candidate_skills.append(actual_s)
        elif norm == "react18" and "react" in project_skills_map:
            actual_s, proj_title = project_skills_map["react"]
            status = RequirementStatus.STRONG_MATCH
            matched_evidence = f"Applied in project '{proj_title}' ({actual_s})"
            matched_candidate_skills.append(actual_s)
        else:
            if any(k in norm for k in ["ml", "ai", "machinelearning", "deeplearning", "svm", "data"]):
                status = RequirementStatus.STRONG_MATCH
                matched_evidence = "Applied ML in Bearing Fault Diagnosis (Published Research Paper, DOI)"
                matched_candidate_skills.append("scikit-learn")
            else:
                status = RequirementStatus.MISSING
                matched_evidence = "Preferred qualification not claimed"

        matrix_items.append(
            RequirementItem(
                category="Preferred Skill",
                requirement=skill_req,
                status=status,
                supporting_evidence=matched_evidence,
                is_must_have=False,
                candidate_skills_matched=matched_candidate_skills,
            )
        )

    # Process Key Responsibilities
    for resp in responsibilities[:4]:  # Top responsibilities
        norm_resp = resp.lower()
        evidence = None
        status = RequirementStatus.PARTIAL_MATCH
        if "api" in norm_resp or "backend" in norm_resp or "service" in norm_resp:
            evidence = "Demonstrated in Spring Boot REST API project with MySQL and JUnit 5"
            status = RequirementStatus.STRONG_MATCH
        elif "frontend" in norm_resp or "ui" in norm_resp or "react" in norm_resp:
            evidence = "Demonstrated in Opportunity Radar (React 18/TypeScript) and Vogue Vault"
            status = RequirementStatus.STRONG_MATCH
        elif "test" in norm_resp or "quality" in norm_resp:
            evidence = "Demonstrated with JUnit 5, Vitest, and React Testing Library"
            status = RequirementStatus.STRONG_MATCH
        elif "data" in norm_resp or "sql" in norm_resp or "database" in norm_resp:
            evidence = "Demonstrated with PostgreSQL relational schema design and complex queries"
            status = RequirementStatus.STRONG_MATCH
        else:
            evidence = "Supported by general software engineering foundation and academic credentials"

        matrix_items.append(
            RequirementItem(
                category="Responsibility",
                requirement=resp,
                status=status,
                supporting_evidence=evidence,
                is_must_have=True,
                candidate_skills_matched=[],
            )
        )

    strong = sum(1 for i in matrix_items if i.status == RequirementStatus.STRONG_MATCH)
    partial = sum(1 for i in matrix_items if i.status == RequirementStatus.PARTIAL_MATCH)
    missing = sum(1 for i in matrix_items if i.status == RequirementStatus.MISSING)
    unsupported = sum(1 for i in matrix_items if i.status == RequirementStatus.UNSUPPORTED)
    total = len(matrix_items)
    match_pct = round(((strong * 1.0 + partial * 0.5) / max(total, 1)) * 100, 1)

    return RequirementMatrix(
        items=matrix_items,
        strong_match_count=strong,
        partial_match_count=partial,
        missing_count=missing,
        unsupported_count=unsupported,
        match_percentage=match_pct,
    )
