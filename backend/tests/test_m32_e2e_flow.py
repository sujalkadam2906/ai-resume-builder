"""End-to-end validation test for Milestone 3.2: Complete Resume Workspace Lifecycle.

Tests:
1. Candidate profile retrieval and verification.
2. Job description creation and requirements analysis.
3. Candidate matching with 45/25/20/10 project ranking & Bearing Fault safeguard.
4. Resume generation draft creation via API.
5. Verification of 4-project limit and Bearing Fault Diagnosis in slot #2 for Sujal.
6. Attempted export of draft resume -> must fail with 400 Bad Request.
7. Manual editing of resume draft manifest -> success.
8. Human approval transition -> locks version #1.
9. Approved export -> ReportLab PDF and python-docx DOCX successfully generated and non-empty.
10. Editing approved resume -> must increment version to v2 and return status to draft!
11. Version immutability check: v1 snapshot remains preserved and intact.
12. Deterministic ATS evaluation execution and scoring.
"""

import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.base import Base
from backend.app.database.session import get_db
from backend.app.main import app
from backend.app.models.candidate import CandidateProfile
from backend.app.models.resume import JobDescription, Resume, ResumeVersion, ATSEvaluation
from backend.app.services.profile_ingestion import ProfileIngestionService


@pytest.fixture(autouse=True)
def setup_isolated_test_db():
    """Isolate E2E test with in-memory database pre-seeded with sujal and demo_candidate."""
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
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

