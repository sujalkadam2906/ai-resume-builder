"""Unit tests for Gemini fallback logic, error handling, and offline generator."""

import pytest
from unittest.mock import MagicMock
from resume_builder.ai.fallback import classify_error, execute_with_fallback, InvalidAPIKeyError
from resume_builder.ai.gemini_client import generate_offline_content
from resume_builder.jd_analysis.models import JobDescription, RequirementMatrix
from resume_builder.profile.manager import ProfileManager
from resume_builder.project_selection.selector import select_projects_for_jd


def test_classify_errors():
    err_401 = Exception("401 Unauthorized: API key invalid")
    err_404 = Exception("404 Not Found: Model gemini-4-carbon does not exist")
    err_429 = Exception("429 Resource has been exhausted (e.g. check quota).")
    err_500 = Exception("500 Internal Server Error")

    assert classify_error(err_401)[0] == "AUTH_ERROR"
    assert classify_error(err_404)[0] == "MODEL_NOT_FOUND"
    assert classify_error(err_429)[0] == "QUOTA_EXHAUSTED"
    assert classify_error(err_500)[0] == "SERVER_ERROR"


def test_offline_deterministic_generator():
    pm = ProfileManager()
    profile = pm.load_profile()
    projects = pm.load_projects()

    jd = JobDescription(
        raw_text="Java Spring Boot Backend Engineer",
        company_name="InnovateTech",
        job_title="Java Backend Developer",
        required_skills=["Java", "Spring Boot", "SQL"],
    )
    selected, _, _ = select_projects_for_jd(projects, jd, target_count=4)
    req_matrix = RequirementMatrix()

    content = generate_offline_content(profile, selected, jd, req_matrix)
    assert "Java" in content.professional_headline
    assert len(content.tailored_projects) == 4
    # Slot 2 must be Bearing Fault
    assert "bearing" in content.tailored_projects[1].title.lower()


def test_execute_with_fallback_skips_unavailable_model():
    candidates = ["model-nonexistent", "model-valid"]
    mock_client = MagicMock()

    def fake_call(model_name: str):
        if model_name == "model-nonexistent":
            raise Exception("404 Model not found")
        return {"status": "ok"}

    result, active_model = execute_with_fallback(
        client=mock_client,
        candidate_models=candidates,
        call_fn=fake_call,
        max_retries=1,
    )
    assert active_model == "model-valid"
    assert result == {"status": "ok"}
