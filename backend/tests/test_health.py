"""Tests for FastAPI health and system endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["version"] == "1.0.0"
    assert "/docs" in data["docs"]


def test_liveness_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_readiness_probe_endpoint():
    response = client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "checks" in data
    assert "storage" in data["checks"]
    assert data["checks"]["storage"]["status"] == "ok"
    assert "resume_engine" in data["checks"]
    assert data["checks"]["resume_engine"]["status"] == "ok"


def test_system_info_endpoint():
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "python_version" in data
    assert "platform" in data
    assert data["app_version"] == "1.0.0"


def test_ai_providers_status_endpoint():
    response = client.get("/api/v1/system/providers")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "primary_provider" in data
    assert "providers" in data
    assert len(data["providers"]) >= 1

    # Ensure no secret API keys are leaked in response
    serialized = response.text
    assert "AIza" not in serialized
    assert "gsk_" not in serialized
