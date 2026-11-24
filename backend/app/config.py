"""Configuration settings for the FastAPI Web Backend."""

from pathlib import Path
from typing import List
import os
from dotenv import load_dotenv

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Load root .env
load_dotenv(PROJECT_ROOT / ".env")


class WebSettings:
    """Strongly-typed application settings loaded from environment with production hardening."""

    def __init__(self):
        self.app_name: str = os.getenv("APP_NAME", "AI Resume Builder Platform API")
        self.app_version: str = "1.0.0"
        self.environment: str = os.getenv("APP_ENV", "development").lower()
        self.debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

        # Server
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.api_v1_prefix: str = "/api/v1"

        # CORS
        raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
        self.cors_origins: List[str] = [orig.strip() for orig in raw_cors.split(",") if orig.strip()]

        # Database
        pg_user = os.getenv("POSTGRES_USER", "postgres")
        pg_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = os.getenv("POSTGRES_PORT", "5434")
        pg_db = os.getenv("POSTGRES_DB", "resume_builder")
        default_db_url = f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        self.database_url: str = os.getenv("DATABASE_URL", default_db_url)

        # Storage
        self.storage_backend: str = os.getenv("STORAGE_BACKEND", "local")  # local | supabase
        self.storage_path: Path = STORAGE_DIR
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_service_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        # Cloudflare Access Security Gate
        self.cloudflare_access_team_name: str = os.getenv("CF_ACCESS_TEAM_NAME", "")
        self.cloudflare_access_aud: str = os.getenv("CF_ACCESS_AUD", "")
        self.require_cf_access: bool = os.getenv("REQUIRE_CF_ACCESS", "false").lower() in ("true", "1", "yes")
        self.allow_dev_auth_bypass: bool = os.getenv("ALLOW_DEV_AUTH_BYPASS", "true").lower() in ("true", "1", "yes")

        # Access authorization: comma-separated list of allowed user emails (empty = allow all authenticated CF Access users)
        raw_allowed = os.getenv("ALLOWED_EMAILS", "")
        self.allowed_emails: List[str] = [e.strip().lower() for e in raw_allowed.split(",") if e.strip()]

        # Rate Limiting
        self.rate_limit_generation_per_minute: int = int(os.getenv("RATE_LIMIT_GENERATION_PER_MINUTE", "10"))
        self.rate_limit_analysis_per_minute: int = int(os.getenv("RATE_LIMIT_ANALYSIS_PER_MINUTE", "15"))
        self.rate_limit_export_per_minute: int = int(os.getenv("RATE_LIMIT_EXPORT_PER_MINUTE", "20"))

        # Production Hardening Fail-Closed Enforcement
        if self.is_production:
            # In production, debug mode and development bypasses are strictly forbidden
            self.debug = False
            self.allow_dev_auth_bypass = False
            self.require_cf_access = True

    @property
    def is_production(self) -> bool:
        """Evaluate if the runtime environment is production."""
        return self.environment in ("production", "prod")

    @property
    def cloudflare_certs_url(self) -> str:
        """Return the public JWKS endpoint for the configured Cloudflare Access team."""
        if not self.cloudflare_access_team_name:
            return ""
        return f"https://{self.cloudflare_access_team_name}.cloudflareaccess.com/cdn-cgi/access/certs"


settings = WebSettings()
