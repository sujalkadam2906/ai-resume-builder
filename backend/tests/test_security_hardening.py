"""Comprehensive Security Hardening, Zero-Trust Access, and Reliability Tests.

Verifies:
1. Supabase JWT validation (valid signature, audience, issuer, expiration, key ID).
2. Support for RSA and EC (ECDSA) asymmetric signing keys via JWKS.
3. Rejection of unverified/forged JWTs, expired JWTs, wrong audience, and naked identity headers.
4. Fail-closed production behavior (no bypasses permitted).
5. OWASP security response headers.
6. Sliding-window rate limiting on sensitive/expensive endpoints.
7. Path traversal protection on file storage paths.
8. Whitelisted email access control (ALLOWED_EMAILS).
"""

import json
import time
from typing import Dict, Tuple
import uuid
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from fastapi.testclient import TestClient
import jwt
from jwt.algorithms import RSAAlgorithm, ECAlgorithm
import pytest

from backend.app.config import settings
from backend.app.core.auth import auth_validator, SupabaseAuthValidator
from backend.app.core.rate_limiter import rate_limit
from backend.app.main import app
from backend.app.services.resume_export_service import ResumeExportService

client = TestClient(app)


# ------------------------------------------------------------------------------
# Asymmetric Test Key Helpers
# ------------------------------------------------------------------------------

def generate_test_rsa_keys() -> Tuple[rsa.RSAPrivateKey, Dict[str, str], str]:
    """Generate an ephemeral RSA key pair and matching JWK."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = f"test-rsa-{uuid.uuid4().hex[:8]}"
    jwk_dict = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk_dict["kid"] = kid
    jwk_dict["alg"] = "RS256"
    return private_key, jwk_dict, kid


def generate_test_ec_keys() -> Tuple[ec.EllipticCurvePrivateKey, Dict[str, str], str]:
    """Generate an ephemeral EC (P-256) key pair and matching JWK."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    kid = f"test-ec-{uuid.uuid4().hex[:8]}"
    jwk_dict = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
    jwk_dict["kid"] = kid
    jwk_dict["alg"] = "ES256"
    return private_key, jwk_dict, kid


# ------------------------------------------------------------------------------
# 1. Supabase JWT Cryptographic Verification (RSA and EC)
# ------------------------------------------------------------------------------

def test_supabase_valid_rsa_jwt():
    """Verify that a valid, cryptographically signed Supabase RSA JWT is accepted."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    
    supabase_url = "https://xyzcompany.supabase.co"
    aud = "authenticated"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud=aud)
    validator.set_cached_keys([jwk])

    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "email": "candidate@example.com",
        "user_metadata": {"full_name": "Test Candidate"},
        "aud": aud,
        "iss": f"{supabase_url}/auth/v1",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})

    user = validator.verify_jwt(token)
    assert user.is_authenticated is True
    assert user.email == "candidate@example.com"
    assert user.user_id == "00000000-0000-0000-0000-000000000001"
    assert user.name == "Test Candidate"


def test_supabase_valid_ec_jwt():
    """Verify that a valid Supabase ES256 (ECDSA) JWT is accepted."""
    priv_key, jwk, kid = generate_test_ec_keys()

    supabase_url = "https://xyzcompany.supabase.co"
    aud = "authenticated"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud=aud)
    validator.set_cached_keys([jwk])

    payload = {
        "sub": "00000000-0000-0000-0000-000000000002",
        "email": "ecuser@example.com",
        "aud": aud,
        "iss": f"{supabase_url}/auth/v1",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, priv_key, algorithm="ES256", headers={"kid": kid})

    user = validator.verify_jwt(token)
    assert user.is_authenticated is True
    assert user.email == "ecuser@example.com"
    assert user.user_id == "00000000-0000-0000-0000-000000000002"


def test_supabase_reject_forged_signature():
    """Verify that a JWT signed with an untrusted private key is rejected."""
    _, untrusted_jwk, untrusted_kid = generate_test_rsa_keys()
    trusted_priv, trusted_jwk, trusted_kid = generate_test_rsa_keys()
    forged_priv, _, _ = generate_test_rsa_keys()

    supabase_url = "https://xyzcompany.supabase.co"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud="authenticated")
    validator.set_cached_keys([trusted_jwk])

    payload = {
        "sub": "attacker",
        "email": "attacker@evil.com",
        "aud": "authenticated",
        "iss": f"{supabase_url}/auth/v1",
        "exp": int(time.time()) + 3600,
    }
    # Sign with forged key but claim kid of trusted key
    forged_token = jwt.encode(payload, forged_priv, algorithm="RS256", headers={"kid": trusted_kid})

    with pytest.raises(Exception) as exc_info:
        validator.verify_jwt(forged_token)
    assert "verification failed" in str(exc_info.value).lower() or "signature" in str(exc_info.value).lower()


def test_supabase_reject_expired_jwt():
    """Verify that an expired Supabase JWT is rejected."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    supabase_url = "https://xyzcompany.supabase.co"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud="authenticated")
    validator.set_cached_keys([jwk])

    payload = {
        "sub": "user_1",
        "email": "user@test.com",
        "aud": "authenticated",
        "iss": f"{supabase_url}/auth/v1",
        "exp": int(time.time()) - 300,  # Expired 5 minutes ago
    }
    expired_token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})

    with pytest.raises(Exception) as exc_info:
        validator.verify_jwt(expired_token)
    assert "expired" in str(exc_info.value).lower()


