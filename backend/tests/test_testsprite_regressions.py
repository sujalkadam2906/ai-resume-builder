"""Regression tests covering TestSprite production fixes:
1. Job Description Analysis:
   - FastAPI and modern tech extraction
   - React canonicalization without expanding to React 18
   - Extracting actual responsibilities and requirements without generic fallback
2. ATS Consistency:
   - Match percentage formula consistency between JD analysis and candidate matching
3. Demo Candidate Security:
   - Ensuring demo_candidate and unowned templates cannot be updated, deleted, or mutated
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.auth import AuthenticatedUser, get_current_user
from backend.app.database.base import Base
from backend.app.database.session import get_db
from backend.app.main import app
from backend.app.models.candidate import CandidateProfile
from backend.app.schemas.resume import JobDescriptionCreate
from backend.app.services.job_description_service import JobDescriptionService
from backend.app.services.matching_service import CandidateMatchingService
from backend.app.services.profile_converter import db_candidate_to_engine_profile
from backend.app.services.profile_ingestion import ProfileIngestionService
from backend.app.services.profile_service import ProfileService
from src.resume_builder.jd_analysis.analyzer import JDAnalyzer
from src.resume_builder.jd_analysis.keywords import extract_keywords_from_text


TEST_USER_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))
test_user = AuthenticatedUser(
    email="testuser@example.com",
    user_id=TEST_USER_ID,
    name="Test User",
    roles=["user"],
    claims={"sub": TEST_USER_ID, "email": "testuser@example.com"},
)


@pytest.fixture(scope="function")
def test_setup():
    """In-memory SQLite database pre-seeded with demo_candidate and sujal."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    seed_session = TestingSession()
    ingestion = ProfileIngestionService()
    ingestion.import_all(seed_session, target_profile_ids=["demo_candidate", "sujal"], overwrite=False)

    # Assign sujal to TEST_USER_ID
    sujal = seed_session.query(CandidateProfile).filter_by(slug="sujal").first()
    if sujal:
        sujal.user_id = uuid.UUID(TEST_USER_ID)
    seed_session.commit()
    seed_session.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: test_user

    with TestClient(app) as client:
        yield client, TestingSession

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def api_client(test_setup):
    client, _ = test_setup
    return client


@pytest.fixture(scope="function")
def db_session(test_setup):
    _, TestingSession = test_setup
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


TESTSPRITE_SAMPLE_JD = """
Job Title: Senior Backend Engineer
Company: TestSprite Technologies

About Us:
TestSprite is an autonomous software QA platform testing modern web applications.

What You'll Do:
- Architect and scale high-performance REST APIs using FastAPI and Python.
- Collaborate with frontend teams building responsive interfaces with React.
- Optimize PostgreSQL database queries, indexes, and connection pooling.
- Deploy containerized services with Docker and manage CI/CD pipelines.
- Ensure 99.9% uptime and high test coverage using Pytest.

Requirements:
- 3+ years of production experience developing backend services in Python and FastAPI.
- Strong knowledge of relational databases including PostgreSQL.
- Experience with React, TypeScript, and modern frontend workflows.
- Familiarity with Docker and container orchestration.

Preferred Qualifications:
- Experience with Redis and caching strategies.
- Knowledge of Kubernetes and cloud deployment.
"""


def test_testsprite_jd_skill_extraction_and_no_react18_expansion():
    """Verify FastAPI is extracted, and React is NOT incorrectly expanded to React 18."""
    keywords = extract_keywords_from_text(TESTSPRITE_SAMPLE_JD)
    assert "FastAPI" in keywords, "FastAPI was missed during keyword extraction!"
    assert "React" in keywords, "React was missed during keyword extraction!"
    assert "React 18" not in keywords, "React was incorrectly expanded to React 18 when JD only specified React!"


