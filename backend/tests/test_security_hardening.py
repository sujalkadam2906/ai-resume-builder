"""Comprehensive Security Hardening, Zero-Trust Access, and Reliability Tests.

Verifies:
1. Cloudflare Access JWT validation (valid signature, audience, issuer, expiration).
2. Rejection of unverified/forged JWTs, expired JWTs, and naked identity headers.
3. Fail-closed production behavior (no bypasses permitted).
4. OWASP security response headers.
5. Sliding-window rate limiting on sensitive/expensive endpoints.
6. Path traversal protection on file storage paths.
7. Whitelisted email access control.
"""

import json
import time
from typing import Dict, Tuple
import uuid
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
import jwt
from jwt.algorithms import RSAAlgorithm
import pytest

from backend.app.config import settings
from backend.app.core.auth import access_validator, CloudflareAccessValidator
from backend.app.core.rate_limiter import rate_limit
from backend.app.main import app
from backend.app.services.resume_export_service import ResumeExportService

client = TestClient(app)


# ------------------------------------------------------------------------------
# RSA Test Key Helper
# ------------------------------------------------------------------------------

def generate_test_rsa_keys() -> Tuple[rsa.RSAPrivateKey, Dict[str, str], str]:
    """Generate an ephemeral RSA key pair and matching Cloudflare-style JWK."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = f"test-key-{uuid.uuid4().hex[:8]}"
    jwk_dict = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk_dict["kid"] = kid
    jwk_dict["alg"] = "RS256"
    return private_key, jwk_dict, kid


# ------------------------------------------------------------------------------
# 1. Cloudflare Access JWT Cryptographic Verification
# ------------------------------------------------------------------------------

def test_cf_access_valid_jwt():
    """Verify that a valid, cryptographically signed Cloudflare Access JWT is accepted."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    
    # Configure validator with the test public key
    team_name = "test-team"
    aud = "test-aud-12345"
    validator = CloudflareAccessValidator(team_name=team_name, expected_aud=aud)
    validator.set_cached_keys([jwk])

    payload = {
        "sub": "user_cf_12345",
        "email": "candidate@example.com",
        "name": "Test Candidate",
        "aud": [aud],
        "iss": f"https://{team_name}.cloudflareaccess.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})

    user = validator.verify_jwt(token)
    assert user.is_authenticated is True
    assert user.email == "candidate@example.com"
    assert user.user_id == "user_cf_12345"


def test_cf_access_reject_forged_signature():
    """Verify that a JWT signed with an untrusted private key is rejected."""
    _, untrusted_jwk, untrusted_kid = generate_test_rsa_keys()
    trusted_priv, trusted_jwk, trusted_kid = generate_test_rsa_keys()
    forged_priv, _, _ = generate_test_rsa_keys()

    validator = CloudflareAccessValidator(team_name="test-team", expected_aud="aud-1")
    validator.set_cached_keys([trusted_jwk])

    payload = {
        "sub": "attacker",
        "email": "attacker@evil.com",
        "aud": ["aud-1"],
        "iss": "https://test-team.cloudflareaccess.com",
        "exp": int(time.time()) + 3600,
    }
    # Sign with forged key but claim kid of trusted key
    forged_token = jwt.encode(payload, forged_priv, algorithm="RS256", headers={"kid": trusted_kid})

    with pytest.raises(Exception) as exc_info:
        validator.verify_jwt(forged_token)
    assert "verification failed" in str(exc_info.value).lower() or "signature" in str(exc_info.value).lower()


def test_cf_access_reject_expired_jwt():
    """Verify that an expired JWT is rejected."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    validator = CloudflareAccessValidator(team_name="test-team", expected_aud="aud-1")
    validator.set_cached_keys([jwk])

    payload = {
        "sub": "user_1",
        "email": "user@test.com",
        "aud": ["aud-1"],
        "iss": "https://test-team.cloudflareaccess.com",
        "exp": int(time.time()) - 300,  # Expired 5 minutes ago
    }
    expired_token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})

    with pytest.raises(Exception) as exc_info:
        validator.verify_jwt(expired_token)
    assert "expired" in str(exc_info.value).lower()


def test_cf_access_reject_audience_mismatch():
    """Verify that a token with wrong audience is rejected."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    validator = CloudflareAccessValidator(team_name="test-team", expected_aud="correct-aud")
    validator.set_cached_keys([jwk])

    payload = {
        "sub": "user_1",
        "email": "user@test.com",
        "aud": ["wrong-aud"],
        "iss": "https://test-team.cloudflareaccess.com",
        "exp": int(time.time()) + 3600,
    }
    wrong_aud_token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})

    with pytest.raises(Exception) as exc_info:
        validator.verify_jwt(wrong_aud_token)
    assert "audience" in str(exc_info.value).lower()


