"""Supabase JWT Authentication & Identity Enforcement.

Provides:
- Cryptographic verification of Bearer JWT tokens using Supabase JWKS.
- Flexible algorithm support: Asymmetric (RS256, ES256, EdDSA) via JWKS.
- Strict claim validation: 'aud' (Audience), 'iss' (Supabase project auth issuer), 'exp' (Expiration), 'sub' (User ID).
- Absolute rejection of naked/unverified client identity headers.
- Production fail-closed enforcement (no bypasses permitted when APP_ENV=production).
- Authorization gating against configured allowed user emails (ALLOWED_EMAILS).
"""

import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm, ECAlgorithm
from pydantic import BaseModel, Field

from backend.app.config import settings

logger = logging.getLogger("resume_builder.security.auth")

http_bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """Authenticated user context extracted from cryptographically verified claims."""
    email: str
    user_id: str
    name: Optional[str] = None
    is_authenticated: bool = True
    roles: List[str] = Field(default_factory=lambda: ["user"])
    claims: Dict[str, Any] = Field(default_factory=dict)


# Supported asymmetric signing algorithms
ALLOWED_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "EdDSA"]


class SupabaseAuthValidator:
    """Validator for Supabase JWT assertions using JWKS."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        expected_aud: Optional[str] = None,
        cache_ttl_seconds: int = 3600,
    ):
        self.supabase_url = (supabase_url or settings.supabase_url).rstrip("/")
        self.expected_aud = expected_aud or settings.supabase_jwt_aud
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cached_keys: Dict[str, Any] = {}
        self._last_fetch: float = 0.0

    @property
    def expected_issuer(self) -> str:
        """Expected JWT issuer string for Supabase Auth."""
        if not self.supabase_url:
            return ""
        return f"{self.supabase_url}/auth/v1"

    @property
    def certs_url(self) -> str:
        """Supabase public keys/JWKS endpoint."""
        if not self.supabase_url:
            return ""
        return f"{self.supabase_url}/auth/v1/.well-known/jwks.json"

    def _parse_jwk(self, key_dict: Dict[str, Any]) -> Any:
        """Parse JWK dict into a usable public key object based on kty."""
        kty = key_dict.get("kty", "").upper()
        if kty == "RSA":
            return RSAAlgorithm.from_jwk(key_dict)
        elif kty == "EC":
            return ECAlgorithm.from_jwk(key_dict)
        elif kty == "OKP":
            # For Ed25519 / EdDSA if PyJWT / cryptography supports it
            from jwt.algorithms import OKPAlgorithm
            return OKPAlgorithm.from_jwk(key_dict)
        else:
            raise ValueError(f"Unsupported JWK key type: '{kty}'")

    def set_cached_keys(self, jwks_keys: List[Dict[str, Any]]) -> None:
        """Manually populate cached keys (used for test isolation)."""
        self._cached_keys = {}
        for key_dict in jwks_keys:
            kid = key_dict.get("kid")
            if kid:
                try:
                    self._cached_keys[kid] = self._parse_jwk(key_dict)
                except Exception as exc:
                    logger.warning(f"Failed to parse test JWK with kid '{kid}': {exc}")
        self._last_fetch = time.time()

    def fetch_public_keys(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch and cache Supabase public keys from the JWKS endpoint."""
        now = time.time()
        if not force_refresh and self._cached_keys and (now - self._last_fetch < self.cache_ttl_seconds):
            return self._cached_keys

        if not self.certs_url:
            logger.warning("Supabase URL is not configured; cannot fetch JWKS certs.")
            return {}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(self.certs_url)
                if resp.status_code != 200:
                    logger.error(f"Failed to fetch Supabase JWKS certs: HTTP {resp.status_code}")
                    return self._cached_keys

                jwks = resp.json()
                keys = jwks.get("keys", [])
                parsed_keys = {}
                for key_dict in keys:
                    kid = key_dict.get("kid")
                    if kid:
                        try:
                            parsed_keys[kid] = self._parse_jwk(key_dict)
                        except Exception as exc:
                            logger.warning(f"Skipping key {kid}: {exc}")

                self._cached_keys = parsed_keys
                self._last_fetch = now
                logger.info(f"Refreshed {len(parsed_keys)} Supabase public keys from JWKS.")
                return self._cached_keys
        except Exception as exc:
            logger.error(f"Error fetching Supabase JWKS from {self.certs_url}: {exc}")
            return self._cached_keys

    def verify_jwt(self, token: str) -> AuthenticatedUser:
        """
        Cryptographically verify the Supabase JWT.
        Validates:
        - Signature against matching 'kid' public key from Supabase JWKS
        - Allowed asymmetric algorithm (RS256, ES256, etc.)
        - Audience 'aud'
        - Issuer 'iss'
        - Expiration 'exp'
        - Authorized user email (if ALLOWED_EMAILS is configured)
        """
        if not token or not isinstance(token, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or malformed Supabase Bearer token.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        # 1. Inspect unverified header for key ID and algorithm
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid JWT header format: {exc}",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        alg = unverified_header.get("alg")
        if not alg or alg not in ALLOWED_ALGORITHMS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported token algorithm '{alg}'. Accepted algorithms: {', '.join(ALLOWED_ALGORITHMS)}.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT header missing mandatory Key ID ('kid').",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        # 2. Resolve matching public key
        keys = self.fetch_public_keys(force_refresh=False)
        public_key = keys.get(kid)
        if not public_key:
            # Refresh once in case key was recently rotated by Supabase
            keys = self.fetch_public_keys(force_refresh=True)
            public_key = keys.get(kid)

        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unable to locate trusted public key for kid '{kid}'. Token signature rejected.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        # 3. Cryptographically verify signature and standard claims
        try:
            decode_kwargs: Dict[str, Any] = {
                "algorithms": ALLOWED_ALGORITHMS,
                "options": {
                    "require": ["exp", "iss", "aud", "sub"],
                    "verify_exp": True,
                    "verify_iss": True,
                    "verify_aud": True,
                },
            }
            if self.expected_aud:
                decode_kwargs["audience"] = self.expected_aud
            if self.expected_issuer:
                decode_kwargs["issuer"] = self.expected_issuer

            payload = jwt.decode(token, public_key, **decode_kwargs)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase token has expired.",
                headers={"WWW-Authenticate": 'Bearer error="token_expired"'},
            )
        except jwt.InvalidAudienceError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase token audience ('aud') mismatch.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )
        except jwt.InvalidIssuerError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase token issuer ('iss') mismatch.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Supabase token verification failed: {exc}",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        # 4. Extract verified identity claims
        email = payload.get("email")
        if not email and isinstance(payload.get("user_metadata"), dict):
            email = payload["user_metadata"].get("email")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Verified token payload missing email identity claim.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        user_id = str(payload.get("sub", ""))

        # 5. Authorization: Check allowed emails whitelist if configured
        if settings.allowed_emails and email.lower() not in settings.allowed_emails:
            logger.warning(f"Access denied for authenticated user '{email}': not in ALLOWED_EMAILS.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User '{email}' is authenticated but not authorized to access this platform.",
            )

        user_metadata = payload.get("user_metadata") or {}
        name = user_metadata.get("full_name") or user_metadata.get("name") or payload.get("name") or email.split("@")[0]

        return AuthenticatedUser(
            email=email,
            user_id=user_id,
            name=name,
            is_authenticated=True,
            claims=payload,
        )