def test_supabase_reject_audience_mismatch():
    """Verify that a token with wrong audience is rejected."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    supabase_url = "https://xyzcompany.supabase.co"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud="authenticated")
    validator.set_cached_keys([jwk])

    payload = {
        "sub": "user_1",
        "email": "user@test.com",
        "aud": "wrong-audience",
        "iss": f"{supabase_url}/auth/v1",
        "exp": int(time.time()) + 3600,
    }
    wrong_aud_token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})

    with pytest.raises(Exception) as exc_info:
        validator.verify_jwt(wrong_aud_token)
    assert "audience" in str(exc_info.value).lower()


def test_supabase_reject_unauthorized_email():
    """Verify that an authenticated user not in ALLOWED_EMAILS is rejected with 403."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    supabase_url = "https://xyzcompany.supabase.co"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud="authenticated")
    validator.set_cached_keys([jwk])

    orig_allowed = settings.allowed_emails
    settings.allowed_emails = ["authorized@example.com"]
    try:
        payload = {
            "sub": "user_unauthorized",
            "email": "unauthorized@example.com",
            "aud": "authenticated",
            "iss": f"{supabase_url}/auth/v1",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})
        with pytest.raises(Exception) as exc_info:
            validator.verify_jwt(token)
        assert "not authorized" in str(exc_info.value).lower() or "403" in str(exc_info.value)
    finally:
        settings.allowed_emails = orig_allowed


def test_supabase_reject_naked_headers():
    """Verify that naked identity headers without a valid signed Bearer JWT are never trusted."""
    orig_env = settings.environment
    settings.environment = "production"
    try:
        resp = client.get(
            "/api/v1/profiles",
            headers={"X-User-Email": "admin@example.com", "Cf-Access-Authenticated-User-Email": "admin@example.com"},
        )
        assert resp.status_code == 401
        assert "Missing Bearer token" in resp.json()["detail"]
    finally:
        settings.environment = orig_env


# ------------------------------------------------------------------------------
# 2. Production Fail-Closed Behavior
# ------------------------------------------------------------------------------

def test_production_fail_closed_on_unauthenticated():
    """Verify that when APP_ENV=production, requests fail closed without valid Bearer JWT."""
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
    
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    
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
    malicious_slug = "../../../etc"
    export_dir = ResumeExportService._get_export_dir(malicious_slug)
    
    storage_root = str(settings.storage_path.resolve())
    assert str(export_dir).startswith(storage_root)
    assert ".." not in str(export_dir)
