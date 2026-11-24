"""Comprehensive tests for profile JSON/YAML ingestion, validation, and dry-run service."""

import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from backend.app.database.base import Base
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
from backend.app.services.profile_ingestion import (
    ProfileIngestionService,
    ParsedProfileBundle,
    DryRunReport,
)


@pytest.fixture(scope="function")
def sqlite_test_session():
    """Isolated in-memory SQLite session for testing ingestion transaction logic."""
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


@pytest.fixture
def tmp_profiles_dir(tmp_path: Path) -> Path:
    """Create a temporary profiles directory for testing synthetic edge cases."""
    prof_dir = tmp_path / "profiles"
    prof_dir.mkdir(parents=True, exist_ok=True)
    return prof_dir


# ------------------------------------------------------------------------------
# 1. Profile Discovery & Real Filesystem Validation
# ------------------------------------------------------------------------------

def test_discover_profiles():
    """Verify discovery finds existing profiles with master_profile.json."""
    service = ProfileIngestionService()
    discovered = service.discover_profiles()
    assert "demo_candidate" in discovered
    assert "sujal" in discovered
    # Uninitialized profile directory without master_profile.json must be excluded
    assert "non_existent_candidate_xyz" not in discovered


def test_valid_demo_profile_parsing():
    """Verify demo_candidate parses cleanly into all relational bundles."""
    service = ProfileIngestionService()
    bundle, issues = service.validate_and_parse_profile("demo_candidate")
    assert bundle is not None
    errors = [i for i in issues if i.level == "error"]
    assert len(errors) == 0

    assert bundle.candidate_profile_data["slug"] == "demo_candidate"
    assert bundle.candidate_profile_data["full_name"] == "Aarav Sharma (Demo Candidate)"
    assert bundle.candidate_profile_data["is_synthetic"] is True
    assert len(bundle.educations) == 1
    assert len(bundle.experiences) == 1
    assert len(bundle.skills) == 37
    assert len(bundle.projects) == 4
    assert len(bundle.certifications) == 3
    assert len(bundle.achievements) == 1
    assert len(bundle.professional_developments) == 1


def test_valid_sujal_profile_parsing_and_data_preservation():
    """Verify sujal profile parses cleanly and preserves publications and reconciliation data."""
    service = ProfileIngestionService()
    bundle, issues = service.validate_and_parse_profile("sujal")
    assert bundle is not None
    errors = [i for i in issues if i.level == "error"]
    assert len(errors) == 0

    assert bundle.candidate_profile_data["slug"] == "sujal"
    assert bundle.candidate_profile_data["full_name"] == "Sujal Sunil Kadam"
    assert bundle.candidate_profile_data["is_synthetic"] is False

    # Check preserved research publications and metadata
    cfg = bundle.candidate_profile_data["config_rules"]
    assert "research_publications" in cfg
    assert len(cfg["research_publications"]) == 2
    assert cfg["research_publications"][0]["title"] == "Bearing Fault Diagnosis Using Machine Learning"
    assert "reconciliation_metadata" in cfg
    assert "sources_inspected" in cfg["reconciliation_metadata"]

    # Check fixed project rule preservation
    assert len(bundle.projects) == 7
    fixed_projects = [p for p in bundle.projects if p["is_fixed_project"]]
    assert len(fixed_projects) == 1
    assert fixed_projects[0]["slug"] == "bearing_fault_diagnosis"
    assert fixed_projects[0]["fixed_position"] == 2


# ------------------------------------------------------------------------------
# 2. Error Handling & Edge Cases
# ------------------------------------------------------------------------------

def test_missing_profile_directory():
    """Verify graceful error reporting when a profile directory does not exist."""
    service = ProfileIngestionService()
    bundle, issues = service.validate_and_parse_profile("ghost_candidate_99")
    assert bundle is None
    assert any("Profile directory not found" in i.message for i in issues)


