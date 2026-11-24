"""Zero-Trust Cloudflare Access JWT Authentication & Identity Enforcement.

Provides:
- Cryptographic verification of 'Cf-Access-Jwt-Assertion' headers using Cloudflare JWKS.
- Strict claim validation: 'aud' (Audience tag), 'iss' (Team domain), 'exp' (Expiration), 'sub' (User ID).
- Absolute rejection of unverified client headers (e.g. naked 'Cf-Access-Authenticated-User-Email').
- Production fail-closed enforcement (no bypasses permitted when APP_ENV=production).
- Authorization gating against configured allowed user emails.
"""

from dataclasses import field
import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
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


class CloudflareAccessValidator:
    """Validator for Cloudflare Access JWT assertions."""

    def __init__(
        self,
        team_name: Optional[str] = None,
        expected_aud: Optional[str] = None,
        cache_ttl_seconds: int = 3600,
    ):
        self.team_name = team_name or settings.cloudflare_access_team_name
        self.expected_aud = expected_aud or settings.cloudflare_access_aud
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cached_keys: Dict[str, Any] = {}
        self._last_fetch: float = 0.0

    @property
    def expected_issuer(self) -> str:
        """Expected JWT issuer string for Cloudflare Access."""
        if not self.team_name:
            return ""
        return f"https://{self.team_name}.cloudflareaccess.com"

    @property
    def certs_url(self) -> str:
        """Cloudflare Access public keys/JWKS endpoint."""
        if not self.team_name:
            return ""
        return f"https://{self.team_name}.cloudflareaccess.com/cdn-cgi/access/certs"

    def set_cached_keys(self, jwks_keys: List[Dict[str, Any]]) -> None:
        """Manually populate cached keys (used for test isolation)."""
        self._cached_keys = {}
        for key_dict in jwks_keys:
            kid = key_dict.get("kid")
            if kid:
                self._cached_keys[kid] = RSAAlgorithm.from_jwk(key_dict)
        self._last_fetch = time.time()

    def fetch_public_keys(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch and cache Cloudflare public RSA keys from the JWKS certs endpoint."""
        now = time.time()
        if not force_refresh and self._cached_keys and (now - self._last_fetch < self.cache_ttl_seconds):
            return self._cached_keys

        if not self.certs_url:
            logger.warning("Cloudflare Access team name is not configured; cannot fetch certs.")
            return {}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(self.certs_url)
                if resp.status_code != 200:
                    logger.error(f"Failed to fetch Cloudflare certs: HTTP {resp.status_code}")
                    return self._cached_keys

                jwks = resp.json()
                keys = jwks.get("keys", [])
                parsed_keys = {}
                for key_dict in keys:
                    kid = key_dict.get("kid")
                    if kid:
                        parsed_keys[kid] = RSAAlgorithm.from_jwk(key_dict)

                self._cached_keys = parsed_keys
                self._last_fetch = now
                logger.info(f"Refreshed {len(parsed_keys)} Cloudflare Access public keys.")
                return self._cached_keys
        except Exception as exc:
            logger.error(f"Error fetching Cloudflare certs from {self.certs_url}: {exc}")
            return self._cached_keys

    def verify_jwt(self, token: str) -> AuthenticatedUser:
        """
        Cryptographically verify the Cloudflare Access JWT.
        Validates:
        - RSA256 signature against matching 'kid' public key
        - Audience 'aud'
        - Issuer 'iss'
        - Expiration 'exp'
        - Authorized user email (if ALLOWED_EMAILS is configured)
        """
        if not token or not isinstance(token, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or malformed Cloudflare Access JWT assertion.",
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
        if alg != "RS256":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported token algorithm '{alg}'. Only RS256 is accepted.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT header missing mandatory Key ID ('kid').",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        # 2. Resolve matching public RSA key
        keys = self.fetch_public_keys(force_refresh=False)
        public_key = keys.get(kid)
        if not public_key:
            # Refresh once in case key was recently rotated by Cloudflare
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
                "algorithms": ["RS256"],
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
                detail="Cloudflare Access token has expired.",
                headers={"WWW-Authenticate": 'Bearer error="token_expired"'},
            )
        except jwt.InvalidAudienceError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cloudflare Access token audience ('aud') mismatch.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )
        except jwt.InvalidIssuerError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cloudflare Access token issuer ('iss') mismatch.",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Cloudflare Access token verification failed: {exc}",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        # 4. Extract verified identity claims
        email = payload.get("email") or payload.get("identity", {}).get("email")
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

        return AuthenticatedUser(
            email=email,
            user_id=user_id,
            name=payload.get("name") or email.split("@")[0],
            is_authenticated=True,
            claims=payload,
        )


# Global singleton validator
access_validator = CloudflareAccessValidator()


def get_current_user(
    request: Request,
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_scheme),
) -> AuthenticatedUser:
    """
    FastAPI dependency to authenticate requests.
    Inspects:
    1. 'Cf-Access-Jwt-Assertion' header (primary Cloudflare Access token header)
    2. 'Authorization: Bearer <token>' header (fallback/API bearer token)
    
    Production Fail-Closed Rules:
    - If APP_ENV=production, valid Cloudflare Access token is mandatory.
    - Development bypasses are strictly disallowed in production.
    """
    # Extract token
    token = request.headers.get("Cf-Access-Jwt-Assertion")
    if not token and bearer_credentials and bearer_credentials.credentials:
        token = bearer_credentials.credentials

    # 1. Handle missing token
    if not token:
        if settings.is_production:
            logger.warning(
                f"Unauthorized request to {request.method} {request.url.path} in production: Missing Cloudflare Access JWT."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: Missing Cloudflare Access JWT assertion.",
                headers={"WWW-Authenticate": 'Bearer error="missing_token"'},
            )

        # Development environment handling
        if settings.require_cf_access:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: REQUIRE_CF_ACCESS is enabled.",
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
    return access_validator.verify_jwt(token)