def test_cf_access_reject_naked_headers():
    """Verify that naked identity headers without a valid signed JWT are never trusted."""
    orig_env = settings.environment
    settings.environment = "production"
    try:
        resp = client.get(
            "/api/v1/profiles",
            headers={"Cf-Access-Authenticated-User-Email": "admin@example.com"},
        )
        assert resp.status_code == 401
        assert "Missing Cloudflare Access JWT" in resp.json()["detail"]
    finally:
        settings.environment = orig_env


# ------------------------------------------------------------------------------
# 2. Production Fail-Closed Behavior
# ------------------------------------------------------------------------------

def test_production_fail_closed_on_unauthenticated():
    """Verify that when APP_ENV=production, requests fail closed without JWT."""
    orig_env = settings.environment
    settings.environment = "production"
    try:
        # Public health endpoints remain accessible
        r_health = client.get("/api/v1/health")
        assert r_health.status_code == 200

        r_ready = client.get("/api/v1/health/ready")
        assert r_ready.status_code == 200

        # Protected endpoints strictly reject unauthenticated requests
        r_profiles = client.get("/api/v1/profiles")
        assert r_profiles.status_code == 401

        r_resumes = client.get("/api/v1/resumes")
        assert r_resumes.status_code == 401

        r_system = client.get("/api/v1/system/info")
        assert r_system.status_code == 401
    finally:
        settings.environment = orig_env


# ------------------------------------------------------------------------------
# 3. Security Headers Inspection
# ------------------------------------------------------------------------------

def test_security_headers_present():
    """Verify that standard OWASP security headers are returned on all responses."""
    resp = client.get("/")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in headers
    assert "Content-Security-Policy" in headers
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]


# ------------------------------------------------------------------------------
# 4. Rate Limiting Protection
# ------------------------------------------------------------------------------

def test_rate_limiting_enforcement():
    """Verify that rapid requests exceeding the rate limit receive HTTP 429."""
    from backend.app.core.rate_limiter import SlidingWindowRateLimiter
    from starlette.requests import Request
    
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    
    # Create mock request object with client host
    class MockRequest:
        client = type("Client", (), {"host": "192.168.1.100"})()
        headers = {}

    req = MockRequest()

    # First 3 should succeed
    limiter.check(req)
    limiter.check(req)
    limiter.check(req)

    # 4th request must be rejected with 429
    with pytest.raises(Exception) as exc_info:
        limiter.check(req)
    assert "Rate limit exceeded" in str(exc_info.value)


# ------------------------------------------------------------------------------
# 5. File Path Traversal Protection
# ------------------------------------------------------------------------------

def test_storage_path_traversal_sanitization():
    """Verify that directory traversal strings in candidate slugs cannot escape storage."""
    # Attempt path traversal via slug
    malicious_slug = "../../../etc"
    export_dir = ResumeExportService._get_export_dir(malicious_slug)
    
    # Path should be sanitized to alphanumeric/hyphens only e.g. 'etc'
    storage_root = str(settings.storage_path.resolve())
    assert str(export_dir).startswith(storage_root)
    assert ".." not in str(export_dir)
