"""Offline Deterministic Provider Adapter (Zero network, 100% compliant)."""

from typing import Any, Dict, List, Optional, Tuple

from ...jd_analysis.models import JobDescription, RequirementMatrix
from ...profile.models import MasterProfile, ProjectItem
from ..gemini_client import generate_offline_content
from ..structured_schemas import TailoredResumeContent
from .base import BaseAIProvider


class OfflineProvider(BaseAIProvider):
    """Deterministic local Python generation engine requiring no network or API keys."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        super().__init__(name="offline", display_name="Offline Python Engine", config_dict=config_dict)

    def is_configured(self) -> bool:
        return True

    def check_health(self) -> Dict[str, Any]:
        return {
            "provider": self.display_name,
            "configured": True,
            "auth_status": "Not Required",
            "connectivity": "Local (Instant)",
            "model_status": "Ready",
            "free_tier": True,
            "details": "Local rule-based generator enforcing 100% truthful profile tailoring.",
        }

    def discover_models(self) -> List[str]:
        return ["deterministic-offline-v1"]

    def generate_tailored_content(
        self,
        profile: MasterProfile,
        selected_projects: List[ProjectItem],
        jd: JobDescription,
        req_matrix: RequirementMatrix,
    ) -> Tuple[TailoredResumeContent, str]:
        content = generate_offline_content(profile, selected_projects, jd, req_matrix)
        content = self.parse_and_validate(content.model_dump_json(), selected_projects)
        return content, "offline/deterministic-engine"
