"""Dedicated tests for Backend Hardening & Verification (Milestone 2B.4).

Verifies:
- Explicit PUT/PATCH semantics (PUT removed -> 405 Method Not Allowed)
- Mutation locking on archived candidate profiles (HTTP 400 Bad Request)
- Tamper-proofing of is_archived and archived_at against PATCH payload injection
- Fixed project safeguards (rejection of duplicate fixed project)
- Pagination boundary validation (page >= 1, 1 <= size <= 100)
- Session rollback lifecycle integrity
- Error sanitization (no stack traces or database connection strings leaked)
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.base import Base
from backend.app.database.session import get_db
from backend.app.main import app
from backend.app.models.candidate import CandidateProfile, Project
from backend.app.services.profile_ingestion import ProfileIngestionService
from backend.app.services.profile_service import ProfileService


@pytest.fixture(scope="function")
def hardening_client():
    """Isolated in-memory SQLite database pre-seeded with sujal and demo_candidate."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    seed_session = TestingSessionLocal()
    ingestion = ProfileIngestionService()
    ingestion.import_all(seed_session, target_profile_ids=["demo_candidate", "sujal"], overwrite=False)
    seed_session.commit()
    seed_session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, TestingSessionLocal

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ------------------------------------------------------------------------------
# 1. Explicit PUT/PATCH Semantics
# ------------------------------------------------------------------------------

def test_put_method_not_allowed(hardening_client):
    """Confirm that PUT on /profiles/{id} is removed and returns 405 Method Not Allowed."""
    client, _ = hardening_client
    response = client.put("/api/v1/profiles/sujal", json={"location": "Pune, India"})
    assert response.status_code == 405


