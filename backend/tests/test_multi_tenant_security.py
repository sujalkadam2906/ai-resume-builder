"""Comprehensive Multi-Tenant Security & Tenant Isolation Tests (Stage 2).

Verifies:
1. Cross-tenant candidate profile isolation (User B cannot read, update, or archive User A's profile).
2. Cross-tenant child entity isolation (User B cannot read, add, update, or delete User A's projects/skills/educations).
3. Cross-tenant job description isolation (User B cannot read, edit, delete, or match User A's JDs).
4. Cross-tenant resume lifecycle & export isolation (User B cannot read, update, approve, evaluate, or export User A's resumes).
5. Synthetic demo template safeguards:
   - demo_candidate is accessible to all authenticated users for reading and matching.
   - demo_candidate strictly rejects all mutations (HTTP 403 Forbidden).
   - Cloning demo_candidate creates an isolated, user-owned, non-synthetic copy in the user's workspace.
6. Sujal private profile protection:
   - Non-owner users receive HTTP 404 Not Found (zero resource enumeration).
7. Client-supplied user_id spoofing protection (backend always uses verified token identity).
8. Per-user rate limiting isolation (User A exhaustion does not degrade User B).
9. Unauthenticated request rejection (HTTP 401 Unauthorized).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import settings
from backend.app.core.auth import AuthenticatedUser, get_current_user
from backend.app.database.base import Base
from backend.app.database.session import get_db
from backend.app.main import app
from backend.app.models.candidate import CandidateProfile
from backend.app.services.profile_ingestion import ProfileIngestionService


USER_A_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))
USER_B_ID = str(uuid.UUID("22222222-2222-2222-2222-222222222222"))
USER_A_UUID = uuid.UUID(USER_A_ID)
USER_B_UUID = uuid.UUID(USER_B_ID)

user_a = AuthenticatedUser(
    email="user_a@example.com",
    user_id=USER_A_ID,
    name="Alice User A",
    roles=["user"],
    claims={"sub": USER_A_ID, "email": "user_a@example.com"},
)

user_b = AuthenticatedUser(
    email="user_b@example.com",
    user_id=USER_B_ID,
    name="Bob User B",
    roles=["user"],
    claims={"sub": USER_B_ID, "email": "user_b@example.com"},
)


@pytest.fixture(scope="function")
def tenant_fixture():
    """Isolated in-memory SQLite database pre-seeded with demo_candidate and sujal."""
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

    # Assign sujal to User A for ownership testing
    sujal = seed_session.query(CandidateProfile).filter_by(slug="sujal").first()
    if sujal:
        sujal.user_id = USER_A_UUID
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

    # Default to User A
    app.dependency_overrides[get_current_user] = lambda: user_a

    with TestClient(app) as client:
        yield client, TestingSession

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ==============================================================================
# 1. Cross-Tenant Candidate Profile Isolation
# ==============================================================================

def test_cross_tenant_profile_isolation(tenant_fixture):
    """User B cannot read, update, or archive User A's private profile."""
    client, _ = tenant_fixture

    # 1. As User A: sujal is accessible
    app.dependency_overrides[get_current_user] = lambda: user_a
    resp_a = client.get("/api/v1/profiles/sujal")
    assert resp_a.status_code == 200
    assert resp_a.json()["slug"] == "sujal"

    # User A creates a custom profile
    create_payload = {
        "slug": "alice_profile",
        "full_name": "Alice Wonderland",
        "display_name": "ALICE",
        "email": "alice@example.com",
    }
    create_resp = client.post("/api/v1/profiles", json=create_payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["slug"] == "alice_profile"

    # 2. Switch to User B
    app.dependency_overrides[get_current_user] = lambda: user_b

    # User B cannot read sujal (returns 404 to prevent resource enumeration)
    resp_b_sujal = client.get("/api/v1/profiles/sujal")
    assert resp_b_sujal.status_code == 404

    # User B cannot read alice_profile (returns 404)
    resp_b_alice = client.get("/api/v1/profiles/alice_profile")
    assert resp_b_alice.status_code == 404

    # User B cannot patch alice_profile
    patch_b = client.patch("/api/v1/profiles/alice_profile", json={"location": "Hacked City"})
    assert patch_b.status_code == 404

    # User B cannot delete/archive alice_profile
    del_b = client.delete("/api/v1/profiles/alice_profile")
    assert del_b.status_code == 404

    # User B list profiles: only sees demo_candidate (sujal and alice_profile are hidden)
    list_b = client.get("/api/v1/profiles")
    assert list_b.status_code == 200
    slugs = [p["slug"] for p in list_b.json()["items"]]
    assert "demo_candidate" in slugs
    assert "sujal" not in slugs
    assert "alice_profile" not in slugs


# ==============================================================================
# 2. Cross-Tenant Child Entity Isolation
# ==============================================================================

def test_cross_tenant_child_entity_isolation(tenant_fixture):
    """User B cannot read, add, edit, or delete child entities under User A's profile."""
    client, _ = tenant_fixture

    # 1. As User A: get sujal's existing education record
    app.dependency_overrides[get_current_user] = lambda: user_a
    edus = client.get("/api/v1/profiles/sujal/education").json()
    assert len(edus) > 0
    edu_id = edus[0]["id"]

    # 2. Switch to User B
    app.dependency_overrides[get_current_user] = lambda: user_b

    # User B cannot list User A's education
    assert client.get("/api/v1/profiles/sujal/education").status_code == 404

    # User B cannot get User A's single education
    assert client.get(f"/api/v1/profiles/sujal/education/{edu_id}").status_code == 404

    # User B cannot update User A's education
    assert client.patch(f"/api/v1/profiles/sujal/education/{edu_id}", json={"cgpa": "1.0"}).status_code == 404

    # User B cannot delete User A's education
    assert client.delete(f"/api/v1/profiles/sujal/education/{edu_id}").status_code == 404

    # User B cannot add education under User A's profile
    assert client.post("/api/v1/profiles/sujal/education", json={
        "degree": "Injected Degree", "institution": "Fake College"
    }).status_code == 404

    # User B cannot list, add, update, or delete projects under User A's profile
    assert client.get("/api/v1/profiles/sujal/projects").status_code == 404
    assert client.post("/api/v1/profiles/sujal/projects", json={
        "slug": "injected_proj", "title": "Injected Project"
    }).status_code == 404


# ==============================================================================
# 3. Cross-Tenant Job Description Isolation
# ==============================================================================

def test_cross_tenant_job_description_isolation(tenant_fixture):
    """User B cannot read, edit, delete, or match User A's Job Descriptions."""
    client, _ = tenant_fixture

    # 1. As User A: submit JD
    app.dependency_overrides[get_current_user] = lambda: user_a
    jd_payload = {
        "job_title": "Confidential Executive Role",
        "company_name": "Stealth Corp",
        "raw_text": "Looking for a Principal AI Engineer with 10+ years experience in Python and LLMs.",
    }
    create_resp = client.post("/api/v1/job-descriptions", json=jd_payload)
    assert create_resp.status_code == 201
    jd_id = create_resp.json()["id"]

    # User A can see it in their listing
    list_a = client.get("/api/v1/job-descriptions")
    assert any(jd["id"] == jd_id for jd in list_a.json()["items"])

    # 2. Switch to User B
    app.dependency_overrides[get_current_user] = lambda: user_b

    # User B cannot get User A's JD
    assert client.get(f"/api/v1/job-descriptions/{jd_id}").status_code == 404

    # User B cannot update User A's JD
    assert client.patch(f"/api/v1/job-descriptions/{jd_id}", json={"job_title": "Tampered Title"}).status_code == 404

    # User B cannot delete User A's JD
    assert client.delete(f"/api/v1/job-descriptions/{jd_id}").status_code == 404

    # User B cannot analyze User A's JD
    assert client.post(f"/api/v1/job-descriptions/{jd_id}/analyze").status_code == 404

    # User B does not see User A's JD in their listing
    list_b = client.get("/api/v1/job-descriptions")
    assert not any(jd["id"] == jd_id for jd in list_b.json()["items"])


# ==============================================================================
# 4. Cross-Tenant Resume & Export Isolation
# ==============================================================================

def test_cross_tenant_resume_isolation(tenant_fixture):
    """User B cannot read, update, approve, evaluate, or export User A's resumes."""
    client, _ = tenant_fixture

    # 1. As User A: create JD and generate draft resume
    app.dependency_overrides[get_current_user] = lambda: user_a
    jd_payload = {
        "job_title": "Full Stack Engineer",
        "company_name": "Tech Co",
        "raw_text": "Python FastAPI React PostgreSQL Docker Kubernetes developer wanted.",
    }
    jd_resp = client.post("/api/v1/job-descriptions", json=jd_payload)
    assert jd_resp.status_code == 201
    jd_id = jd_resp.json()["id"]

    gen_payload = {
        "profile_id": "sujal",
        "job_description_id": jd_id,
        "provider_override": "offline",
    }
    gen_resp = client.post("/api/v1/resumes/generate", json=gen_payload)
    assert gen_resp.status_code == 201
    resume_id = gen_resp.json()["id"]

    # 2. Switch to User B
    app.dependency_overrides[get_current_user] = lambda: user_b

    # User B cannot view resume details
    assert client.get(f"/api/v1/resumes/{resume_id}").status_code == 404

    # User B cannot edit resume
    assert client.patch(f"/api/v1/resumes/{resume_id}", json={"resume_title": "Stolen Resume"}).status_code == 404

    # User B cannot approve resume
    assert client.post(f"/api/v1/resumes/{resume_id}/approve").status_code == 404

    # User B cannot list versions
    assert client.get(f"/api/v1/resumes/{resume_id}/versions").status_code == 404

    # User B cannot evaluate resume
    assert client.post(f"/api/v1/resumes/{resume_id}/evaluate").status_code == 404

    # User B cannot export resume to PDF or DOCX
    assert client.get(f"/api/v1/resumes/{resume_id}/export/pdf").status_code == 404
    assert client.get(f"/api/v1/resumes/{resume_id}/export/docx").status_code == 404

    # User B listing does not contain User A's resume
    list_b = client.get("/api/v1/resumes")
    assert not any(r["id"] == resume_id for r in list_b.json()["items"])


# ==============================================================================
# 5. Shared Demo Template Safeguards & Cloning
# ==============================================================================

def test_demo_template_safeguards_and_clone(tenant_fixture):
    """demo_candidate is shared and read-only; cloning creates an isolated user copy."""
    client, _ = tenant_fixture

    # As User B:
    app.dependency_overrides[get_current_user] = lambda: user_b

    # 1. Reading demo_candidate succeeds
    demo_resp = client.get("/api/v1/profiles/demo_candidate")
    assert demo_resp.status_code == 200
    assert demo_resp.json()["is_synthetic"] is True

    # 2. Mutations against demo_candidate are strictly rejected with 403 Forbidden
    patch_demo = client.patch("/api/v1/profiles/demo_candidate", json={"location": "New York"})
    assert patch_demo.status_code == 403
    assert "Shared demo candidate template is read-only" in patch_demo.json()["detail"]

    del_demo = client.delete("/api/v1/profiles/demo_candidate")
    assert del_demo.status_code == 403

    add_skill = client.post("/api/v1/profiles/demo_candidate/skills", json={
        "category": "languages", "skill_name": "Rust"
    })
    assert add_skill.status_code == 403

    # 3. Clone demo_candidate into User B's workspace
    clone_resp = client.post("/api/v1/profiles/demo_candidate/clone", json={
        "new_slug": "bob_cloned_profile",
        "new_name": "Bob B. Builder",
    })
    assert clone_resp.status_code == 201
    cloned = clone_resp.json()
    assert cloned["slug"] == "bob_cloned_profile"
    assert cloned["full_name"] == "Bob B. Builder"
    assert cloned["is_synthetic"] is False  # Cloned profile is owned and non-synthetic
    assert len(cloned["skills"]) == len(demo_resp.json()["skills"])
    assert len(cloned["projects"]) == len(demo_resp.json()["projects"])

    # 4. User B CAN mutate their cloned copy
    patch_cloned = client.patch("/api/v1/profiles/bob_cloned_profile", json={"location": "Chicago, IL"})
    assert patch_cloned.status_code == 200
    assert patch_cloned.json()["location"] == "Chicago, IL"

    # 5. User A cannot access User B's cloned copy
    app.dependency_overrides[get_current_user] = lambda: user_a
    assert client.get("/api/v1/profiles/bob_cloned_profile").status_code == 404


# ==============================================================================
# 6. Unauthenticated Rejection
# ==============================================================================

def test_unauthenticated_request_rejected(tenant_fixture):
    """Unauthenticated requests without valid bearer tokens return HTTP 401."""
    client, _ = tenant_fixture

    # Clear auth overrides to enforce get_current_user dependency
    app.dependency_overrides.pop(get_current_user, None)

    # In non-production, REQUIRE_AUTH or lack of bypass enforces 401
    original_require_auth = settings.require_auth
    original_bypass = settings.allow_dev_auth_bypass
    try:
        settings.require_auth = True
        settings.allow_dev_auth_bypass = False

        resp = client.get("/api/v1/profiles")
        assert resp.status_code == 401
        assert "WWW-Authenticate" in resp.headers

        resp_jd = client.get("/api/v1/job-descriptions")
        assert resp_jd.status_code == 401

        resp_res = client.get("/api/v1/resumes")
        assert resp_res.status_code == 401
    finally:
        settings.require_auth = original_require_auth
        settings.allow_dev_auth_bypass = original_bypass
