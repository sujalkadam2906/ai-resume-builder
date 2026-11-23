"""Comprehensive tests for multi-provider AI architecture, adapters, and fallback logic."""

import json
from unittest.mock import MagicMock, patch
import pytest

from resume_builder.ai.provider_manager import ProviderManager
from resume_builder.ai.providers.base import (
    enforce_resume_safeguards,
    extract_json_from_text,
    sanitize_candidate_evidence_for_privacy,
)
from resume_builder.ai.providers.cloudflare_provider import CloudflareProvider
from resume_builder.ai.providers.cohere_provider import CohereProvider
from resume_builder.ai.providers.gemini_provider import GeminiProvider
from resume_builder.ai.providers.groq_provider import GroqProvider
from resume_builder.ai.providers.offline_provider import OfflineProvider
from resume_builder.ai.providers.openrouter_provider import OpenRouterProvider
from resume_builder.ai.structured_schemas import TailoredProject, TailoredResumeContent
from resume_builder.jd_analysis.models import JobDescription, RequirementMatrix
from resume_builder.profile.manager import ProfileManager


@pytest.fixture
def sample_profile_and_projects():
    pm = ProfileManager()
    profile = pm.load_profile()
    projects = pm.load_projects()
    return profile, projects


@pytest.fixture
def sample_jd():
    return JobDescription(
        raw_text="Looking for a Java Spring Boot Engineer with SQL and REST API knowledge",
        company_name="Sample Corp",
        job_title="Java Developer",
        required_skills=["Java", "Spring Boot", "SQL"],
    )


def test_privacy_sanitizer(sample_profile_and_projects):
    profile, _ = sample_profile_and_projects
    sanitized = sanitize_candidate_evidence_for_privacy(profile)

    # Must NOT contain raw contact details
    str_dump = str(sanitized)
    if profile.personal_info.phone:
        assert profile.personal_info.phone not in str_dump
    if profile.personal_info.email:
        assert profile.personal_info.email not in str_dump


def test_enforce_bearing_fault_safeguard_at_position_2(sample_profile_and_projects):
    _, projects = sample_profile_and_projects
    # Simulate a rogue LLM response that put Bearing Fault at slot 1 instead of slot 2
    rogue_projects = [
        TailoredProject(
            project_id="bearing_fault_diagnosis",
            title="Bearing Fault Diagnosis Using Machine Learning",
            subtitle="Python, SVM",
            bullets=["Bullet 1"],
        ),
        TailoredProject(
            project_id="employee_management_api",
            title="Employee Management REST API",
            subtitle="Java, Spring Boot",
            bullets=["Bullet 1"],
        ),
    ]
    rogue_content = TailoredResumeContent(
        professional_headline="Software Engineer",
        professional_summary="Summary text",
        skills_category_order=["Backend & Java"],
        tailored_projects=rogue_projects,
        relevant_certifications=[],
        change_summary_notes=[],
    )

    fixed = enforce_resume_safeguards(rogue_content, projects[:4])
    # Slot 2 (index 1) must be Bearing Fault
    assert "bearing" in fixed.tailored_projects[1].title.lower()


def test_json_extractor():
    raw_markdown = """Here is your output:
```json
{
  "professional_headline": "Java Backend Engineer",
  "professional_summary": "Experienced graduate...",
  "skills_category_order": ["Backend & Java"],
  "tailored_projects": [],
  "relevant_certifications": [],
  "change_summary_notes": []
}
```
Thank you!"""
    extracted = extract_json_from_text(raw_markdown)
    assert extracted.startswith("{") and extracted.endswith("}")
    parsed = json.loads(extracted)
    assert parsed["professional_headline"] == "Java Backend Engineer"


def test_priority_chain_and_override():
    mgr = ProviderManager()
    chain = mgr.get_priority_chain()
    names = [p.name for p in chain]
    # Default order starts with gemini and ends with offline
    assert names[0] == "gemini"
    assert names[-1] == "offline"

    # With user override: groq requested
    groq_chain = mgr.get_priority_chain(requested_provider="groq")
    assert groq_chain[0].name == "groq"


