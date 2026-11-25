"""Unit and integration tests for multi-tenant database ownership, relationships, and invariants."""

import uuid
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.app.database.base import Base, auth_users
from backend.app.models.candidate import (
    CandidateProfile,
    Education,
    Experience,
    Skill,
    Project,
    Certification,
    Achievement,
    ProfessionalDevelopment,
)
from backend.app.models.resume import (
    JobDescription,
    Resume,
    ResumeVersion,
    ATSEvaluation,
    FileAsset,
)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Create an isolated SQLite database supporting auth schema references."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Enable foreign key support in SQLite
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON;"))

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ------------------------------------------------------------------------------
# 1. Model Column & Type Tests
# ------------------------------------------------------------------------------

def test_models_have_user_id_column():
    """Verify user_id exists on candidate_profiles, job_descriptions, resumes, file_assets."""
    assert hasattr(CandidateProfile, "user_id"), "CandidateProfile must have user_id"
    assert hasattr(JobDescription, "user_id"), "JobDescription must have user_id"
    assert hasattr(Resume, "user_id"), "Resume must have user_id"
    assert hasattr(FileAsset, "user_id"), "FileAsset must have user_id"


def test_child_tables_do_not_have_redundant_user_id():
    """Verify child tables inherit ownership from parent without redundant user_id columns."""
    assert not hasattr(Education, "user_id"), "Education should not have redundant user_id"
    assert not hasattr(Experience, "user_id"), "Experience should not have redundant user_id"
    assert not hasattr(Skill, "user_id"), "Skill should not have redundant user_id"
    assert not hasattr(Project, "user_id"), "Project should not have redundant user_id"
    assert not hasattr(Certification, "user_id"), "Certification should not have redundant user_id"
    assert not hasattr(Achievement, "user_id"), "Achievement should not have redundant user_id"
    assert not hasattr(ProfessionalDevelopment, "user_id"), "ProfessionalDevelopment should not have redundant user_id"
    assert not hasattr(ResumeVersion, "user_id"), "ResumeVersion should not have redundant user_id"
    assert not hasattr(ATSEvaluation, "user_id"), "ATSEvaluation should not have redundant user_id"


# ------------------------------------------------------------------------------
# 2. Sujal Profile Ownership & Data Preservation Tests
# ------------------------------------------------------------------------------

def test_sujal_profile_assigned_to_user_uuid(db_session: Session):
    """Verify sujal profile can be assigned to an authenticated user UUID and queried."""
    test_user_id = uuid.uuid4()
    # Insert auth user record
    db_session.execute(auth_users.insert().values(id=test_user_id))

    sujal = CandidateProfile(
        id=uuid.uuid4(),
        user_id=test_user_id,
        slug="sujal",
        full_name="Sujal Sunil Kadam",
        display_name="SUJAL KADAM",
        email="sujal@example.com",
        is_synthetic=False,
    )
    db_session.add(sujal)
    db_session.commit()

    queried = db_session.execute(
        select(CandidateProfile).where(CandidateProfile.slug == "sujal")
    ).scalar_one()

    assert queried.user_id == test_user_id
    assert queried.is_synthetic is False
    assert queried.full_name == "Sujal Sunil Kadam"


def test_sujal_child_resource_scoping(db_session: Session):
    """Verify child resources are strictly scoped through profile_id."""
    test_user_id = uuid.uuid4()
    db_session.execute(auth_users.insert().values(id=test_user_id))

    sujal = CandidateProfile(
        id=uuid.uuid4(),
        user_id=test_user_id,
        slug="sujal",
        full_name="Sujal Sunil Kadam",
        display_name="SUJAL KADAM",
        is_synthetic=False,
    )
    db_session.add(sujal)
    db_session.flush()

    # Add child items
    edu = Education(
        profile_id=sujal.id,
        degree="B.Tech Computer Science and Engineering",
        institution="PICT",
    )
    skill = Skill(
        profile_id=sujal.id,
        category="Languages",
        skill_name="Python",
    )
    project = Project(
        profile_id=sujal.id,
        slug="ai-resume-builder",
        title="AI Resume Builder",
    )
    db_session.add_all([edu, skill, project])
    db_session.commit()

    # Verify query through profile ownership
    db_session.refresh(sujal)
    assert len(sujal.educations) == 1
    assert sujal.educations[0].degree == "B.Tech Computer Science and Engineering"
    assert len(sujal.skills) == 1
    assert len(sujal.projects) == 1