def test_invalid_json_syntax(tmp_profiles_dir: Path):
    """Verify error reporting for corrupted JSON files."""
    bad_dir = tmp_profiles_dir / "bad_json_candidate"
    bad_dir.mkdir(parents=True)
    (bad_dir / "master_profile.json").write_text("{ corrupt json: [ ", encoding="utf-8")

    service = ProfileIngestionService(profiles_dir=tmp_profiles_dir)
    bundle, issues = service.validate_and_parse_profile("bad_json_candidate")
    assert bundle is None
    assert any("JSON syntax error" in i.message for i in issues)


def test_missing_mandatory_name(tmp_profiles_dir: Path):
    """Verify validation fails if full_name is missing."""
    p_dir = tmp_profiles_dir / "no_name_candidate"
    p_dir.mkdir(parents=True)
    (p_dir / "master_profile.json").write_text(
        json.dumps({"personal_info": {"email": "test@example.com"}}),
        encoding="utf-8",
    )

    service = ProfileIngestionService(profiles_dir=tmp_profiles_dir)
    bundle, issues = service.validate_and_parse_profile("no_name_candidate")
    assert bundle is None
    assert any("personal_info.full_name" in i.field_name for i in issues)


def test_missing_optional_fields_uses_defaults(tmp_profiles_dir: Path):
    """Verify minimal profile parses successfully with proper fallback defaults."""
    p_dir = tmp_profiles_dir / "minimal_candidate"
    p_dir.mkdir(parents=True)
    minimal_data = {
        "personal_info": {
            "full_name": "Minimalist User",
        }
    }
    (p_dir / "master_profile.json").write_text(json.dumps(minimal_data), encoding="utf-8")

    service = ProfileIngestionService(profiles_dir=tmp_profiles_dir)
    bundle, issues = service.validate_and_parse_profile("minimal_candidate")
    assert bundle is not None
    assert bundle.candidate_profile_data["full_name"] == "Minimalist User"
    assert bundle.candidate_profile_data["display_name"] == "Minimalist User"
    assert bundle.candidate_profile_data["open_to_relocate"] is True
    assert bundle.candidate_profile_data["immediate_joiner"] is True
    assert bundle.candidate_profile_data["is_synthetic"] is False
    assert bundle.candidate_profile_data["email"] is None


def test_unknown_field_reporting_and_preservation(tmp_profiles_dir: Path):
    """Verify non-relational fields are reported as info and stored in extra_fields."""
    p_dir = tmp_profiles_dir / "custom_candidate"
    p_dir.mkdir(parents=True)
    custom_data = {
        "personal_info": {"full_name": "Custom Candidate"},
        "custom_portfolio_rating": 9.8,
        "legacy_tracking_id": "LEG-12345",
    }
    (p_dir / "master_profile.json").write_text(json.dumps(custom_data), encoding="utf-8")

    service = ProfileIngestionService(profiles_dir=tmp_profiles_dir)
    bundle, issues = service.validate_and_parse_profile("custom_candidate")
    assert bundle is not None
    cfg = bundle.candidate_profile_data["config_rules"]
    assert "extra_fields" in cfg
    assert cfg["extra_fields"]["custom_portfolio_rating"] == 9.8
    assert cfg["extra_fields"]["legacy_tracking_id"] == "LEG-12345"
    assert "master_profile.custom_portfolio_rating" in bundle.unmapped_fields


# ------------------------------------------------------------------------------
# 3. Dry-Run Audit Verification
# ------------------------------------------------------------------------------

def test_dry_run_audit_integrity():
    """Verify dry_run produces comprehensive report and never writes to database."""
    service = ProfileIngestionService()
    report = service.dry_run()

    assert isinstance(report, DryRunReport)
    assert report.dry_run_mode is True
    assert report.written_to_database is False
    assert "demo_candidate" in report.valid_profiles
    assert "sujal" in report.valid_profiles
    assert len(report.invalid_profiles) == 0

    # Verify expected total records across 8 tables
    expected = report.total_expected_records
    assert expected["candidate_profiles"] == 2
    assert expected["educations"] == 2
    assert expected["experiences"] == 2
    assert expected["skills"] == 94
    assert expected["projects"] == 11
    assert expected["certifications"] == 9
    assert expected["achievements"] == 2
    assert expected["professional_developments"] == 2