def test_groq_provider_adapter_mock(sample_profile_and_projects, sample_jd):
    profile, projects = sample_profile_and_projects
    provider = GroqProvider()
    provider.api_key = "mock-key-123"

    dummy_response_content = {
        "professional_headline": "Java Backend Engineer | Spring Boot & REST APIs",
        "professional_summary": "B.Tech graduate with strong Java foundation.",
        "skills_category_order": ["Backend & Java", "Databases & SQL"],
        "tailored_projects": [
            {
                "project_id": "employee_management_api",
                "title": "Employee Management REST API",
                "subtitle": "Java, Spring Boot",
                "bullets": ["Developed CRUD endpoints with JUnit tests."],
            },
            {
                "project_id": "bearing_fault_diagnosis",
                "title": "Bearing Fault Diagnosis Using Machine Learning",
                "subtitle": "Python, SVM",
                "bullets": ["Trained SVM classifier with >95% accuracy."],
            },
        ],
        "relevant_certifications": ["Core & Advanced Java"],
        "change_summary_notes": ["Tailored for Java role"],
    }

    mock_http_response = MagicMock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(dummy_response_content)}}]
    }

    with patch("httpx.Client.post", return_value=mock_http_response):
        content, model = provider.generate_tailored_content(
            profile, projects[:4], sample_jd, RequirementMatrix()
        )
        assert "Software Engineer" in content.professional_headline
        assert content.tailored_projects[1].project_id == "bearing_fault_diagnosis"
        assert "groq" in model


def test_cohere_provider_adapter_mock(sample_profile_and_projects, sample_jd):
    profile, projects = sample_profile_and_projects
    provider = CohereProvider()
    provider.api_key = "mock-key-123"

    dummy_response = {
        "professional_headline": "Software Engineer | Java & SQL",
        "professional_summary": "Summary text",
        "skills_category_order": ["Backend & Java"],
        "tailored_projects": [
            {
                "project_id": "employee_management_api",
                "title": "Employee Management REST API",
                "subtitle": "Java, Spring Boot",
                "bullets": ["Developed REST APIs."],
            },
            {
                "project_id": "bearing_fault_diagnosis",
                "title": "Bearing Fault Diagnosis Using Machine Learning",
                "subtitle": "Python, SVM",
                "bullets": ["Bearing fault pipeline."],
            },
        ],
        "relevant_certifications": [],
        "change_summary_notes": [],
    }

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "message": {"content": [{"text": json.dumps(dummy_response)}]}
    }

    with patch("httpx.Client.post", return_value=mock_res):
        content, model = provider.generate_tailored_content(
            profile, projects[:4], sample_jd, RequirementMatrix()
        )
        assert "Software Engineer" in content.professional_headline
        assert "cohere" in model


def test_openrouter_provider_adapter_mock(sample_profile_and_projects, sample_jd):
    profile, projects = sample_profile_and_projects
    provider = OpenRouterProvider()
    provider.api_key = "mock-key-123"

    dummy_response = {
        "professional_headline": "Full-Stack Developer",
        "professional_summary": "Full-stack summary",
        "skills_category_order": ["Backend & Java"],
        "tailored_projects": [
            {
                "project_id": "employee_management_api",
                "title": "Employee Management REST API",
                "subtitle": "Java",
                "bullets": ["API endpoints."],
            },
            {
                "project_id": "bearing_fault_diagnosis",
                "title": "Bearing Fault Diagnosis Using Machine Learning",
                "subtitle": "Python",
                "bullets": ["Vibration sensor analysis."],
            },
        ],
        "relevant_certifications": [],
        "change_summary_notes": [],
    }

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "choices": [{"message": {"content": json.dumps(dummy_response)}}]
    }

    with patch("httpx.Client.post", return_value=mock_res):
        content, model = provider.generate_tailored_content(
            profile, projects[:4], sample_jd, RequirementMatrix()
        )
        assert "Software Engineer" in content.professional_headline
        assert "openrouter" in model