# ------------------------------------------------------------------------------
# 3. Demo Candidate Synthetic Invariant Tests
# ------------------------------------------------------------------------------

def test_demo_candidate_remains_synthetic_and_unowned(db_session: Session):
    """Verify demo_candidate can exist unowned (user_id=None) with is_synthetic=True."""
    demo = CandidateProfile(
        id=uuid.uuid4(),
        user_id=None,
        slug="demo_candidate",
        full_name="Aarav Sharma (Demo)",
        display_name="AARAV SHARMA",
        is_synthetic=True,
    )
    db_session.add(demo)
    db_session.commit()

    queried = db_session.execute(
        select(CandidateProfile).where(CandidateProfile.slug == "demo_candidate")
    ).scalar_one()

    assert queried.user_id is None
    assert queried.is_synthetic is True


# ------------------------------------------------------------------------------
# 4. Resume & Job Description Ownership Tests
# ------------------------------------------------------------------------------

def test_resume_and_jd_ownership_integrity(db_session: Session):
    """Verify resumes and job descriptions link to user_id and profile_id."""
    test_user_id = uuid.uuid4()
    db_session.execute(auth_users.insert().values(id=test_user_id))

    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=test_user_id,
        slug="candidate_a",
        full_name="Candidate A",
        display_name="CANDIDATE A",
        is_synthetic=False,
    )
    db_session.add(profile)
    db_session.flush()

    jd = JobDescription(
        id=uuid.uuid4(),
        user_id=test_user_id,
        profile_id=profile.id,
        job_title="Senior Python Engineer",
        raw_text="Job description requirements...",
    )
    db_session.add(jd)
    db_session.flush()

    resume = Resume(
        id=uuid.uuid4(),
        user_id=test_user_id,
        profile_id=profile.id,
        job_description_id=jd.id,
        resume_title="Senior Python Engineer Resume",
        status="draft",
        editable_manifest={"header": {"name": "Candidate A"}},
    )
    db_session.add(resume)
    db_session.flush()

    # Add resume version and ATS evaluation
    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        manifest_snapshot=resume.editable_manifest,
        ats_score=85,
    )
    eval_record = ATSEvaluation(
        resume_id=resume.id,
        overall_score=85,
        format_score=28,
        relevance_score=42,
        quality_score=15,
    )
    db_session.add_all([version, eval_record])
    db_session.commit()

    # Query and assert ownership
    queried_resume = db_session.execute(
        select(Resume).where(Resume.user_id == test_user_id)
    ).scalar_one()
    assert queried_resume.id == resume.id
    assert queried_resume.user_id == test_user_id
    assert len(queried_resume.versions) == 1
    assert len(queried_resume.ats_evaluations) == 1


# ------------------------------------------------------------------------------
# 5. Cascade Delete & Referential Integrity Tests
# ------------------------------------------------------------------------------

def test_cascade_delete_profile_removes_children_cleanly(db_session: Session):
    """Verify cascade delete on candidate profile removes all child resources without orphans."""
    test_user_id = uuid.uuid4()
    db_session.execute(auth_users.insert().values(id=test_user_id))

    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=test_user_id,
        slug="to_delete",
        full_name="Delete Candidate",
        display_name="DELETE CANDIDATE",
        is_synthetic=False,
    )
    db_session.add(profile)
    db_session.flush()

    skill = Skill(profile_id=profile.id, category="Tech", skill_name="Docker")
    db_session.add(skill)
    db_session.commit()

    # Delete profile
    db_session.delete(profile)
    db_session.commit()

    # Verify no orphaned skills
    remaining_skills = db_session.execute(select(Skill)).scalars().all()
    assert len(remaining_skills) == 0


# ------------------------------------------------------------------------------
# 6. Migration Backfill Safety & Ambiguous Records Tests
# ------------------------------------------------------------------------------

