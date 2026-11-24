"""Comprehensive integration tests for Milestone 2C: Resume Generation & Tailoring APIs."""

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


SAMPLE_SWE_JD = """
About the Job:
We are looking for a Senior Software Engineer at FinTech Global to join our core backend payments team.

Job Title: Backend Software Engineer
Company: FinTech Global
Source: https://careers.fintechglobal.com/jobs/102

Requirements:
- Strong proficiency in Java, Python, and SQL.
- Hands-on experience with Spring Boot, FastAPI, and PostgreSQL.
- Experience building scalable REST APIs and microservices.
- Familiarity with Docker, Git, and Linux environments.
- Knowledge of machine learning concepts or data analytics is a major plus.

Responsibilities:
- Develop high-quality, maintainable, and testable backend services.
- Design and implement REST APIs and persistence layers for financial transactions.
- Collaborate with cross-functional teams to deliver software features.
- Participate in code reviews, architectural discussions, and system observability.

Preferred Qualifications:
- Experience with AWS, Kubernetes, and CI/CD pipelines.
- Bachelor's degree in Computer Science, Engineering, or related technical field.
"""


@pytest.fixture(scope="function")
def api_client():
    """Create a completely isolated in-memory SQLite database pre-seeded with sujal and demo_candidate."""
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
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ==============================================================================
# 1. Job Description CRUD & Analysis Tests
# ==============================================================================