def test_patch_partial_update_preserves_unmentioned_fields(hardening_client):
    """Confirm PATCH /profiles/{id} updates only targeted fields and preserves all others."""
    client, _ = hardening_client
    original = client.get("/api/v1/profiles/sujal").json()

    patch_resp = client.patch(
        "/api/v1/profiles/sujal",
        json={"professional_headline": "Senior Full-Stack AI Engineer"},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()

    # Updated field
    assert updated["professional_headline"] == "Senior Full-Stack AI Engineer"
    # Preserved fields
    assert updated["full_name"] == original["full_name"]
    assert updated["location"] == original["location"]
    assert updated["email"] == original["email"]
    assert len(updated["projects"]) == len(original["projects"])
    assert len(updated["skills"]) == len(original["skills"])


# ------------------------------------------------------------------------------
# 2. Archive Consistency & Mutation Guard
# ------------------------------------------------------------------------------

def test_tamper_proofing_is_archived_via_patch(hardening_client):
    """Confirm client cannot toggle is_archived or set archived_at via PATCH config_rules."""
    client, _ = hardening_client

    # Attempt to flip is_archived to True via PATCH config_rules
    patch_resp = client.patch(
        "/api/v1/profiles/sujal",
        json={"config_rules": {"is_archived": True, "archived_at": "fake-timestamp", "custom_key": "valid_val"}},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()

    # Custom key must be updated, but is_archived must remain False
    assert data["config_rules"].get("custom_key") == "valid_val"
    assert data["is_archived"] is False
    assert "is_archived" not in data["config_rules"]
    assert "archived_at" not in data["config_rules"]


def test_archived_profile_mutation_guard(hardening_client):
    """Confirm archived profiles reject all mutating endpoints with HTTP 400 Bad Request and synthetic templates reject mutations with 403."""
    client, _ = hardening_client

    # Demo template cannot be deleted/archived
    demo_resp = client.delete("/api/v1/profiles/demo_candidate")
    assert demo_resp.status_code == 403
    assert "Shared demo candidate template is read-only" in demo_resp.json()["detail"]

    # 1. Archive sujal
    archive_resp = client.delete("/api/v1/profiles/sujal")
    assert archive_resp.status_code == 200
    assert archive_resp.json()["status"] == "archived"

    expected_msg = "Candidate profile 'sujal' is archived. Restore the profile before making modifications."

    # 2. Attempt PATCH on profile
    p_resp = client.patch("/api/v1/profiles/sujal", json={"location": "Berlin"})
    assert p_resp.status_code == 400
    assert p_resp.json()["detail"] == expected_msg

    # 3. Attempt POST education
    edu_post = client.post(
        "/api/v1/profiles/sujal/education",
        json={"degree": "B.Tech", "institution": "Tech University", "start_year": 2020},
    )
    assert edu_post.status_code == 400
    assert edu_post.json()["detail"] == expected_msg

    # 4. Attempt POST project
    proj_post = client.post(
        "/api/v1/profiles/sujal/projects",
        json={"slug": "new_proj", "title": "New Project", "description": "Test"},
    )
    assert proj_post.status_code == 400
    assert proj_post.json()["detail"] == expected_msg

    # 5. Attempt POST skill
    skill_post = client.post(
        "/api/v1/profiles/sujal/skills",
        json={"category": "languages", "skill_name": "Go", "display_order": 99},
    )
    assert skill_post.status_code == 400
    assert skill_post.json()["detail"] == expected_msg

    # 6. Read endpoints must still function for inspection
    read_resp = client.get("/api/v1/profiles/sujal")
    assert read_resp.status_code == 200
    assert read_resp.json()["is_archived"] is True

    # 7. Restore profile and confirm mutations succeed again
    restore_resp = client.post("/api/v1/profiles/sujal/restore")
    assert restore_resp.status_code == 200
    assert restore_resp.json()["status"] == "restored"

    post_restore = client.patch("/api/v1/profiles/sujal", json={"location": "Berlin"})
    assert post_restore.status_code == 200
    assert post_restore.json()["location"] == "Berlin"


# ------------------------------------------------------------------------------
# 3. Pinned Project Safeguards
# ------------------------------------------------------------------------------

def test_prevent_duplicate_fixed_project(hardening_client):
    """Confirm a profile cannot have a second fixed pinned project created."""
    client, _ = hardening_client

    # sujal already has bearing_fault_diagnosis as fixed_position=2
    new_fixed_project = {
        "slug": "duplicate_fixed",
        "title": "Duplicate Fixed Project",
        "description": "Attempt to create another pinned project",
        "is_fixed_project": True,
        "fixed_position": 2,
    }
    resp = client.post("/api/v1/profiles/sujal/projects", json=new_fixed_project)
    assert resp.status_code == 400
    assert "already has a fixed pinned project" in resp.json()["detail"]


# ------------------------------------------------------------------------------
# 4. Pagination Boundary Validation
# ------------------------------------------------------------------------------

def test_pagination_boundary_rejection(hardening_client):
    """Verify pagination rejects out-of-bounds parameters (page < 1, size < 1, size > 100)."""
    client, _ = hardening_client

    # page=0 must be rejected with 422
    resp_page_zero = client.get("/api/v1/profiles?page=0")
    assert resp_page_zero.status_code == 422

    # size=0 must be rejected with 422
    resp_size_zero = client.get("/api/v1/profiles?size=0")
    assert resp_size_zero.status_code == 422

    # size=101 must be rejected with 422
    resp_size_101 = client.get("/api/v1/profiles?size=101")
    assert resp_size_101.status_code == 422

    # Valid boundaries (page=1, size=100) must succeed
    resp_valid = client.get("/api/v1/profiles?page=1&size=100")
    assert resp_valid.status_code == 200


# ------------------------------------------------------------------------------
# 5. Database Session Rollback Integrity
# ------------------------------------------------------------------------------

def test_database_session_rollback_on_failure(hardening_client):
    """Verify database transactions roll back cleanly when an error occurs during processing."""
    client, session_factory = hardening_client

    # Count initial projects for sujal
    initial_projects = client.get("/api/v1/profiles/sujal/projects").json()
    initial_count = len(initial_projects)

    # Attempt to post an invalid project that fails database constraint (or duplicate slug)
    duplicate_payload = {
        "slug": "bearing_fault_diagnosis",  # Duplicate slug
        "title": "Conflict Bearing Fault",
        "description": "Conflict project",
    }
    resp = client.post("/api/v1/profiles/sujal/projects", json=duplicate_payload)
    assert resp.status_code == 409

    # Verify session rollback left the database intact
    final_projects = client.get("/api/v1/profiles/sujal/projects").json()
    assert len(final_projects) == initial_count


# ------------------------------------------------------------------------------
# 6. Global Error Sanitization
# ------------------------------------------------------------------------------

def test_global_exception_handler_sanitizes_500(hardening_client):
    """Verify unhandled exceptions return a clean 500 JSON detail without leaking internals."""
    # Temporarily mount a buggy test route to simulate an uncaught exception
    @app.get("/api/v1/test-unhandled-crash")
    def crash_endpoint():
        raise RuntimeError("psycopg.OperationalError: connection to server at '127.0.0.1', port 5434 failed")

    try:
        with TestClient(app, raise_server_exceptions=False) as unhandled_client:
            resp = unhandled_client.get("/api/v1/test-unhandled-crash")
            assert resp.status_code == 500
            body = resp.json()
            assert "detail" in body
            assert body["detail"] == "An internal server error occurred. System administrators have been notified."
            # Ensure credentials/host/port/tracebacks do not appear in response
            assert "5434" not in body["detail"]
            assert "OperationalError" not in body["detail"]
            assert "traceback" not in body
    finally:
        # Clean up route
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/api/v1/test-unhandled-crash"]
