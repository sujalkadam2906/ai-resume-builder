"""Comprehensive database foundation tests for SQLAlchemy 2.0, models, and migrations."""

import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.app.database.base import Base
from backend.app.database.session import (
    get_normalized_database_url,
    create_db_engine,
    check_db_connection,
    get_db,
)
from backend.app.models import (
    CandidateProfile,
    Education,
    Experience,
    Skill,
    Project,
    Certification,
    Achievement,
    ProfessionalDevelopment,
    JobDescription,
    Resume,
    ResumeVersion,
    ATSEvaluation,
    FileAsset,
)
from backend.app.main import app


# Isolated in-memory test database fixture (NEVER touches development or production database)
@pytest.fixture(scope="function")
def test_db_session():
    """Create a completely isolated in-memory SQLite database session for unit tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ------------------------------------------------------------------------------
# 1. Database Connection and URL Normalization Tests
# ------------------------------------------------------------------------------

def test_get_normalized_database_url():
    """Verify standard and legacy database URLs are properly mapped to psycopg3."""
    # Legacy postgres://
    assert get_normalized_database_url("postgres://usr:pwd@localhost:5432/db") == "postgresql+psycopg://usr:pwd@localhost:5432/db"
    # Generic postgresql:// without driver
    assert get_normalized_database_url("postgresql://usr:pwd@localhost:5432/db") == "postgresql+psycopg://usr:pwd@localhost:5432/db"
    # Explicit psycopg driver preserved
    assert get_normalized_database_url("postgresql+psycopg://usr:pwd@localhost:5432/db") == "postgresql+psycopg://usr:pwd@localhost:5432/db"
    # SQLite preserved
    assert get_normalized_database_url("sqlite:///:memory:") == "sqlite:///:memory:"


def test_check_db_connection_healthy_and_degraded():
    """Test check_db_connection reports healthy for valid engine and failure for broken engine."""
    healthy_engine = create_engine("sqlite:///:memory:")
    is_healthy, msg = check_db_connection(healthy_engine)
    assert is_healthy is True
    assert "healthy" in msg.lower()

    # Broken engine (non-existent host/port with zero timeout)
    broken_engine = create_engine("postgresql+psycopg://invalid:invalid@127.0.0.1:59999/non_existent?connect_timeout=1")
    is_broken, err = check_db_connection(broken_engine)
    assert is_broken is False
    assert len(err) > 0


def test_get_db_session_lifecycle():
    """Verify get_db generator yields an active Session and safely closes it."""
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)
    assert session.is_active is True
    with pytest.raises(StopIteration):
        next(gen)


# ------------------------------------------------------------------------------
# 2. Model Instantiation & Metadata Registration Tests
# ------------------------------------------------------------------------------

def test_metadata_contains_all_required_tables():
    """Confirm all 13 required entity tables are registered in Base.metadata."""
    expected_tables = {
        "candidate_profiles",
        "educations",
        "experiences",
        "skills",
        "projects",
        "certifications",
        "achievements",
        "professional_developments",
        "job_descriptions",
        "resumes",
        "resume_versions",
        "ats_evaluations",
        "file_assets",
    }
    registered_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(registered_tables)


def test_model_instantiation_and_uuids(test_db_session: Session):
    """Verify models instantiate with generated UUIDs and default attributes."""
    profile = CandidateProfile(
        slug="test-candidate",
        full_name="Jane Doe",
        display_name="JANE DOE",
        email="jane.doe@example.com",
        location="Remote, India",
        headlines={"primary": "Senior Software Architect"},
        summaries={"master": "Experienced distributed systems engineer."},
        links={"github": {"url": "https://github.com/janedoe", "display": "github.com/janedoe"}},
        config_rules={"theme": "modern_slate"},
    )
    test_db_session.add(profile)
    test_db_session.commit()
    test_db_session.refresh(profile)

    assert isinstance(profile.id, uuid.UUID)
    assert profile.slug == "test-candidate"
    assert profile.open_to_relocate is True
    assert profile.immediate_joiner is True

    # Test Project model
    project = Project(
        profile_id=profile.id,
        slug="cloud-orchestrator",
        title="Cloud Orchestrator",
        subtitle="Go / Kubernetes / gRPC",
        categories=["Cloud", "DevOps"],
        skills=["Go", "Kubernetes", "Docker"],
        bullets=["Designed multi-cluster autoscaling controller."],
        metrics=["Reduced failover latency by 45%"],
        evidence_source="verified_production",
    )
    test_db_session.add(project)
    test_db_session.commit()
    test_db_session.refresh(project)

    assert isinstance(project.id, uuid.UUID)
    assert project.profile_id == profile.id
    assert project.verification_status == "verified"


# ------------------------------------------------------------------------------
# 3. Foreign Key Relationships & Deliberate Cascade Deletions
# ------------------------------------------------------------------------------

def test_profile_relationships_and_cascade_delete(test_db_session: Session):
    """Verify bidirectional relationships and that deleting a candidate profile cascades to all child records."""
    profile = CandidateProfile(
        slug="alex-smith",
        full_name="Alex Smith",
        display_name="ALEX SMITH",
    )
    test_db_session.add(profile)
    test_db_session.commit()

    # Add child records
    edu = Education(
        profile_id=profile.id,
        degree="B.Tech Computer Science",
        institution="Apex University",
        start_year=2020,
        end_year=2024,
    )
    exp = Experience(
        profile_id=profile.id,
        role="Backend Engineer Intern",
        organization="CloudScale Systems",
        bullets=["Implemented Redis cache cluster."],
    )
    skill = Skill(
        profile_id=profile.id,
        category="languages",
        skill_name="Python",
    )
    cert = Certification(
        profile_id=profile.id,
        name="AWS Solutions Architect Associate",
    )
    achieve = Achievement(
        profile_id=profile.id,
        title="1st Place University Hackathon",
    )
    prof_dev = ProfessionalDevelopment(
        profile_id=profile.id,
        title="Advanced Distributed Systems",
        organization="Coursera",
    )
    jd = JobDescription(
        profile_id=profile.id,
        company_name="InnovateTech",
        job_title="Senior Python Engineer",
        raw_text="Looking for Python and FastAPI specialists.",
        extracted_skills=["Python", "FastAPI"],
    )
    test_db_session.add_all([edu, exp, skill, cert, achieve, prof_dev, jd])
    test_db_session.commit()

    resume = Resume(
        profile_id=profile.id,
        job_description_id=jd.id,
        resume_title="Alex Smith - InnovateTech Python Resume",
        editable_manifest={"header": {"name": "Alex Smith"}},
    )
    test_db_session.add(resume)
    test_db_session.commit()

    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        manifest_snapshot={"header": {"name": "Alex Smith"}},
        ats_score=88,
    )
    ats = ATSEvaluation(
        resume_id=resume.id,
        overall_score=88,
        matched_keywords=["Python", "FastAPI"],
        missing_keywords=["Docker"],
        critical_issues=[],
        warnings=[],
        suggestions=["Add Kubernetes metrics"],
    )
    test_db_session.add_all([version, ats])
    test_db_session.commit()

    # Verify relationships are loaded
    test_db_session.refresh(profile)
    assert len(profile.educations) == 1
    assert len(profile.experiences) == 1
    assert len(profile.skills) == 1
    assert len(profile.certifications) == 1
    assert len(profile.achievements) == 1
    assert len(profile.professional_developments) == 1
    assert len(profile.job_descriptions) == 1
    assert len(profile.resumes) == 1
    assert len(profile.resumes[0].versions) == 1
    assert len(profile.resumes[0].ats_evaluations) == 1

    # Cascade delete verification: deleting profile removes all child entities
    test_db_session.delete(profile)
    test_db_session.commit()

    assert test_db_session.query(CandidateProfile).filter_by(id=profile.id).first() is None
    assert test_db_session.query(Education).filter_by(profile_id=profile.id).first() is None
    assert test_db_session.query(Experience).filter_by(profile_id=profile.id).first() is None
    assert test_db_session.query(Skill).filter_by(profile_id=profile.id).first() is None
    assert test_db_session.query(Certification).filter_by(profile_id=profile.id).first() is None
    assert test_db_session.query(Achievement).filter_by(profile_id=profile.id).first() is None
    assert test_db_session.query(ProfessionalDevelopment).filter_by(profile_id=profile.id).first() is None
    assert test_db_session.query(JobDescription).filter_by(profile_id=profile.id).first() is None
    assert test_db_session.query(Resume).filter_by(profile_id=profile.id).first() is None
    assert test_db_session.query(ResumeVersion).filter_by(resume_id=resume.id).first() is None
    assert test_db_session.query(ATSEvaluation).filter_by(resume_id=resume.id).first() is None


# ------------------------------------------------------------------------------
# 4. Readiness Probe Integration & Degraded Simulation
# ------------------------------------------------------------------------------

def test_readiness_probe_database_status(monkeypatch):
    """Verify the /health/ready endpoint inspects database health accurately."""
    client = TestClient(app)
    import backend.app.api.v1.endpoints.health as health_mod

    # 1. Normal execution (with mocked healthy DB to prevent network timeouts)
    monkeypatch.setattr(health_mod, "check_db_connection", lambda: (True, "Database connection healthy"))
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] == "ok"

    # 2. Simulated degraded database condition
    monkeypatch.setattr(health_mod, "check_db_connection", lambda: (False, "Connection timeout"))
    degraded_resp = client.get("/api/v1/health/ready")
    assert degraded_resp.status_code == 503
    degraded_data = degraded_resp.json()
    assert degraded_data["status"] == "degraded"
    assert degraded_data["checks"]["database"]["status"] == "error"
    assert "Database connectivity check failed." in degraded_data["checks"]["database"]["detail"]
