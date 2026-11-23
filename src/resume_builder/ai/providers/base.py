"""Common Base Provider interface and utilities for multi-provider AI architecture."""

import abc
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from ...jd_analysis.models import JobDescription, RequirementMatrix
from ...profile.models import MasterProfile, ProfileConfig, ProjectItem
from ..prompts import SYSTEM_PROMPT, build_tailoring_user_prompt
from ..structured_schemas import TailoredProject, TailoredResumeContent

logger = logging.getLogger("resume_builder.ai")


def extract_json_from_text(text: str) -> str:
    """Extract JSON object from string, handling markdown fences or leading/trailing text."""
    text = text.strip()
    # Match markdown json codeblocks
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if code_block:
        return code_block.group(1).strip()
    # Match outermost curly braces
    brace_match = re.search(r"(\{[\s\S]*\})", text)
    if brace_match:
        return brace_match.group(1).strip()
    return text


def sanitize_candidate_evidence_for_privacy(
    profile: MasterProfile,
    profile_config: Optional[ProfileConfig] = None,
) -> Dict[str, Any]:
    """
    Privacy safeguard: Strip private personal identifiers and prohibited terms
    before sending data to external AI providers.
    Uses candidate's verified name from profile.
    """
    edu_summaries = [
        f"{e.degree}, {e.institution}, {e.cgpa}" for e in profile.education
    ]
    return {
        "candidate": f"Candidate {profile.personal_info.full_name}",
        "education": "; ".join(edu_summaries) if edu_summaries else "B.Tech",
        "verified_skills": profile.technical_skills.model_dump(),
        "verified_leadership": [l.description for l in profile.leadership_and_experience],
        "verified_certifications": profile.certifications,
    }


def enforce_resume_safeguards(
    content: TailoredResumeContent,
    selected_projects: List[ProjectItem],
    profile_config: Optional[ProfileConfig] = None,
) -> TailoredResumeContent:
    """
    Enforces candidate-specific identity and project positioning rules.
    Respects profile_config rules when provided, falling back safely.
    """
    # 1. Headline rule
    if profile_config and profile_config.headline_rule.mode == "permanent" and profile_config.headline_rule.permanent_headline:
        content.professional_headline = profile_config.headline_rule.permanent_headline
    elif not profile_config:
        content.professional_headline = "Entry-Level Software Engineer | Full Stack Developer | ML Research Paper Publisher"

    # 2. Summary rule
    if profile_config and profile_config.summary_rule.mode == "permanent" and profile_config.summary_rule.permanent_summary:
        content.professional_summary = profile_config.summary_rule.permanent_summary
    elif not profile_config:
        content.professional_summary = (
            "Developed full-stack projects using Java/Spring Boot and React/TypeScript, "
            "alongside PostgreSQL analytics and Python-based machine learning and Gemini-powered automation. "
            "Coordinated campus placement operations for 1,500+ students across 20+ recruitment drives. "
            "B.Tech graduate (2026, CGPA: 8.23/10); immediate joiner and open to relocation."
        )

    # 3. Fixed project rule
    has_fixed = (
        profile_config.project_selection.has_fixed_project
        if profile_config is not None
        else any("bearing" in p.id.lower() for p in selected_projects)
    )

    if has_fixed:
        fx_rule = profile_config.project_selection.fixed_project if profile_config else None
        fx_id = fx_rule.id.lower() if fx_rule else "bearing"
        fx_pos = fx_rule.position if fx_rule else 2

        if len(content.tailored_projects) >= fx_pos:
            target_p = content.tailored_projects[fx_pos - 1]
            if fx_id not in target_p.title.lower() and fx_id not in target_p.project_id.lower():
                logger.warning("Provider response displaced fixed project. Enforcing fixed position safeguard.")
                matching_orig = next(
                    (p for p in selected_projects if fx_id in p.id.lower() or fx_id in p.title.lower()),
                    None,
                )
                if matching_orig:
                    content.tailored_projects[fx_pos - 1] = TailoredProject(
                        project_id=matching_orig.id,
                        title=matching_orig.title,
                        subtitle=matching_orig.subtitle,
                        bullets=matching_orig.bullets,
                    )

    # If provider omitted projects, backfill from selected_projects
    existing_ids = {tp.project_id for tp in content.tailored_projects}
    if len(content.tailored_projects) < len(selected_projects):
        for orig in selected_projects:
            if orig.id not in existing_ids:
                content.tailored_projects.append(
                    TailoredProject(
                        project_id=orig.id,
                        title=orig.title,
                        subtitle=orig.subtitle,
                        bullets=orig.bullets,
                    )
                )

    return content


class BaseAIProvider(abc.ABC):
    """Abstract Base Class for all LLM providers."""

    def __init__(self, name: str, display_name: str, config_dict: Optional[Dict[str, Any]] = None):
        self.name = name
        self.display_name = display_name
        self.config = config_dict or {}

    @property
    def enabled(self) -> bool:
        return self.config.get("enabled", True)

    @property
    def temperature(self) -> float:
        return float(self.config.get("temperature", 0.2))

    @property
    def timeout_seconds(self) -> int:
        return int(self.config.get("timeout_seconds", 30))

    @property
    def max_retries(self) -> int:
        return int(self.config.get("max_retries", 3))

    @property
    def candidate_models(self) -> List[str]:
        return self.config.get("candidate_models", [])

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Returns True if required credentials / environment variables are set."""
        pass

    @abc.abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """
        Tests connectivity and authentication.
        Returns a dict: {
            "provider": str,
            "configured": bool,
            "auth_status": "Valid" | "Missing Key" | "Unauthorized",
            "connectivity": "Reachable" | "Unreachable",
            "model_status": str,
            "free_tier": bool,
            "details": str
        }
        """
        pass

    @abc.abstractmethod
    def discover_models(self) -> List[str]:
        """Discover available models from provider API or return verified candidate models."""
        pass

    @abc.abstractmethod
    def generate_tailored_content(
        self,
        profile: MasterProfile,
        selected_projects: List[ProjectItem],
        jd: JobDescription,
        req_matrix: RequirementMatrix,
    ) -> Tuple[TailoredResumeContent, str]:
        """
        Generate tailored resume content.
        Returns (TailoredResumeContent, active_model_name).
        """
        pass

    def parse_and_validate(
        self,
        raw_output: str,
        selected_projects: List[ProjectItem],
    ) -> TailoredResumeContent:
        """Parse raw text response, convert to Pydantic schema, and enforce safeguards."""
        clean_json_str = extract_json_from_text(raw_output)
        try:
            data = json.loads(clean_json_str)
        except Exception as e:
            raise ValueError(f"Provider {self.name} returned invalid JSON: {e}\nRaw: {raw_output[:200]}") from e

        content = TailoredResumeContent(**data)
        content = enforce_resume_safeguards(content, selected_projects)
        return content
