"""Unit tests for JD analysis, requirement matrix, and synonym handling."""

from resume_builder.jd_analysis.analyzer import JDAnalyzer
from resume_builder.jd_analysis.keywords import canonicalize_skill, extract_keywords_from_text
from resume_builder.jd_analysis.models import RequirementStatus
from resume_builder.profile.manager import ProfileManager


def test_canonical_synonyms():
    assert canonicalize_skill("js") == "JavaScript"
    assert canonicalize_skill("ts") == "TypeScript"
    assert canonicalize_skill("postgres") == "PostgreSQL"
    assert canonicalize_skill("springboot") == "Spring Boot"
    assert canonicalize_skill("react.js") == "React 18"


def test_extract_keywords():
    sample_text = "We require strong Java 8, Spring Boot, MySQL, and React experience. Knowledge of Git is a plus."
    kw = extract_keywords_from_text(sample_text)
    assert "Java" in kw or "Java 8" in kw
    assert "Spring Boot" in kw
    assert "MySQL" in kw
    assert "React 18" in kw
    assert "Git" in kw


def test_requirement_matrix_unsupported_filtering():
    pm = ProfileManager()
    profile = pm.load_profile()
    projects = pm.load_projects()

    analyzer = JDAnalyzer(profile, projects)
    jd_raw = """
    Job Title: Senior Cloud Architect
    Company: Acme Cloud
    Required:
    - Java
    - Spring Boot
    - AWS Cloud Architecture
    - Kubernetes
    - Docker
    """
    jd = analyzer.analyze(jd_raw)
    matrix = analyzer.evaluate_match(jd)

    unsupported = matrix.get_unsupported_skills()
    assert any("aws" in u.lower() or "cloud" in u.lower() or "kubernetes" in u.lower() or "docker" in u.lower() for u in unsupported)
    # Matched must haves should contain Java or Spring Boot
    matched = matrix.get_matched_must_have()
    assert "Java" in matched or "Spring Boot" in matched