def test_migration_detects_unresolved_sujal_owner(monkeypatch):
    """Verify migration aborts when non-synthetic profile exists without resolvable owner."""
    # Ensure SUJAL_AUTH_USER_ID is unset and ALLOWED_EMAILS is empty
    monkeypatch.delenv("SUJAL_AUTH_USER_ID", raising=False)
    monkeypatch.setenv("ALLOWED_EMAILS", "")

    # Import upgrade function from migration
    import importlib
    mig = importlib.import_module("backend.alembic.versions.7a8f9c0d1e2b_add_user_ownership_and_rls")

    class MockBind:
        dialect = type("Dialect", (), {"name": "sqlite"})()
        def execute(self, stmt, params=None):
            sql = str(stmt)
            if "SELECT id, slug, is_synthetic FROM candidate_profiles" in sql:
                # Returns sujal as non-synthetic
                return type("Result", (), {"fetchall": lambda self: [(uuid.uuid4(), "sujal", False)]})()
            return type("Result", (), {"fetchall": lambda self: [], "fetchone": lambda self: None, "scalar": lambda self: None})()

    monkeypatch.setattr(mig.op, "get_bind", lambda: MockBind())
    monkeypatch.setattr(mig.op, "add_column", lambda *a, **kw: None)
    monkeypatch.setattr(mig.op, "create_index", lambda *a, **kw: None)
    monkeypatch.setattr(mig.context, "is_offline_mode", lambda: False)

    with pytest.raises(RuntimeError, match="Non-synthetic profile.*owner user UUID could not be determined"):
        mig.upgrade()


def test_migration_detects_unowned_ambiguous_job_descriptions(monkeypatch):
    """Verify migration aborts when orphaned unowned job descriptions cannot be linked to an owner."""
    valid_uuid = str(uuid.uuid4())
    monkeypatch.setenv("SUJAL_AUTH_USER_ID", valid_uuid)

    import importlib
    mig = importlib.import_module("backend.alembic.versions.7a8f9c0d1e2b_add_user_ownership_and_rls")

    class MockBind:
        dialect = type("Dialect", (), {"name": "sqlite"})()
        def execute(self, stmt, params=None):
            sql = str(stmt)
            if "SELECT id, slug, is_synthetic FROM candidate_profiles" in sql:
                return type("Result", (), {"fetchall": lambda self: [(uuid.uuid4(), "sujal", False)]})()
            if "SELECT id FROM resumes WHERE profile_id NOT IN" in sql:
                return type("Result", (), {"fetchall": lambda self: []})()
            if "SELECT id FROM job_descriptions WHERE user_id IS NULL AND profile_id IS NULL" in sql:
                # Simulates an ambiguous orphaned job description
                return type("Result", (), {"fetchall": lambda self: [(uuid.uuid4(),)]})()
            return type("Result", (), {"fetchall": lambda self: [], "fetchone": lambda self: None, "scalar": lambda self: None})()

    monkeypatch.setattr(mig.op, "get_bind", lambda: MockBind())
    monkeypatch.setattr(mig.op, "add_column", lambda *a, **kw: None)
    monkeypatch.setattr(mig.op, "create_index", lambda *a, **kw: None)
    monkeypatch.setattr(mig.context, "is_offline_mode", lambda: False)

    with pytest.raises(RuntimeError, match="unowned job description"):
        mig.upgrade()


# ------------------------------------------------------------------------------
# 7. Static PostgreSQL Migration SQL Generation Tests
# ------------------------------------------------------------------------------

def test_alembic_offline_postgresql_sql_generation(monkeypatch):
    """Verify Alembic compiles clean, valid DDL for PostgreSQL in offline mode."""
    import subprocess
    import sys
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[2]
    cmd = [
        sys.executable,
        "-m",
        "alembic",
        "-c",
        str(root_dir / "backend" / "alembic.ini"),
        "upgrade",
        "4426bf87b36a:7a8f9c0d1e2b",
        "--sql",
    ]
    result = subprocess.run(cmd, cwd=root_dir, capture_output=True, text=True)
    assert result.returncode == 0, f"Offline migration SQL generation failed: {result.stderr}"

    sql_output = result.stdout
    # Verify core security and schema statements are present in generated SQL
    assert "ALTER TABLE candidate_profiles ADD COLUMN user_id UUID;" in sql_output
    assert "CREATE INDEX ix_candidate_profiles_user_id ON candidate_profiles (user_id);" in sql_output
    assert "fk_candidate_profiles_user_id_auth_users FOREIGN KEY(user_id) REFERENCES auth.users (id)" in sql_output
    assert "ALTER TABLE candidate_profiles ENABLE ROW LEVEL SECURITY;" in sql_output
    assert "CREATE POLICY \"candidate_profiles_select_policy\"" in sql_output
    assert "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;" in sql_output
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;" in sql_output
