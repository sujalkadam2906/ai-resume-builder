"""Gemini AI Provider Adapter."""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from ...config import config
from ...jd_analysis.models import JobDescription, RequirementMatrix
from ...profile.models import MasterProfile, ProjectItem
from ..prompts import SYSTEM_PROMPT, build_tailoring_user_prompt
from ..structured_schemas import TailoredResumeContent
from .base import BaseAIProvider, enforce_resume_safeguards

logger = logging.getLogger("resume_builder.ai.gemini")


class GeminiProvider(BaseAIProvider):
    """Google Gemini Provider using official google-genai SDK."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        super().__init__(name="gemini", display_name="Google Gemini", config_dict=config_dict)
        self.api_key = config.gemini_api_key

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
                "details": "GEMINI_API_KEY is not set in environment or .env.",
            }

        try:
            from google import genai
            from google.genai import types
            timeout_ms = int(min(self.timeout_seconds, 10) * 1000)
            client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(timeout=timeout_ms))
            models = self.discover_models()
            return {
                "provider": self.display_name,
                "configured": True,
                "auth_status": "Valid",
                "connectivity": "Reachable",
                "model_status": f"Available ({len(models)} candidate models)",
                "free_tier": True,
                "details": f"Usable candidate models: {', '.join(models[:3])}",
            }
        except Exception as e:
            err_str = str(e)
            auth = "Unauthorized" if any(k in err_str for k in ["401", "403", "API_KEY_INVALID"]) else "Error"
            return {
                "provider": self.display_name,
                "configured": True,
                "auth_status": auth,
                "connectivity": "Failed",
                "model_status": "Unavailable",
                "free_tier": True,
                "details": f"Health check failed: {err_str[:120]}",
            }

    def discover_models(self) -> List[str]:
        candidates = self.candidate_models or config.candidate_models
        if not self.is_configured():
            return candidates

        try:
            from google import genai
            from google.genai import types
            timeout_ms = int(min(self.timeout_seconds, 10) * 1000)
            client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(timeout=timeout_ms))
            available = set()
            for m in client.models.list():
                name = getattr(m, "name", "")
                short = name.split("/")[-1] if "/" in name else name
                available.add(short)
            filtered = [c for c in candidates if c in available]
            return filtered if filtered else candidates
        except Exception:
            return candidates

    def generate_tailored_content(
        self,
        profile: MasterProfile,
        selected_projects: List[ProjectItem],
        jd: JobDescription,
        req_matrix: RequirementMatrix,
    ) -> Tuple[TailoredResumeContent, str]:
        if not self.is_configured():
            raise ValueError("Gemini API key is not configured.")

        from google import genai
        from google.genai import types

        timeout_ms = int(self.timeout_seconds * 1000)
        client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(timeout=timeout_ms))
        user_prompt = build_tailoring_user_prompt(profile, selected_projects, jd, req_matrix)
        models = self.discover_models()

        last_err = None
        for model_name in models:
            logger.info(f"Gemini attempting model: {model_name}")
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=self.temperature,
                        response_mime_type="application/json",
                        response_schema=TailoredResumeContent,
                    ),
                )
                content = self.parse_and_validate(response.text, selected_projects)
                return content, model_name
            except Exception as e:
                last_err = e
                err_str = str(e)
                if any(k in err_str for k in ["401", "403", "API_KEY_INVALID"]):
                    raise PermissionError(f"Gemini authentication failed: {e}") from e
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    logger.warning(f"Gemini model {model_name} quota exhausted (429). Switching to next candidate model.")
                    continue
                if "404" in err_str or "NOT_FOUND" in err_str:
                    logger.warning(f"Gemini model {model_name} not found (404), skipping to next model.")
                    continue
                if any(k in err_str for k in ["500", "503", "UNAVAILABLE"]):
                    logger.warning(f"Gemini model {model_name} temporarily unavailable ({err_str[:80]}). Switching to next candidate.")
                    continue
                logger.warning(f"Gemini error with {model_name}: {err_str[:120]}")

        raise RuntimeError(f"All Gemini candidate models failed. Last error: {last_err}")
