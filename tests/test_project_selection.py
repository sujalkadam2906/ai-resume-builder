"""Unit tests for the mandatory project selection rule and ranking heuristics."""

import pytest
from resume_builder.jd_analysis.models import JobDescription
from resume_builder.profile.manager import ProfileManager
from resume_builder.project_selection.selector import select_projects_for_jd


@pytest.fixture
def all_projects():
    pm = ProfileManager()
    return pm.load_projects()


def test_bearing_fault_always_position_2_java_role(all_projects):
    jd_java = JobDescription(
        raw_text="Looking for Java Spring Boot Developer with SQL and REST API knowledge",
        company_name="Acme Corp",
        job_title="Java Backend Engineer",
        required_skills=["Java", "Spring Boot", "MySQL", "REST APIs"],
        responsibilities=["Build backend REST APIs in Spring Boot", "Manage MySQL database"],
    )

    selected, scored_pool, shortage = select_projects_for_jd(all_projects, jd_java, target_count=4)

    assert len(selected) == 4
    # Slot 2 must ALWAYS be Bearing Fault Detection
    assert selected[1].id == "bearing_fault_diagnosis"
    assert "bearing" in selected[1].title.lower()
    # Slot 1 should be Java REST API project
    assert selected[0].id == "employee_management_api"


def test_bearing_fault_always_position_2_frontend_role(all_projects):
    jd_frontend = JobDescription(
        raw_text="Looking for Frontend React Developer with TypeScript, Vite, CSS Modules",
        company_name="DesignTech",
        job_title="Frontend React Developer",
        required_skills=["React 18", "TypeScript", "JavaScript", "HTML5", "CSS3"],
        responsibilities=["Build responsive React web applications", "Implement UI components"],
    )

    selected, scored_pool, shortage = select_projects_for_jd(all_projects, jd_frontend, target_count=4)

    assert len(selected) == 4
    # Slot 2 must ALWAYS be Bearing Fault Detection
    assert selected[1].id == "bearing_fault_diagnosis"
    # Slot 1 should be Opportunity Radar (React/TypeScript) or Vogue Vault
    assert selected[0].id in ("opportunity_radar", "vogue_vault")


def test_bearing_fault_always_position_2_ml_role(all_projects):
    jd_ml = JobDescription(
        raw_text="Seeking Python Machine Learning and Data Analysis Engineer",
        company_name="AI Labs",
        job_title="Machine Learning Engineer",
        required_skills=["Python", "Pandas", "NumPy", "scikit-learn", "Machine Learning"],
    )

    selected, scored_pool, shortage = select_projects_for_jd(all_projects, jd_ml, target_count=4)

    assert len(selected) == 4
    # Slot 2 is still Bearing Fault Detection!
    assert selected[1].id == "bearing_fault_diagnosis"


def test_no_duplicate_projects(all_projects):
    jd = JobDescription(
        raw_text="Full-stack developer needed",
        company_name="Tech Solutions",
        job_title="Full-Stack Developer",
        required_skills=["Java", "React 18", "SQL"],
    )
    selected, _, _ = select_projects_for_jd(all_projects, jd, target_count=4)
    ids = [p.id for p in selected]
    assert len(ids) == len(set(ids)), "Selected projects contain duplicates!"


def test_bynry_forward_deployed_project_selection(all_projects):
    """
    Test Bynry Forward Deployed Engineer Intern selection:
    Slot 1: SpringNotes Forge (Python AI automation, workflow, ReportLab, Pytest)
    Slot 2: Bearing Fault Diagnosis (Fixed position 2)
    Slots 3 & 4: Employee Management REST API & Online Bookstore Database Analysis
    """
    from resume_builder.jd_analysis.analyzer import JDAnalyzer
    pm = ProfileManager()
    profile = pm.load_profile()
    analyzer = JDAnalyzer(profile, all_projects)

    with open("job_descriptions/bynry_forward_deployed_engineer_intern.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

    jd_bynry = analyzer.analyze(raw_text)
    selected, scored_pool, shortage = select_projects_for_jd(all_projects, jd_bynry, target_count=4)

    assert len(selected) == 4
    # Slot 1: SpringNotes Forge
    assert selected[0].id == "spring_notes_forge"
    # Slot 2: Permanently Bearing Fault Diagnosis
    assert selected[1].id == "bearing_fault_diagnosis"
    # Slots 3 & 4: Python AI / Database projects
    assert {selected[2].id, selected[3].id} in [
        {"employee_management_api", "online_bookstore_db"},
        {"ai_resume_builder", "online_bookstore_db"},
    ]