# ------------------------------------------------------------------------------
# 4. Idempotency & Transaction Management Tests (Isolated SQLite)
# ------------------------------------------------------------------------------

def test_idempotent_import_and_duplicate_skip(sqlite_test_session: Session):
    """Verify importing same profile twice skips duplicates when overwrite=False."""
    service = ProfileIngestionService()
    bundle, _ = service.validate_and_parse_profile("demo_candidate")
    assert bundle is not None

    # First import
    res1 = service.import_profile(bundle, sqlite_test_session, overwrite=False)
    sqlite_test_session.commit()
    assert res1["status"] == "imported"

    # Verify rows in DB
    prof_count = sqlite_test_session.execute(select(CandidateProfile)).scalars().all()
    assert len(prof_count) == 1

    # Second import without overwrite
    res2 = service.import_profile(bundle, sqlite_test_session, overwrite=False)
    sqlite_test_session.commit()
    assert res2["status"] == "skipped"
    assert res2["reason"] == "duplicate_profile"

    # Row count must remain exactly 1
    prof_count2 = sqlite_test_session.execute(select(CandidateProfile)).scalars().all()
    assert len(prof_count2) == 1


def test_idempotent_import_with_overwrite(sqlite_test_session: Session):
    """Verify importing with overwrite=True refreshes data without creating duplicate candidates."""
    service = ProfileIngestionService()
    bundle, _ = service.validate_and_parse_profile("demo_candidate")
    assert bundle is not None

    # First import
    service.import_profile(bundle, sqlite_test_session, overwrite=False)
    sqlite_test_session.commit()

    # Re-import with overwrite
    res_overwrite = service.import_profile(bundle, sqlite_test_session, overwrite=True)
    sqlite_test_session.commit()
    assert res_overwrite["status"] == "imported"

    # Verify no duplicate candidate profiles or child records
    profiles = sqlite_test_session.execute(select(CandidateProfile)).scalars().all()
    assert len(profiles) == 1
    projects = sqlite_test_session.execute(select(Project)).scalars().all()
    assert len(projects) == 4
    skills = sqlite_test_session.execute(select(Skill)).scalars().all()
    assert len(skills) == 37


def test_transaction_rollback_on_failure(sqlite_test_session: Session):
    """Verify transaction rolls back completely when an error occurs."""
    service = ProfileIngestionService()
    bundle, _ = service.validate_and_parse_profile("demo_candidate")
    assert bundle is not None

    # Deliberately corrupt bundle to trigger integrity failure (duplicate skill UUID or invalid FK)
    corrupted_bundle = ParsedProfileBundle(
        profile_id="corrupt_candidate",
        candidate_profile_data={**bundle.candidate_profile_data, "slug": "corrupt_candidate"},
        skills=[{"id": "invalid-uuid-type", "category": "bad"}],  # Will trigger DB error
    )

    try:
        service.import_profile(corrupted_bundle, sqlite_test_session, overwrite=False)
        sqlite_test_session.commit()
    except Exception:
        sqlite_test_session.rollback()

    # Confirm candidate was NOT persisted due to rollback
    check = sqlite_test_session.execute(
        select(CandidateProfile).filter_by(slug="corrupt_candidate")
    ).scalar_one_or_none()
    assert check is None


def test_import_all_atomic_batch(sqlite_test_session: Session):
    """Verify import_all imports both demo_candidate and sujal in one transaction."""
    service = ProfileIngestionService()
    results = service.import_all(sqlite_test_session, target_profile_ids=["demo_candidate", "sujal"], overwrite=False)
    sqlite_test_session.commit()

    assert "demo_candidate" in results
    assert "sujal" in results
    assert results["demo_candidate"]["status"] == "imported"
    assert results["sujal"]["status"] == "imported"

    profiles = sqlite_test_session.execute(select(CandidateProfile)).scalars().all()
    assert len(profiles) == 2
