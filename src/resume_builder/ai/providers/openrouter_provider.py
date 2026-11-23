"""OpenRouter AI Provider Adapter (Unified gateway with free-tier access)."""

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

logger = logging.getLogger("resume_builder.ai.openrouter")


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter Provider supporting open-weight and commercial models with free tier."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        super().__init__(name="openrouter", display_name="OpenRouter", config_dict=config_dict)
        self.api_key = config.openrouter_api_key

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    @property
    def dynamic_routing(self) -> bool:
        return bool(self.config.get("dynamic_routing", False))

    def check_health(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "provider": self.display_name,
                "configured": False,
                "auth_status": "Missing Key",
                "connectivity": "Untested",
                "model_status": "N/A",
                "free_tier": True,
                "details": "OPENROUTER_API_KEY is not set in environment or .env.",
            }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    "https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if res.status_code == 200:
                    info = res.json().get("data", {})
                    limit = info.get("limit", "Unlimited/Free")
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Valid",
                        "connectivity": "Reachable",
                        "model_status": f"Free Tier Eligible (Dynamic: {self.dynamic_routing})",
                        "free_tier": True,
                        "details": f"Key verified. Pinned model: {self.config.get('default_free_model')}",
                    }
                elif res.status_code in (401, 403):
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Unauthorized",
                        "connectivity": "Reachable",
                        "model_status": "Invalid Key",
                        "free_tier": True,
                        "details": f"OpenRouter rejected API key (HTTP {res.status_code}).",
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
                "details": f"Network error connecting to OpenRouter: {e}",
            }

    def discover_models(self) -> List[str]:
        default_model = self.config.get("default_free_model", "meta-llama/llama-3.3-70b-instruct:free")
        candidates = self.candidate_models or [default_model, "mistralai/mistral-7b-instruct:free"]
        if self.dynamic_routing and "openrouter/free" not in candidates:
            candidates.insert(0, "openrouter/free")
        return candidates

    def generate_tailored_content(
        self,
        profile: MasterProfile,
        selected_projects: List[ProjectItem],
        jd: JobDescription,
        req_matrix: RequirementMatrix,
    ) -> Tuple[TailoredResumeContent, str]:
        if not self.is_configured():
            raise ValueError("OpenRouter API key is not configured.")

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
                    logger.info(f"OpenRouter calling model: {model_name} (dynamic={self.dynamic_routing}, attempt={attempt + 1})")
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": self.temperature,
                        "response_format": {"type": "json_object"},
                    }

                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/sujalkadam2906",
                        "X-Title": "ATS Resume Builder",
                    }

                    with httpx.Client(timeout=float(self.timeout_seconds)) as client:
                        res = client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=payload,
                        )

                    if res.status_code in (401, 403):
                        raise PermissionError(f"OpenRouter auth error ({res.status_code}): {res.text}")
                    if res.status_code == 404:
                        logger.warning(f"OpenRouter model {model_name} returned 404, skipping.")
                        break
                    if res.status_code == 429:
                        raise RuntimeError(f"OpenRouter rate limit exceeded (429): {res.text}")
                    if res.status_code != 200:
                        raise RuntimeError(f"OpenRouter API returned HTTP {res.status_code}: {res.text}")

                    data = res.json()
                    content_str = data["choices"][0]["message"]["content"]
                    content = self.parse_and_validate(content_str, selected_projects)
                    return content, f"openrouter/{model_name}"

                except Exception as e:
                    last_err = e
                    if isinstance(e, PermissionError) or "rate limit" in str(e).lower():
                        raise
                    logger.warning(f"OpenRouter error with {model_name}: {e}")

        raise RuntimeError(f"All OpenRouter models failed. Last error: {last_err}")