def test_m32_complete_end_to_end_workflow():
    print("=== STARTING MILESTONE 3.2 END-TO-END WORKFLOW TEST ===")

    # 1. Candidate Profile Check
    resp = client.get("/api/v1/profiles/sujal")
    assert resp.status_code == 200, f"Profile fetch failed: {resp.text}"
    profile_data = resp.json()
    assert profile_data["slug"] == "sujal"
    assert profile_data["is_synthetic"] is False
    print("✓ Step 1: Candidate profile 'sujal' verified.")

    # 2. Ingest a target Job Description
    jd_payload = {
        "job_title": "Full Stack Software Engineer",
        "company_name": "Razorpay Payments",
        "raw_text": """
        Razorpay is looking for a Software Engineer with expertise in Python, Java, FastAPI,
        and PostgreSQL. You will design distributed payment services, optimize database queries,
        and implement automated tests. Experience with Docker, Redis, and Machine Learning is a plus.
        Responsibilities include high-throughput transaction processing, API latency reduction,
        and building scalable microservices.
        """,
        "profile_id": "sujal",
        "source_url": "https://careers.razorpay.com/jobs/full-stack-engineer"
    }
    resp = client.post("/api/v1/job-descriptions", json=jd_payload)
    assert resp.status_code == 201, f"JD creation failed: {resp.text}"
    jd_data = resp.json()
    jd_id = jd_data["id"]
    print(f"✓ Step 2: Target Job Description created (ID: {jd_id}).")

    # 3. Analyze Job Description & Match Candidate
    resp = client.post(f"/api/v1/job-descriptions/{jd_id}/analyze?profile_id=sujal")
    assert resp.status_code == 200, f"JD analyze failed: {resp.text}"
    analysis = resp.json()
    assert len(analysis["required_skills"]) > 0
    print(f"✓ Step 3a: JD requirements extracted ({len(analysis['required_skills'])} skills).")

    resp = client.get(f"/api/v1/job-descriptions/{jd_id}/match?profile_id=sujal")
    assert resp.status_code == 200, f"Match failed: {resp.text}"
    match_data = resp.json()
    assert match_data["overall_match_percentage"] > 0
    recs = match_data["recommended_projects"]
    assert len(recs) == 4, f"Expected 4 recommended projects, got {len(recs)}"
    assert recs[1]["title"] == "Bearing Fault Diagnosis Using Machine Learning", "Sujal slot #2 safeguard violated in match!"
    print(f"✓ Step 3b: Match computed ({round(match_data['overall_match_percentage'])}%). Bearing Fault pinned at pos 2.")

    # 4. Generate Tailored Resume Draft via API
    gen_payload = {
        "profile_id": "sujal",
        "job_description_id": jd_id,
        "provider_override": "offline",
        "resume_title": "Sujal Kadam - Razorpay Full Stack Resume"
    }
    resp = client.post("/api/v1/resumes/generate", json=gen_payload)
    assert resp.status_code == 201, f"Resume generate failed: {resp.text}"
    resume = resp.json()
    resume_id = resume["id"]
    assert resume["status"] == "draft"
    assert resume["current_version"] == 1
    manifest = resume["editable_manifest"]
    assert len(manifest["projects"]) == 4, "Generated resume does not have exactly 4 projects!"
    assert manifest["projects"][1]["title"] == "Bearing Fault Diagnosis Using Machine Learning", "Slot #2 violated in manifest!"
    print(f"✓ Step 4: Tailored resume draft generated (ID: {resume_id}, v1). Pinned safeguard verified.")

    # 5. Export Rejection on Draft Status
    resp = client.get(f"/api/v1/resumes/{resume_id}/export/pdf")
    assert resp.status_code == 400, "Draft PDF export must be rejected with 400!"
    assert "Cannot export unapproved resume" in resp.json()["detail"]
    resp = client.get(f"/api/v1/resumes/{resume_id}/export/docx")
    assert resp.status_code == 400, "Draft DOCX export must be rejected with 400!"
    print("✓ Step 5: Draft PDF and DOCX export correctly rejected with 400 Bad Request.")

    # 6. Manual Manifest Edits
    manifest["headline"] = "Senior Software Development Engineer | Distributed Systems & AI"
    manifest["projects"][0]["bullets"][0] = "Engineered real-time transaction processing microservice achieving 99.99% uptime."
    resp = client.patch(f"/api/v1/resumes/{resume_id}", json={"editable_manifest": manifest})
    assert resp.status_code == 200, f"Edit failed: {resp.text}"
    updated = resp.json()
    assert updated["editable_manifest"]["headline"] == "Senior Software Development Engineer | Distributed Systems & AI"
    assert updated["status"] == "draft"
    assert updated["current_version"] == 1
    print("✓ Step 6: Manual edits applied to draft manifest in place.")

    # 7. Prohibited Terms Rejection Check (e.g. 'mechanical engineer' is prohibited for Sujal)
    invalid_manifest = dict(manifest)
    invalid_manifest["summary"] = "Experienced mechanical engineer transitioning into software engineering."
    resp = client.patch(f"/api/v1/resumes/{resume_id}", json={"editable_manifest": invalid_manifest})
    assert resp.status_code == 400, "Prohibited terms should be rejected with 400!"
    print("✓ Step 7: Prohibited terms injection ('mechanical') safely rejected by backend validator.")

    # 8. Human Approval Workflow
    resp = client.post(f"/api/v1/resumes/{resume_id}/approve")
    assert resp.status_code == 200, f"Approve failed: {resp.text}"
    approval = resp.json()
    assert approval["status"] == "approved"
    assert approval["approved_version"] == 1
    print("✓ Step 8: Human approval granted. Version #1 locked.")

    # 9. PDF and DOCX Export of Approved Resume
    resp = client.get(f"/api/v1/resumes/{resume_id}/export/pdf")
    assert resp.status_code == 200, f"PDF export failed: {resp.status_code}"
    assert len(resp.content) > 1000, "PDF export file is too small or empty!"
    assert resp.headers["content-type"] == "application/pdf"
    
    resp = client.get(f"/api/v1/resumes/{resume_id}/export/docx")
    assert resp.status_code == 200, f"DOCX export failed: {resp.status_code}"
    assert len(resp.content) > 1000, "DOCX export file is too small or empty!"
    print(f"✓ Step 9: Export successful. PDF ({len(resp.content)} bytes) & DOCX verified.")

    # 10. Edit Approved Resume -> Version Increment & Draft Transition
    modified_manifest = dict(manifest)
    modified_manifest["summary"] = "Full Stack Engineer specializing in robust, fault-tolerant payment architecture."
    resp = client.patch(f"/api/v1/resumes/{resume_id}", json={"editable_manifest": modified_manifest})
    assert resp.status_code == 200, f"Post-approval edit failed: {resp.text}"
    post_edit = resp.json()
    assert post_edit["current_version"] == 2, "Editing approved resume must increment version to 2!"
    assert post_edit["status"] == "draft", "Editing approved resume must revert status to draft!"
    print("✓ Step 10: Editing approved resume created new Draft Version #2.")

    # 11. Version Immutability Check
    resp = client.get(f"/api/v1/resumes/{resume_id}/versions")
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2, f"Expected 2 version snapshots, got {len(versions)}"
    assert versions[0]["version_number"] == 1
    assert versions[1]["version_number"] == 2
    # Check v1 snapshot still has the v1 summary
    assert versions[0]["manifest_snapshot"]["summary"] != modified_manifest["summary"]
    print("✓ Step 11: Version immutability verified. v1 snapshot preserved unchanged.")

    # 12. ATS Heuristic Evaluation
    resp = client.post(f"/api/v1/resumes/{resume_id}/evaluate")
    assert resp.status_code == 200, f"ATS evaluate failed: {resp.text}"
    ats_eval = resp.json()
    assert 0 <= ats_eval["overall_score"] <= 100
    assert ats_eval["format_score"] is not None
    assert ats_eval["relevance_score"] is not None
    assert ats_eval["quality_score"] is not None
    assert "heuristic" in ats_eval["disclaimer"].lower() or "estimate" in ats_eval["disclaimer"].lower()
    print(f"✓ Step 12: ATS evaluation completed ({ats_eval['overall_score']} pts: Rel {ats_eval['relevance_score']}, Fmt {ats_eval['format_score']}, Qual {ats_eval['quality_score']}).")

    print("\n=== ALL 12 END-TO-END WORKFLOW ACCEPTANCE CRITERIA PASSED! ===")

if __name__ == "__main__":
    run_e2e_test()