def test_testsprite_jd_responsibilities_and_requirements_extracted_without_fallback():
    """Verify responsibilities and requirements are extracted from actual JD text, not generic fallback."""
    analyzer = JDAnalyzer(profile=None, projects=[])
    jd = analyzer.analyze(TESTSPRITE_SAMPLE_JD)

    assert jd.company_name == "TestSprite Technologies"
    assert jd.job_title == "Senior Backend Engineer"

    # Responsibilities must be extracted from the JD
    assert len(jd.responsibilities) >= 4
    assert any("FastAPI and Python" in r for r in jd.responsibilities), "Actual JD responsibility missing!"
    assert any("React" in r for r in jd.responsibilities), "Actual JD responsibility missing!"
    assert not any("maintainable, and testable code" in r for r in jd.responsibilities), "Generic fallback text was used!"

    # Required skills must include FastAPI and React (not React 18)
    assert "FastAPI" in jd.required_skills
    assert "React" in jd.required_skills
    assert "React 18" not in jd.required_skills

    # Preferred skills must include Redis and Kubernetes
    assert "Redis" in jd.preferred_skills or "Kubernetes" in jd.preferred_skills


def test_ats_match_percentage_calculation_consistency(db_session: Session):
    """Verify JobDescriptionService and CandidateMatchingService use identical match calculations without inflation."""
    # Create test candidate with specific skills
    candidate = ProfileService.get_profile_by_id_or_slug(db_session, "sujal")
    assert candidate is not None

    # Submit TestSprite JD
    jd_record = JobDescriptionService.create_job_description(
        db_session,
        data=JobDescriptionCreate(
            profile_id="sujal",
            job_title="Senior Backend Engineer",
            company_name="TestSprite Technologies",
            raw_text=TESTSPRITE_SAMPLE_JD,
            source_url=None,
        ),
        user_id=uuid.UUID(TEST_USER_ID),
    )

    # 1. Run JobDescriptionService analysis
    analysis_resp = JobDescriptionService.analyze_job_description(db_session, jd_record, candidate_profile=candidate)

    # 2. Run CandidateMatchingService
    match_resp = CandidateMatchingService.match_candidate_to_jd(db_session, candidate, jd_record)

    # Both must report the exact same match percentage!
    assert analysis_resp.match_percentage == match_resp.overall_match_percentage, (
        f"Mismatch: JD analysis calculated {analysis_resp.match_percentage}% while "
        f"CandidateMatching calculated {match_resp.overall_match_percentage}%!"
    )
    # The percentage must equal matched / total
    expected_pct = round(len(match_resp.matched_skills) / len(jd_record.extracted_skills) * 100.0, 1)
    # Match percentage cannot be artificially inflated to 83% if skills are missing
    assert match_resp.overall_match_percentage < 80.0


def test_demo_candidate_cannot_be_mutated_by_authenticated_user(api_client: TestClient):
    """Confirm authenticated users cannot update, delete, or modify shared demo candidate through API calls."""
    # 1. PATCH demo_candidate must return 403 Forbidden
    patch_resp = api_client.patch(
        "/api/v1/profiles/demo_candidate",
        json={"full_name": "Tampered Name"},
    )
    assert patch_resp.status_code == 403
    assert "read-only" in patch_resp.json()["detail"].lower()

    # 2. DELETE demo_candidate must return 403 Forbidden
    del_resp = api_client.delete("/api/v1/profiles/demo_candidate")
    assert del_resp.status_code == 403
    assert "read-only" in del_resp.json()["detail"].lower()

    # 3. Adding child resource (education) to demo_candidate must return 403 Forbidden
    edu_resp = api_client.post(
        "/api/v1/profiles/demo_candidate/education",
        json={
            "degree": "B.S. Computer Science",
            "institution": "Stanford University",
            "duration": "2020-2024",
        },
    )
    assert edu_resp.status_code == 403
    assert "read-only" in edu_resp.json()["detail"].lower()

    # 4. Adding skill to demo_candidate must return 403 Forbidden
    skill_resp = api_client.post(
        "/api/v1/profiles/demo_candidate/skills",
        json={"category": "Languages", "skill_name": "Haskell"},
    )
    assert skill_resp.status_code == 403
    assert "read-only" in skill_resp.json()["detail"].lower()
