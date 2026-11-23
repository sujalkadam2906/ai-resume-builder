"""Cohere AI Provider Adapter (Command-R series)."""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from ...config import config
from ...jd_analysis.models import JobDescription, RequirementMatrix
from ...profile.models import MasterProfile, ProjectItem
from ..prompts import SYSTEM_PROMPT, build_tailoring_user_prompt
from ..structured_schemas import TailoredResumeContent
from .base import BaseAIProvider

logger = logging.getLogger("resume_builder.ai.cohere")


class CohereProvider(BaseAIProvider):
    """Cohere Provider supporting Command-R and Command-R+ models."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        super().__init__(name="cohere", display_name="Cohere", config_dict=config_dict)
        self.api_key = config.cohere_api_key

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def check_health(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "provider": self.display_name,
                "configured": False,
                "auth_status": "Missing Key",
                "connectivity": "Untested",
                "model_status": "N/A",
                "free_tier": True,
                "details": "COHERE_API_KEY is not set in environment or .env.",
            }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    "https://api.cohere.com/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", []) if "name" in m]
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Valid",
                        "connectivity": "Reachable",
                        "model_status": f"Available ({len(models)} models)",
                        "free_tier": True,
                        "details": f"Cohere models available: {', '.join(models[:3])}",
                    }
                elif res.status_code in (401, 403):
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Unauthorized",
                        "connectivity": "Reachable",
                        "model_status": "Invalid Key",
                        "free_tier": True,
                        "details": f"Cohere rejected API key (HTTP {res.status_code}).",
                    }
                else:
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Unknown",
                        "connectivity": "Failed",
                        "model_status": f"HTTP {res.status_code}",
                        "free_tier": True,
                        "details": res.text[:100],
                    }
        except Exception as e:
            return {
                "provider": self.display_name,
                "configured": True,
                "auth_status": "Error",
                "connectivity": "Unreachable",
                "model_status": "Unavailable",
                "free_tier": True,
                "details": f"Network error connecting to Cohere: {e}",
            }

    def discover_models(self) -> List[str]:
        candidates = self.candidate_models or [
            "command-r-plus-08-2024",
            "command-r-plus",
            "command-r",
            "command-light",
        ]
        if not self.is_configured():
            return candidates

        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.get(
                    "https://api.cohere.com/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if res.status_code == 200:
                    active = {m.get("name") for m in res.json().get("models", [])}
                    matched = [c for c in candidates if c in active]
                    return matched if matched else candidates
        except Exception:
            pass
        return candidates

    def generate_tailored_content(
        self,
        profile: MasterProfile,
        selected_projects: List[ProjectItem],
        jd: JobDescription,
        req_matrix: RequirementMatrix,
    ) -> Tuple[TailoredResumeContent, str]:
        if not self.is_configured():
            raise ValueError("Cohere API key is not configured.")

        user_prompt = build_tailoring_user_prompt(profile, selected_projects, jd, req_matrix)
        models = self.discover_models()

        schema_json = json.dumps(TailoredResumeContent.model_json_schema(), indent=2)
        system_instruction = (
            f"{SYSTEM_PROMPT}\n\n"
            "You MUST output valid, parseable JSON strictly matching this JSON schema:\n"
            f"{schema_json}\n"
            "Do not include any conversational preamble or postscript. Output ONLY JSON."
        )

        last_err = None
        for model_name in models:
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Cohere calling model: {model_name} (attempt {attempt + 1})")
                    # Cohere v2 chat format
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": self.temperature,
                        "response_format": {"type": "json_object"},
                    }

                    with httpx.Client(timeout=float(self.timeout_seconds)) as client:
                        res = client.post(
                            "https://api.cohere.com/v2/chat",
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json",
                            },
                            json=payload,
                        )

                    if res.status_code in (401, 403):
                        raise PermissionError(f"Cohere auth error ({res.status_code}): {res.text}")
                    if res.status_code == 404:
                        logger.warning(f"Cohere model {model_name} returned 404, skipping.")
                        break
                    if res.status_code == 429:
                        raise RuntimeError(f"Cohere rate limit exceeded (429): {res.text}")
                    if res.status_code != 200:
                        raise RuntimeError(f"Cohere API returned HTTP {res.status_code}: {res.text}")

                    data = res.json()
                    # v2 chat message content
                    content_str = data["message"]["content"][0]["text"]
                    content = self.parse_and_validate(content_str, selected_projects)
                    return content, f"cohere/{model_name}"

                except Exception as e:
                    last_err = e
                    if isinstance(e, PermissionError) or "rate limit" in str(e).lower():
                        raise
                    logger.warning(f"Cohere error with {model_name}: {e}")

        raise RuntimeError(f"All Cohere models failed. Last error: {last_err}")