def test_cloudflare_provider_adapter_mock(sample_profile_and_projects, sample_jd):
    profile, projects = sample_profile_and_projects
    provider = CloudflareProvider()
    provider.api_token = "mock-token-123"
    provider.account_id = "mock-acc-123"

    dummy_response = {
        "professional_headline": "Cloud & Software Developer",
        "professional_summary": "Cloud summary",
        "skills_category_order": ["Backend & Java"],
        "tailored_projects": [
            {
                "project_id": "employee_management_api",
                "title": "Employee Management REST API",
                "subtitle": "Java",
                "bullets": ["API endpoints."],
            },
            {
                "project_id": "bearing_fault_diagnosis",
                "title": "Bearing Fault Diagnosis Using Machine Learning",
                "subtitle": "Python",
                "bullets": ["Predictive maintenance."],
            },
        ],
        "relevant_certifications": [],
        "change_summary_notes": [],
    }

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "result": {"response": json.dumps(dummy_response)}
    }

    with patch("httpx.Client.post", return_value=mock_res):
        content, model = provider.generate_tailored_content(
            profile, projects[:4], sample_jd, RequirementMatrix()
        )
        assert "Software Engineer" in content.professional_headline
        assert "cloudflare" in model


def test_fallback_cascade_on_auth_and_rate_limits(sample_profile_and_projects, sample_jd):
    """
    Test that when Gemini fails with 401 or 429, ProviderManager
    seamlessly falls back to Groq or the next active provider.
    """
    profile, projects = sample_profile_and_projects
    mgr = ProviderManager()

    # Mock Gemini failing with 401 Unauthorized
    with patch.object(
        mgr._providers["gemini"],
        "generate_tailored_content",
        side_effect=PermissionError("401 Unauthorized"),
    ):
        # Mock Groq configured and succeeding
        mgr._providers["groq"].api_key = "mock_groq_key"
        mock_groq_content = TailoredResumeContent(
            professional_headline="Groq Tailored SWE",
            professional_summary="Groq summary",
            skills_category_order=["Backend & Java"],
            tailored_projects=[
                TailoredProject(
                    project_id="employee_management_api",
                    title="Employee Management REST API",
                    subtitle="Java",
                    bullets=["Bullet 1"],
                ),
                TailoredProject(
                    project_id="bearing_fault_diagnosis",
                    title="Bearing Fault Diagnosis Using Machine Learning",
                    subtitle="Python",
                    bullets=["Bullet 2"],
                ),
            ],
            relevant_certifications=[],
            change_summary_notes=[],
        )
        with patch.object(
            mgr._providers["groq"],
            "generate_tailored_content",
            return_value=(mock_groq_content, "groq/llama-3.3-70b-versatile"),
        ):
            content, provider_name, model_str = mgr.generate(
                profile, projects[:4], sample_jd, RequirementMatrix()
            )
            assert provider_name == "Groq"
            assert "groq" in model_str
            assert content.professional_headline == "Groq Tailored SWE"


def test_complete_fallback_to_offline_when_all_fail(sample_profile_and_projects, sample_jd):
    profile, projects = sample_profile_and_projects
    mgr = ProviderManager()

    # Make all online providers raise an exception
    for name in ["gemini", "groq", "cohere", "openrouter", "cloudflare"]:
        if name in mgr._providers:
            mgr._providers[name].is_configured = MagicMock(return_value=True)
            mgr._providers[name].generate_tailored_content = MagicMock(
                side_effect=RuntimeError("Simulated Provider Outage")
            )

    content, provider_name, model_str = mgr.generate(
        profile, projects[:4], sample_jd, RequirementMatrix()
    )
    assert provider_name == "Offline Python Engine"
    assert "offline" in model_str
    assert content.tailored_projects[1].project_id == "bearing_fault_diagnosis"
