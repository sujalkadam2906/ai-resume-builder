"""Configuration management for the multi-provider resume builder system."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import yaml
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_FILE = DATA_DIR / "config.yaml"
MASTER_PROFILE_FILE = DATA_DIR / "master_profile.json"
PROJECTS_FILE = DATA_DIR / "projects.json"
BACKUPS_DIR = DATA_DIR / "backups"
PROFILES_DIR = PROJECT_ROOT / "profiles"
DEFAULT_PROFILE_ID = "sujal"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
JOB_DESCRIPTIONS_DIR = PROJECT_ROOT / "job_descriptions"


def get_profile_dir(profile_id: str) -> Path:
    """Validates profile ID and returns safe profile path preventing path traversal."""
    if not profile_id or not isinstance(profile_id, str):
        raise ValueError("Profile ID must be a non-empty string.")
    import re
    if not re.match(r"^[a-zA-Z0-9_\-]+$", profile_id) or ".." in profile_id or "/" in profile_id or "\\" in profile_id:
        raise ValueError(f"Invalid profile ID: '{profile_id}'. Only alphanumeric characters, dashes, and underscores are permitted.")
    return PROFILES_DIR / profile_id

# Load environment variables from .env if present
load_dotenv(PROJECT_ROOT / ".env")


def load_yaml_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from config.yaml with sensible fallbacks."""
    config_path = path or CONFIG_FILE
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


class AppConfig:
    """Strongly typed application configuration."""

    def __init__(self, raw: Optional[Dict[str, Any]] = None):
        self._raw = raw or load_yaml_config()
        self._providers = self._raw.get("providers", {})
        self._project_sel = self._raw.get("project_selection", {})
        self._layout = self._raw.get("layout", {})
        self._ats = self._raw.get("ats_scoring", {})

    @property
    def provider_priority(self) -> List[str]:
        return self._providers.get(
            "priority",
            ["gemini", "groq", "cohere", "openrouter", "cloudflare", "offline"],
        )

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Return provider-specific dictionary configuration."""
        # Check under providers section
        p_cfg = self._providers.get(provider_name.lower(), {})
        # Fallback to legacy gemini section if present
        if not p_cfg and provider_name.lower() == "gemini":
            p_cfg = self._raw.get("gemini", {})
        return p_cfg

    def is_provider_enabled(self, provider_name: str) -> bool:
        p_cfg = self.get_provider_config(provider_name)
        return p_cfg.get("enabled", True)

    # API Keys & Credentials
    @property
    def gemini_api_key(self) -> Optional[str]:
        return os.environ.get("GEMINI_API_KEY") or None

    @property
    def groq_api_key(self) -> Optional[str]:
        return os.environ.get("GROQ_API_KEY") or None

    @property
    def cohere_api_key(self) -> Optional[str]:
        return os.environ.get("COHERE_API_KEY") or None

    @property
    def openrouter_api_key(self) -> Optional[str]:
        return os.environ.get("OPENROUTER_API_KEY") or None

    @property
    def cloudflare_api_token(self) -> Optional[str]:
        return os.environ.get("CLOUDFLARE_API_TOKEN") or None

    @property
    def cloudflare_account_id(self) -> Optional[str]:
        return os.environ.get("CLOUDFLARE_ACCOUNT_ID") or None

    # Legacy gemini candidate models for backward compatibility
    @property
    def candidate_models(self) -> List[str]:
        g_cfg = self.get_provider_config("gemini")
        return g_cfg.get(
            "candidate_models",
            [
                "gemini-4-carbon",
                "gemini-4-hydrogen",
                "gemini-3.8-flash",
                "gemini-3.6-flash",
                "gemini-3.5-flash-lite",
            ],
        )

    @property
    def gemini_temperature(self) -> float:
        return float(self.get_provider_config("gemini").get("temperature", 0.2))

    @property
    def gemini_max_retries(self) -> int:
        return int(self.get_provider_config("gemini").get("max_retries", 3))

    @property
    def gemini_timeout_seconds(self) -> int:
        return int(self.get_provider_config("gemini").get("timeout_seconds", 30))

    @property
    def gemini_backoff_factor(self) -> float:
        return float(self.get_provider_config("gemini").get("backoff_factor", 2.0))

    # Project selection
    @property
    def target_project_count(self) -> int:
        return int(self._project_sel.get("target_project_count", 4))

    @property
    def fixed_project_id(self) -> str:
        fixed = self._project_sel.get("fixed_project", {})
        return fixed.get("id", "bearing_fault_diagnosis")

    @property
    def fixed_project_position(self) -> int:
        fixed = self._project_sel.get("fixed_project", {})
        return int(fixed.get("position", 2))

    @property
    def project_weights(self) -> Dict[str, float]:
        return self._project_sel.get(
            "weights",
            {
                "required_skills_coverage": 0.45,
                "responsibilities_alignment": 0.25,
                "tech_stack_similarity": 0.20,
                "domain_relevance": 0.10,
            },
        )

    # ATS scoring
    @property
    def ats_weights(self) -> Dict[str, int]:
        return self._ats.get(
            "weights",
            {
                "format_compatibility": 30,
                "jd_relevance": 50,
                "content_quality": 20,
            },
        )

    @property
    def primary_accent_color(self) -> str:
        colors = self._layout.get("colors", {})
        return colors.get("primary_accent", "#1B365D")


config = AppConfig()
