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
        "email_confirmed_at": "2024-01-01T00:00:00Z",
        "user_metadata": {"full_name": "Test Candidate"},
        "aud": aud,
        "iss": f"{supabase_url}/auth/v1",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})

    orig_signup = settings.allow_public_signup
    settings.allow_public_signup = True
    try:
        user = validator.verify_jwt(token)
        assert user.is_authenticated is True
        assert user.email == "candidate@example.com"
        assert user.user_id == "00000000-0000-0000-0000-000000000001"
        assert user.name == "Test Candidate"
    finally:
        settings.allow_public_signup = orig_signup


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
        "email_confirmed_at": "2024-01-01T00:00:00Z",
        "aud": aud,
        "iss": f"{supabase_url}/auth/v1",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, priv_key, algorithm="ES256", headers={"kid": kid})

    orig_signup = settings.allow_public_signup
    settings.allow_public_signup = True
    try:
        user = validator.verify_jwt(token)
        assert user.is_authenticated is True
        assert user.email == "ecuser@example.com"
        assert user.user_id == "00000000-0000-0000-0000-000000000002"
    finally:
        settings.allow_public_signup = orig_signup


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
    orig_signup = settings.allow_public_signup
    settings.allow_public_signup = False
    settings.allowed_emails = ["authorized@example.com"]
    try:
        payload = {
            "sub": "user_unauthorized",
            "email": "unauthorized@example.com",
            "email_confirmed_at": "2024-01-01T00:00:00Z",
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
        settings.allow_public_signup = orig_signup


def test_supabase_public_signup_permits_ordinary_users():
    """Verify that in Public SaaS mode (allow_public_signup=True), ordinary registered users are permitted."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    supabase_url = "https://xyzcompany.supabase.co"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud="authenticated")
    validator.set_cached_keys([jwk])

    orig_allowed = settings.allowed_emails
    orig_signup = settings.allow_public_signup
    settings.allow_public_signup = True
    settings.allowed_emails = ["operator@example.com"]  # Operator allowlist should not block registered public users
    try:
        payload = {
            "sub": str(uuid.uuid4()),
            "email": "ordinary_new_user@example.com",
            "email_confirmed_at": "2024-01-01T00:00:00Z",
            "aud": "authenticated",
            "iss": f"{supabase_url}/auth/v1",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})
        user = validator.verify_jwt(token)
        assert user.email == "ordinary_new_user@example.com"
        assert user.is_authenticated is True
    finally:
        settings.allowed_emails = orig_allowed
        settings.allow_public_signup = orig_signup


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

def test_production_fail_closed_on_unauthenticated(monkeypatch):
    """Verify that when APP_ENV=production, requests fail closed without valid Bearer JWT."""
    import backend.app.api.v1.endpoints.health as health_mod
    monkeypatch.setattr(health_mod, "check_db_connection", lambda: (False, "Database connection timed out"))

    orig_env = settings.environment
    settings.environment = "production"
    try:
        # Public health endpoints remain accessible
        r_health = client.get("/api/v1/health")
        assert r_health.status_code == 200

        # Readiness probe returns 503 when DB is unreachable (mocked to prevent network hang)
        r_ready = client.get("/api/v1/health/ready")
        assert r_ready.status_code == 503
        body = r_ready.json()
        assert "checks" in body
        # Ensure no sensitive data (connection strings) is leaked
        assert "database_url" not in str(body).lower()
        assert "@" not in str(body.get("checks", {}).get("database", {}))

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


# ------------------------------------------------------------------------------
# 6. Email Verification, Signup Controls, Health Separation & Input Bounds
# ------------------------------------------------------------------------------

def test_supabase_standard_jwt_without_email_confirmed_claim():
    """Standard Supabase access tokens omit email_confirmed_at; verify_jwt accepts them when authorized."""
    priv_key, jwk, kid = generate_test_rsa_keys()
    supabase_url = "https://xyzcompany.supabase.co"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud="authenticated")
    validator.set_cached_keys([jwk])

    orig_allowed = settings.allowed_emails
    settings.allowed_emails = ["verified@example.com"]
    try:
        payload = {
            "sub": str(uuid.uuid4()),
            "email": "verified@example.com",
            "aud": "authenticated",
            "iss": f"{supabase_url}/auth/v1",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})
        user = validator.verify_jwt(token)
        assert user.email == "verified@example.com"
    finally:
        settings.allowed_emails = orig_allowed


def test_supabase_reject_unverified_claims_in_jwt():
    """Explicitly unverified claims (email_verified=False or email_confirmed_at=None) are rejected with 403."""
    from fastapi import HTTPException

    priv_key, jwk, kid = generate_test_rsa_keys()
    supabase_url = "https://xyzcompany.supabase.co"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud="authenticated")
    validator.set_cached_keys([jwk])

    orig_allowed = settings.allowed_emails
    settings.allowed_emails = ["user@example.com"]
    try:
        for extra_claim in [{"email_verified": False}, {"email_confirmed_at": None}]:
            payload = {
                "sub": str(uuid.uuid4()),
                "email": "user@example.com",
                "aud": "authenticated",
                "iss": f"{supabase_url}/auth/v1",
                "exp": int(time.time()) + 3600,
                **extra_claim,
            }
            token = jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})
            with pytest.raises(HTTPException) as exc_info:
                validator.verify_jwt(token)
            assert exc_info.value.status_code == 403
    finally:
        settings.allowed_emails = orig_allowed


def test_db_email_verification_enforcement_on_postgresql():
    """_verify_email_confirmed_in_db rejects unconfirmed users on PostgreSQL and allows confirmed users."""
    from fastapi import HTTPException
    from backend.app.core.auth import AuthenticatedUser, _verify_email_confirmed_in_db

    user = AuthenticatedUser(
        email="user@example.com",
        user_id=str(uuid.uuid4()),
        claims={"sub": "x", "email": "user@example.com"},
    )

    class FakeDialect:
        name = "postgresql"

    class FakeBind:
        dialect = FakeDialect()

    class FakeResult:
        def __init__(self, row):
            self._row = row

        def fetchone(self):
            return self._row

    class FakeSession:
        def __init__(self, row):
            self._row = row

        def get_bind(self):
            return FakeBind()

        def execute(self, *_args, **_kwargs):
            return FakeResult(self._row)

    # Unconfirmed (email_confirmed_at is None) -> 403
    with pytest.raises(HTTPException) as exc_info:
        _verify_email_confirmed_in_db(FakeSession((None,)), user)
    assert exc_info.value.status_code == 403

    # Missing auth.users row -> 403
    with pytest.raises(HTTPException) as exc_info:
        _verify_email_confirmed_in_db(FakeSession(None), user)
    assert exc_info.value.status_code == 403

    # Database query error -> fails closed with 403
    class ErrorSession(FakeSession):
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("Database connection lost")

    with pytest.raises(HTTPException) as exc_info:
        _verify_email_confirmed_in_db(ErrorSession(None), user)
    assert exc_info.value.status_code == 403
    assert "Unable to verify" in exc_info.value.detail

    # Confirmed -> passes
    _verify_email_confirmed_in_db(FakeSession(("2026-01-01T00:00:00Z",)), user)


def test_allowed_emails_matrix_comprehensive():
    """Explicitly verify the 5 ALLOWED_EMAILS & REQUIRE_AUTH configurations requested."""
    from fastapi import HTTPException
    from backend.app.config import WebSettings

    priv_key, jwk, kid = generate_test_rsa_keys()
    supabase_url = "https://xyzcompany.supabase.co"
    validator = SupabaseAuthValidator(supabase_url=supabase_url, expected_aud="authenticated")
    validator.set_cached_keys([jwk])

    def create_token(email: str) -> str:
        payload = {
            "sub": str(uuid.uuid4()),
            "email": email,
            "email_confirmed_at": "2026-01-01T00:00:00Z",
            "aud": "authenticated",
            "iss": f"{supabase_url}/auth/v1",
            "exp": int(time.time()) + 3600,
        }
        return jwt.encode(payload, priv_key, algorithm="RS256", headers={"kid": kid})

    orig_allowed = settings.allowed_emails
    orig_signup = settings.allow_public_signup
    orig_require_auth = settings.require_auth
    orig_env = settings.environment
    try:
        operator_token = create_token("operator@example.com")
        stranger_token = create_token("stranger@example.com")

        # 1. REQUIRE_AUTH=true, ALLOW_PUBLIC_SIGNUP=false, ALLOWED_EMAILS contains operator -> operator permitted
        settings.require_auth = True
        settings.allow_public_signup = False
        settings.allowed_emails = ["operator@example.com"]
        op_user = validator.verify_jwt(operator_token)
        assert op_user.email == "operator@example.com"

        # 2. REQUIRE_AUTH=true, ALLOW_PUBLIC_SIGNUP=false, ALLOWED_EMAILS empty -> fail closed (403)
        settings.allowed_emails = []
        with pytest.raises(HTTPException) as exc_2:
            validator.verify_jwt(operator_token)
        assert exc_2.value.status_code == 403
        assert "restricted" in exc_2.value.detail.lower()

        # 3. REQUIRE_AUTH=true, ALLOW_PUBLIC_SIGNUP=false, unlisted user -> denied (403)
        settings.allowed_emails = ["operator@example.com"]
        with pytest.raises(HTTPException) as exc_3:
            validator.verify_jwt(stranger_token)
        assert exc_3.value.status_code == 403
        assert "not authorized" in exc_3.value.detail.lower()

        # 4. ALLOW_PUBLIC_SIGNUP=true -> opens backend auth to all verified identities
        settings.allowed_emails = []
        settings.allow_public_signup = True
        public_user = validator.verify_jwt(stranger_token)
        assert public_user.email == "stranger@example.com"

        # 5. REQUIRE_AUTH=false cannot bypass production: in production environment, settings forces require_auth=True
        prod_settings = WebSettings()
        prod_settings.environment = "production"
        # Simulate environment instantiation
        assert prod_settings.is_production is True
        # Calling __init__ with production environment
        import os
        orig_os_env = os.environ.get("APP_ENV")
        orig_os_auth = os.environ.get("REQUIRE_AUTH")
        try:
            os.environ["APP_ENV"] = "production"
            os.environ["REQUIRE_AUTH"] = "false"  # Attacker tries to disable in prod
            test_prod = WebSettings()
            assert test_prod.require_auth is True  # Forced true
            assert test_prod.allow_dev_auth_bypass is False  # Forced false
        finally:
            if orig_os_env: os.environ["APP_ENV"] = orig_os_env
            else: os.environ.pop("APP_ENV", None)
            if orig_os_auth: os.environ["REQUIRE_AUTH"] = orig_os_auth
            else: os.environ.pop("REQUIRE_AUTH", None)
    finally:
        settings.allowed_emails = orig_allowed
        settings.allow_public_signup = orig_signup
        settings.require_auth = orig_require_auth
        settings.environment = orig_env


def test_health_liveness_and_readiness_separation(monkeypatch):
    """Liveness stays 200 when DB is down; readiness returns 503 when DB is down and 200 when healthy."""
    import backend.app.api.v1.endpoints.health as health_mod

    monkeypatch.setattr(health_mod, "check_db_connection", lambda: (False, "DB down"))
    r_live = client.get("/api/v1/health")
    assert r_live.status_code == 200
    assert r_live.json()["status"] == "healthy"

    r_ready_down = client.get("/api/v1/health/ready")
    assert r_ready_down.status_code == 503
    assert r_ready_down.json()["status"] == "degraded"
    assert r_ready_down.json()["checks"]["database"]["status"] == "error"

    monkeypatch.setattr(health_mod, "check_db_connection", lambda: (True, "Connected"))
    r_ready_up = client.get("/api/v1/health/ready")
    assert r_ready_up.status_code == 200
    assert r_ready_up.json()["status"] == "ready"
    assert r_ready_up.json()["checks"]["database"]["status"] == "ok"


def test_jd_input_size_limit():
    """Verify JobDescriptionCreate rejects oversized raw_text payloads."""
    from pydantic import ValidationError
    from backend.app.schemas.resume import JobDescriptionCreate

    with pytest.raises(ValidationError):
        JobDescriptionCreate(raw_text="x" * 50001)