# Global singleton validator
auth_validator = SupabaseAuthValidator()
# Backward-compatibility alias
CloudflareAccessValidator = SupabaseAuthValidator
access_validator = auth_validator


def get_current_user(
    request: Request,
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_scheme),
) -> AuthenticatedUser:
    """
    FastAPI dependency to authenticate requests.
    Strictly inspects 'Authorization: Bearer <token>' header.
    Never trusts client-supplied identity headers.
    
    Production Fail-Closed Rules:
    - If APP_ENV=production, valid Supabase JWT Bearer token is mandatory.
    - Development bypasses are strictly disallowed in production.
    """
    token = None
    if bearer_credentials and bearer_credentials.credentials:
        token = bearer_credentials.credentials

    # 1. Handle missing token
    if not token:
        if settings.is_production:
            logger.warning(
                f"Unauthorized request to {request.method} {request.url.path} in production: Missing Bearer token."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: Missing Bearer token.",
                headers={"WWW-Authenticate": 'Bearer error="missing_token"'},
            )

        # Development environment handling
        if settings.require_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: REQUIRE_AUTH is enabled.",
                headers={"WWW-Authenticate": 'Bearer error="missing_token"'},
            )

        if settings.allow_dev_auth_bypass:
            # Safe local developer context
            return AuthenticatedUser(
                email="dev@local.internal",
                user_id="dev-local-user",
                name="Local Developer",
                roles=["admin"],
                claims={"dev_mode": True},
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": 'Bearer error="missing_token"'},
        )

    # 2. Token is present: verify cryptographically
    return auth_validator.verify_jwt(token)
