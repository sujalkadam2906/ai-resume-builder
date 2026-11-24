"""Comprehensive integration tests for Candidate Profile & Child Resource CRUD APIs."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.base import Base
from backend.app.database.session import get_db
from backend.app.main import app
from backend.app.services.profile_ingestion import ProfileIngestionService


@pytest.fixture(scope="function")
def api_client():
    """Create a completely isolated in-memory SQLite database pre-seeded with test profiles."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed the test profiles (demo_candidate & sujal)
    seed_session = TestingSessionLocal()
    ingestion = ProfileIngestionService()
    ingestion.import_all(seed_session, target_profile_ids=["demo_candidate", "sujal"], overwrite=False)
    seed_session.commit()
    seed_session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ------------------------------------------------------------------------------
# 1. Candidate Profile Root API Tests
# ------------------------------------------------------------------------------

def test_list_profiles_and_pagination(api_client: TestClient):
    """Test listing candidate profiles with pagination."""
    response = api_client.get("/api/v1/profiles?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["size"] == 10
    slugs = [item["slug"] for item in data["items"]]
    assert "demo_candidate" in slugs
    assert "sujal" in slugs


def test_get_profile_by_slug_and_uuid(api_client: TestClient):
    """Test retrieving complete profile by slug and by UUID."""
    # 1. Retrieve by slug
    resp_slug = api_client.get("/api/v1/profiles/sujal")
    assert resp_slug.status_code == 200
    data_slug = resp_slug.json()
    assert data_slug["slug"] == "sujal"
    assert data_slug["full_name"] == "Sujal Sunil Kadam"
    assert len(data_slug["skills"]) == 57
    assert len(data_slug["projects"]) == 7
    assert len(data_slug["certifications"]) == 6
    assert len(data_slug["educations"]) == 1

    # Verify research publications in config_rules
    assert "research_publications" in data_slug["config_rules"]
    assert len(data_slug["config_rules"]["research_publications"]) == 2

    # 2. Retrieve by UUID
    profile_uuid = data_slug["id"]
    resp_uuid = api_client.get(f"/api/v1/profiles/{profile_uuid}")
    assert resp_uuid.status_code == 200
    assert resp_uuid.json()["id"] == profile_uuid


def test_get_non_existent_profile_404(api_client: TestClient):
    """Test retrieving unknown profile returns 404."""
    response = api_client.get("/api/v1/profiles/ghost_user_99")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_profile_success(api_client: TestClient):
    """Test creating a new candidate profile."""
    payload = {
        "slug": "priya_patel",
        "full_name": "Priya Patel",
        "display_name": "PRIYA PATEL",
        "email": "priya.patel@example.com",
        "location": "Mumbai, India",
        "professional_headline": "Cloud DevOps Engineer",
        "is_synthetic": True,
        "skills": [
            {"category": "languages", "skill_name": "Python", "display_order": 0},
            {"category": "cloud_devops_and_deployment", "skill_name": "Terraform", "display_order": 1},
        ],
    }
    response = api_client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "priya_patel"
    assert data["full_name"] == "Priya Patel"
    assert data["is_synthetic"] is True
    assert len(data["skills"]) == 2


def test_create_profile_duplicate_slug_rejected_409(api_client: TestClient):
    """Test that creating a profile with an existing slug returns 409 Conflict."""
    payload = {
        "slug": "sujal",
        "full_name": "Duplicate Sujal",
    }
    response = api_client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_profile_invalid_payload_422(api_client: TestClient):
    """Test validation failure on invalid slug regex or missing full_name."""
    # Invalid slug with spaces and uppercase
    payload = {
        "slug": "Invalid Slug!",
        "full_name": "Test User",
    }
    response = api_client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 422


def test_update_profile_partial_patch(api_client: TestClient):
    """Test partial update (PATCH) preserves untouched fields."""
    patch_payload = {
        "location": "Tokyo, Japan",
        "open_to_relocate": False,
    }
    response = api_client.patch("/api/v1/profiles/sujal", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Tokyo, Japan"
    assert data["open_to_relocate"] is False
    # Untouched fields must remain intact
    assert data["full_name"] == "Sujal Sunil Kadam"
    assert len(data["projects"]) == 7


def test_archive_and_restore_profile(api_client: TestClient):
    """Test soft-deletion (archive) and restoration of candidate profile."""
    # 1. Archive demo_candidate
    del_resp = api_client.delete("/api/v1/profiles/demo_candidate")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "archived"

    # 2. Default list should now only contain sujal
    list_resp = api_client.get("/api/v1/profiles")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["slug"] == "sujal"

    # 3. List with include_archived=true returns both
    all_resp = api_client.get("/api/v1/profiles?include_archived=true")
    assert all_resp.status_code == 200
    all_items = all_resp.json()["items"]
    assert len(all_items) == 2

    # 4. Restore demo_candidate
    restore_resp = api_client.post("/api/v1/profiles/demo_candidate/restore")
    assert restore_resp.status_code == 200
    assert restore_resp.json()["status"] == "restored"

    # 5. Default list now shows both again
    list_again = api_client.get("/api/v1/profiles")
    assert len(list_again.json()["items"]) == 2


# ------------------------------------------------------------------------------
# 2. Child Resource CRUD Operations
# ------------------------------------------------------------------------------

def test_education_crud(api_client: TestClient):
    """Test Education child CRUD endpoints."""
    # List educations
    list_resp = api_client.get("/api/v1/profiles/sujal/education")
    assert list_resp.status_code == 200
    edus = list_resp.json()
    assert len(edus) == 1
    edu_id = edus[0]["id"]

    # Update education
    patch_resp = api_client.patch(f"/api/v1/profiles/sujal/education/{edu_id}", json={"cgpa": "8.50 / 10"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["cgpa"] == "8.50 / 10"

    # Add second education
    new_edu = {
        "degree": "Diploma in IT",
        "institution": "Polytechnic Institute",
        "start_year": 2019,
        "end_year": 2021,
    }
    create_resp = api_client.post("/api/v1/profiles/sujal/education", json=new_edu)
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]

    # Delete second education
    del_resp = api_client.delete(f"/api/v1/profiles/sujal/education/{created_id}")
    assert del_resp.status_code == 204


def test_experience_crud(api_client: TestClient):
    """Test Experience child CRUD endpoints."""
    list_resp = api_client.get("/api/v1/profiles/sujal/experience")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    exp_id = list_resp.json()[0]["id"]

    # Patch experience metrics
    patch_resp = api_client.patch(f"/api/v1/profiles/sujal/experience/{exp_id}", json={"metrics": "2,000+ students"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["metrics"] == "2,000+ students"


def test_skills_crud(api_client: TestClient):
    """Test Skill child CRUD endpoints."""
    list_resp = api_client.get("/api/v1/profiles/demo_candidate/skills")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 37

    # Add new skill
    new_skill = {
        "category": "languages",
        "skill_name": "Rust",
        "display_order": 99,
    }
    add_resp = api_client.post("/api/v1/profiles/demo_candidate/skills", json=new_skill)
    assert add_resp.status_code == 201
    skill_id = add_resp.json()["id"]

    # Delete skill
    del_resp = api_client.delete(f"/api/v1/profiles/demo_candidate/skills/{skill_id}")
    assert del_resp.status_code == 204


# ------------------------------------------------------------------------------
# 3. Critical Business Rules & Pinning Safeguards
# ------------------------------------------------------------------------------

def test_fixed_project_position_protection(api_client: TestClient):
    """Verify Bearing Fault Diagnosis fixed position at 2 cannot be modified or deleted."""
    # Lookup bearing_fault_diagnosis on sujal
    proj_resp = api_client.get("/api/v1/profiles/sujal/projects/bearing_fault_diagnosis")
    assert proj_resp.status_code == 200
    proj_data = proj_resp.json()
    assert proj_data["is_fixed_project"] is True
    assert proj_data["fixed_position"] == 2

    # 1. Attempting to change fixed_position to 3 must fail with 400 Bad Request
    illegal_move = api_client.patch(
        "/api/v1/profiles/sujal/projects/bearing_fault_diagnosis",
        json={"fixed_position": 3},
    )
    assert illegal_move.status_code == 400
    assert "Cannot modify fixed project position" in illegal_move.json()["detail"]

    # 2. Attempting to unpin fixed project must fail with 400 Bad Request
    illegal_unpin = api_client.patch(
        "/api/v1/profiles/sujal/projects/bearing_fault_diagnosis",
        json={"is_fixed_project": False},
    )
    assert illegal_unpin.status_code == 400
    assert "Cannot unpin fixed project safeguard" in illegal_unpin.json()["detail"]

    # 3. Attempting to delete pinned project must fail with 400 Bad Request
    illegal_del = api_client.delete("/api/v1/profiles/sujal/projects/bearing_fault_diagnosis")
    assert illegal_del.status_code == 400
    assert "Cannot delete pinned project safeguard" in illegal_del.json()["detail"]

    # 4. Updating non-safeguard fields (e.g. subtitle, bullets) must succeed
    legal_update = api_client.patch(
        "/api/v1/profiles/sujal/projects/bearing_fault_diagnosis",
        json={"subtitle": "Python · Scikit-Learn · Signal Processing · Research Paper Publisher"},
    )
    assert legal_update.status_code == 200
    assert "Research Paper Publisher" in legal_update.json()["subtitle"]
    assert legal_update.json()["fixed_position"] == 2


def test_cross_profile_resource_access_rejected(api_client: TestClient):
    """Verify child resource requests strictly reject cross-profile access."""
    # Obtain education ID from sujal
    sujal_edu = api_client.get("/api/v1/profiles/sujal/education").json()[0]
    sujal_edu_id = sujal_edu["id"]

    # Attempt to access Sujal's education under demo_candidate
    cross_access = api_client.get(f"/api/v1/profiles/demo_candidate/education/{sujal_edu_id}")
    assert cross_access.status_code == 404
    assert "not found for this profile" in cross_access.json()["detail"].lower()

    # Attempt to delete Sujal's education under demo_candidate
    cross_del = api_client.delete(f"/api/v1/profiles/demo_candidate/education/{sujal_edu_id}")
    assert cross_del.status_code == 404


def test_certifications_achievements_and_pd_crud(api_client: TestClient):
    """Test Certification, Achievement, and Professional Development child endpoints."""
    # 1. Certification CRUD
    certs = api_client.get("/api/v1/profiles/sujal/certifications").json()
    assert len(certs) == 6
    cert_id = certs[0]["id"]
    patch_cert = api_client.patch(f"/api/v1/profiles/sujal/certifications/{cert_id}", json={"issuer": "Oracle Corporation"})
    assert patch_cert.status_code == 200
    assert patch_cert.json()["issuer"] == "Oracle Corporation"

    # 2. Achievement CRUD
    achieves = api_client.get("/api/v1/profiles/sujal/achievements").json()
    assert len(achieves) == 1
    ach_id = achieves[0]["id"]
    patch_ach = api_client.patch(f"/api/v1/profiles/sujal/achievements/{ach_id}", json={"title": "Distinguished Placement Officer Award"})
    assert patch_ach.status_code == 200

    # 3. Professional Development CRUD
    pds = api_client.get("/api/v1/profiles/sujal/professional-development").json()
    assert len(pds) == 1
    pd_id = pds[0]["id"]
    patch_pd = api_client.patch(f"/api/v1/profiles/sujal/professional-development/{pd_id}", json={"date": "2024 (Verified)"})
    assert patch_pd.status_code == 200
    assert patch_pd.json()["date"] == "2024 (Verified)"