def test_job_description_crud(api_client: TestClient):
    """Test creating, listing, retrieving, updating, and deleting job descriptions."""
    # 1. Create JD linked to sujal
    payload = {
        "job_title": "Backend Software Engineer",
        "company_name": "FinTech Global",
        "raw_text": SAMPLE_SWE_JD,
        "source_url": "https://careers.fintechglobal.com/jobs/102",
        "profile_id": "sujal",
    }
    create_resp = api_client.post("/api/v1/job-descriptions", json=payload)
    assert create_resp.status_code == 201
    jd_data = create_resp.json()
    assert jd_data["job_title"] == "Backend Software Engineer"
    assert jd_data["company_name"] == "FinTech Global"
    assert jd_data["source_url"] == "https://careers.fintechglobal.com/jobs/102"
    jd_id = jd_data["id"]

    # 2. List JDs
    list_resp = api_client.get("/api/v1/job-descriptions?profile_id=sujal")
    assert list_resp.status_code == 200
    list_json = list_resp.json()
    assert list_json["total"] == 1
    assert list_json["items"][0]["id"] == jd_id

    # 3. Retrieve by ID
    get_resp = api_client.get(f"/api/v1/job-descriptions/{jd_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["company_name"] == "FinTech Global"

    # 4. Partial update (PATCH)
    patch_resp = api_client.patch(
        f"/api/v1/job-descriptions/{jd_id}",
        json={"job_title": "Lead Platform Engineer"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["job_title"] == "Lead Platform Engineer"
    assert patch_resp.json()["company_name"] == "FinTech Global"

    # 5. Delete JD
    del_resp = api_client.delete(f"/api/v1/job-descriptions/{jd_id}")
    assert del_resp.status_code == 204

    # Confirm 404 after deletion
    assert api_client.get(f"/api/v1/job-descriptions/{jd_id}").status_code == 404


def test_job_description_analysis_and_retrieval(api_client: TestClient):
    """Test analyzing a job description and retrieving saved structured analysis."""
    # Create JD
    create_resp = api_client.post(
        "/api/v1/job-descriptions",
        json={"raw_text": SAMPLE_SWE_JD, "profile_id": "sujal"},
    )
    jd_id = create_resp.json()["id"]

    # Trigger analysis
    analyze_resp = api_client.post(f"/api/v1/job-descriptions/{jd_id}/analyze")
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()

    assert analysis["company_name"] == "FinTech Global"
    assert len(analysis["required_skills"]) > 0
    # Must identify Java, Python, SQL, PostgreSQL, Spring Boot, etc.
    skills_lower = [s.lower() for s in analysis["required_skills"]]
    assert any("python" in s for s in skills_lower)
    assert any("java" in s for s in skills_lower)
    assert any("sql" in s or "postgres" in s for s in skills_lower)

    # Verify tech stack breakdown
    tech_stack = analysis["technical_stack"]
    assert "languages" in tech_stack
    assert "databases" in tech_stack

    # Retrieve stored analysis via GET
    saved_analysis_resp = api_client.get(f"/api/v1/job-descriptions/{jd_id}/analysis")
    assert saved_analysis_resp.status_code == 200
    assert saved_analysis_resp.json()["company_name"] == "FinTech Global"
    assert len(saved_analysis_resp.json()["required_skills"]) == len(analysis["required_skills"])


# ==============================================================================
# 2. Candidate Matching & Intelligent Project Ranking Tests
# ==============================================================================

def test_candidate_matching_and_sujal_pinned_project_safeguard(api_client: TestClient):
    """Verify candidate matching evaluates skills and preserves Bearing Fault Diagnosis at position 2."""
    # Create and analyze JD
    create_resp = api_client.post(
        "/api/v1/job-descriptions",
        json={"raw_text": SAMPLE_SWE_JD, "profile_id": "sujal"},
    )
    jd_id = create_resp.json()["id"]

    # Perform matching for Sujal
    match_resp = api_client.get(f"/api/v1/job-descriptions/{jd_id}/match?profile_id=sujal")
    assert match_resp.status_code == 200
    match_data = match_resp.json()

    assert match_data["candidate_slug"] == "sujal"
    assert match_data["overall_match_percentage"] > 0
    assert len(match_data["matched_skills"]) > 0

    recommended = match_data["recommended_projects"]
    assert len(recommended) <= 4

    # CRITICAL SAFEGUARD: Slot #2 (index 1) must be Bearing Fault Diagnosis and pinned
    slot_2 = recommended[1]
    assert slot_2["is_fixed"] is True
    assert slot_2["fixed_position"] == 2
    assert "bearing" in slot_2["title"].lower()
    assert "pinned safeguard" in slot_2["ranking_explanation"].lower()

    # Verify component score breakdown (45% skills, 25% responsibilities, 20% stack, 10% domain)
    breakdown = slot_2["score_breakdown"]
    assert "required_skills_weight_45" in breakdown
    assert "responsibilities_weight_25" in breakdown
    assert "tech_stack_weight_20" in breakdown
    assert "domain_relevance_weight_10" in breakdown


def test_candidate_matching_demo_candidate_dynamic_ranking(api_client: TestClient):
    """Verify demo_candidate has 100% dynamic ranking without forced fixed projects."""
    create_resp = api_client.post(
        "/api/v1/job-descriptions",
        json={"raw_text": SAMPLE_SWE_JD, "profile_id": "demo_candidate"},
    )
    jd_id = create_resp.json()["id"]

    match_resp = api_client.get(f"/api/v1/job-descriptions/{jd_id}/match?profile_id=demo_candidate")
    assert match_resp.status_code == 200
    recommended = match_resp.json()["recommended_projects"]

    # In demo_candidate, no project should be forcibly locked as fixed
    for p in recommended:
        assert p["is_fixed"] is False


# ==============================================================================
# 3. Resume Generation & Human Approval Workflow Tests
# ==============================================================================

def test_resume_generation_and_approval_workflow(api_client: TestClient):
    """Test generating a draft resume, manual editing, approval, and version snapshotting."""
    # 1. Create JD
    jd_resp = api_client.post(
        "/api/v1/job-descriptions",
        json={"raw_text": SAMPLE_SWE_JD, "profile_id": "sujal"},
    )
    jd_id = jd_resp.json()["id"]

    # 2. Generate resume draft
    gen_payload = {
        "profile_id": "sujal",
        "job_description_id": jd_id,
        "resume_title": "Sujal Kadam - FinTech SWE Resume Draft",
        "provider_override": "offline",
    }
    gen_resp = api_client.post("/api/v1/resumes/generate", json=gen_payload)
    assert gen_resp.status_code == 201
    resume = gen_resp.json()
    resume_id = resume["id"]

    assert resume["status"] == "draft"
    assert resume["current_version"] == 1
    assert "editable_manifest" in resume
    manifest = resume["editable_manifest"]
    assert manifest["headline"] != ""
    assert len(manifest["projects"]) == 4

    # Bearing Fault Detection must be at position 2 in manifest
    assert "bearing" in manifest["projects"][1]["title"].lower()

    # 3. Attempting export on draft MUST FAIL with 400 Bad Request
    unapproved_export = api_client.get(f"/api/v1/resumes/{resume_id}/export/pdf")
    assert unapproved_export.status_code == 400
    assert "unapproved resume" in unapproved_export.json()["detail"].lower()

    # 4. Manual edit of draft: update summary
    original_summary = manifest["summary"]
    manifest["summary"] = original_summary + " Tailored for high-scale FinTech systems."
    patch_resp = api_client.patch(
        f"/api/v1/resumes/{resume_id}",
        json={"editable_manifest": manifest},
    )
    assert patch_resp.status_code == 200
    assert "FinTech systems" in patch_resp.json()["editable_manifest"]["summary"]
    # Still version 1 and status draft
    assert patch_resp.json()["current_version"] == 1
    assert patch_resp.json()["status"] == "draft"

    # 5. Approve resume draft
    approve_resp = api_client.post(f"/api/v1/resumes/{resume_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"
    assert approve_resp.json()["approved_version"] == 1

    # Verify status changed to approved
    assert api_client.get(f"/api/v1/resumes/{resume_id}").json()["status"] == "approved"

    # 6. Post-approval edit must create version 2, preserving version 1 immutable!
    manifest["summary"] = original_summary + " Revision 2 with enhanced bullet points."
    revision_resp = api_client.patch(
        f"/api/v1/resumes/{resume_id}",
        json={"editable_manifest": manifest},
    )
    assert revision_resp.status_code == 200
    rev_data = revision_resp.json()
    assert rev_data["current_version"] == 2
    assert rev_data["status"] == "draft"

    # Verify version history contains 2 versions
    versions_resp = api_client.get(f"/api/v1/resumes/{resume_id}/versions")
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 1
    assert versions[1]["version_number"] == 2


def test_prohibited_terms_rejected_on_manual_edit(api_client: TestClient):
    """Verify manual edits that inject candidate prohibited terms are rejected with 400."""
    jd_resp = api_client.post("/api/v1/job-descriptions", json={"raw_text": SAMPLE_SWE_JD, "profile_id": "sujal"})
    jd_id = jd_resp.json()["id"]

    gen_resp = api_client.post(
        "/api/v1/resumes/generate",
        json={"profile_id": "sujal", "job_description_id": jd_id, "provider_override": "offline"},
    )
    resume = gen_resp.json()
    resume_id = resume["id"]
    manifest = resume["editable_manifest"]

    # Inject prohibited term
    manifest["summary"] = "Experienced mechanical engineer transitioning into software engineering."
    bad_edit = api_client.patch(f"/api/v1/resumes/{resume_id}", json={"editable_manifest": manifest})
    assert bad_edit.status_code == 400
    assert "prohibited term" in bad_edit.json()["detail"].lower()


# ==============================================================================
# 4. Document Export & ATS Evaluation Tests
# ==============================================================================

def test_approved_resume_pdf_and_docx_export(api_client: TestClient):
    """Test exporting approved resume to ReportLab A4 PDF and python-docx DOCX."""
    # Generate and approve resume
    jd_resp = api_client.post("/api/v1/job-descriptions", json={"raw_text": SAMPLE_SWE_JD, "profile_id": "sujal"})
    gen_resp = api_client.post(
        "/api/v1/resumes/generate",
        json={"profile_id": "sujal", "job_description_id": jd_resp.json()["id"], "provider_override": "offline"},
    )
    resume_id = gen_resp.json()["id"]
    api_client.post(f"/api/v1/resumes/{resume_id}/approve")

    # 1. Export PDF
    pdf_resp = api_client.get(f"/api/v1/resumes/{resume_id}/export/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000
    assert pdf_resp.content[:4] == b"%PDF"

    # 2. Export DOCX
    docx_resp = api_client.get(f"/api/v1/resumes/{resume_id}/export/docx")
    assert docx_resp.status_code == 200
    assert "openxmlformats" in docx_resp.headers["content-type"]
    assert len(docx_resp.content) > 1000


def test_ats_evaluation_endpoint(api_client: TestClient):
    """Test running deterministic ATS evaluation with 30/50/20 breakdown and disclaimer."""
    jd_resp = api_client.post("/api/v1/job-descriptions", json={"raw_text": SAMPLE_SWE_JD, "profile_id": "sujal"})
    gen_resp = api_client.post(
        "/api/v1/resumes/generate",
        json={"profile_id": "sujal", "job_description_id": jd_resp.json()["id"], "provider_override": "offline"},
    )
    resume_id = gen_resp.json()["id"]

    # Run evaluation
    eval_resp = api_client.post(f"/api/v1/resumes/{resume_id}/evaluate")
    assert eval_resp.status_code == 200
    report = eval_resp.json()

    assert report["overall_score"] > 0
    assert "score_breakdown" in report
    breakdown = report["score_breakdown"]
    assert breakdown["ats_format_compatibility"]["max"] == 30
    assert breakdown["jd_relevance"]["max"] == 50
    assert breakdown["content_quality"]["max"] == 20
    assert "disclaimer" in report
    assert any(term in report["disclaimer"].lower() for term in ["diagnostic", "heuristic", "not an official vendor score"])

    # Retrieve history
    history_resp = api_client.get(f"/api/v1/resumes/{resume_id}/evaluations")
    assert history_resp.status_code == 200
    assert len(history_resp.json()) >= 1


# ==============================================================================
# 5. Isolation & Boundary Tests
# ==============================================================================

def test_cross_profile_job_description_isolation(api_client: TestClient):
    """Verify attempting to generate a resume using another candidate's JD is rejected."""
    # JD belongs to demo_candidate
    jd_resp = api_client.post(
        "/api/v1/job-descriptions",
        json={"raw_text": SAMPLE_SWE_JD, "profile_id": "demo_candidate"},
    )
    jd_id = jd_resp.json()["id"]

    # Sujal attempts to generate resume using demo_candidate's JD
    bad_req = api_client.post(
        "/api/v1/resumes/generate",
        json={"profile_id": "sujal", "job_description_id": jd_id},
    )
    assert bad_req.status_code == 400
    assert "different candidate" in bad_req.json()["detail"].lower()


def test_generate_resume_archived_candidate_rejected(api_client: TestClient):
    """Verify archived candidate profile cannot generate new resumes."""
    # Archive demo_candidate
    api_client.delete("/api/v1/profiles/demo_candidate")

    jd_resp = api_client.post(
        "/api/v1/job-descriptions",
        json={"raw_text": SAMPLE_SWE_JD},
    )
    jd_id = jd_resp.json()["id"]

    resp = api_client.post(
        "/api/v1/resumes/generate",
        json={"profile_id": "demo_candidate", "job_description_id": jd_id},
    )
    assert resp.status_code == 400
    assert "archived" in resp.json()["detail"].lower()


def test_ai_provider_fallback_to_offline_on_failure(api_client: TestClient):
    """Verify provider fallback: if an unknown or failing provider is requested, falls back gracefully."""
    jd_resp = api_client.post("/api/v1/job-descriptions", json={"raw_text": SAMPLE_SWE_JD, "profile_id": "sujal"})
    jd_id = jd_resp.json()["id"]

    # Request an invalid provider; ProviderManager falls back down priority chain to offline
    gen_resp = api_client.post(
        "/api/v1/resumes/generate",
        json={
            "profile_id": "sujal",
            "job_description_id": jd_id,
            "provider_override": "non_existent_mock_provider",
        },
    )
    assert gen_resp.status_code == 201
    assert gen_resp.json()["status"] == "draft"
    assert "editable_manifest" in gen_resp.json()


def test_invalid_identifiers_produce_404(api_client: TestClient):
    """Verify non-existent UUIDs produce 404 Not Found."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    assert api_client.get(f"/api/v1/job-descriptions/{fake_uuid}").status_code == 404
    assert api_client.get(f"/api/v1/resumes/{fake_uuid}").status_code == 404
    assert api_client.get(f"/api/v1/resumes/{fake_uuid}/versions/1").status_code == 404
    assert api_client.get(f"/api/v1/resumes/{fake_uuid}/export/pdf").status_code == 404


def test_database_rollback_on_resume_generation_failure(api_client: TestClient):
    """Verify database remains clean and uncorrupted when generation fails."""
    initial_resumes = api_client.get("/api/v1/resumes").json()["total"]

    # Attempt generate with missing candidate
    bad_req = api_client.post(
        "/api/v1/resumes/generate",
        json={"profile_id": "non_existent_candidate", "job_description_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert bad_req.status_code == 404

    # Total resumes must remain unchanged
    final_resumes = api_client.get("/api/v1/resumes").json()["total"]
    assert final_resumes == initial_resumes

