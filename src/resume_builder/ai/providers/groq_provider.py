"""Groq AI Provider Adapter (Ultra-low latency, free tier available)."""

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

logger = logging.getLogger("resume_builder.ai.groq")


class GroqProvider(BaseAIProvider):
    """Groq Provider offering high-throughput inference for open-weight models."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        super().__init__(name="groq", display_name="Groq", config_dict=config_dict)
        self.api_key = config.groq_api_key

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
                "details": "GROQ_API_KEY is not set in environment or .env.",
            }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if res.status_code == 200:
                    models_data = res.json().get("data", [])
                    available_ids = [m["id"] for m in models_data if "id" in m]
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Valid",
                        "connectivity": "Reachable",
                        "model_status": f"Available ({len(available_ids)} models)",
                        "free_tier": True,
                        "details": f"Verified free-tier access. Models: {', '.join(available_ids[:3])}",
                    }
                elif res.status_code in (401, 403):
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Unauthorized",
                        "connectivity": "Reachable",
                        "model_status": "Invalid Key",
                        "free_tier": True,
                        "details": f"Groq rejected API key (HTTP {res.status_code}).",
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
                "details": f"Network error connecting to Groq: {e}",
            }

    def discover_models(self) -> List[str]:
        candidates = self.candidate_models or [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ]
        if not self.is_configured():
            return candidates

        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if res.status_code == 200:
                    active = {m["id"] for m in res.json().get("data", [])}
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
            raise ValueError("Groq API key is not configured.")

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
                    logger.info(f"Groq calling model: {model_name} (attempt {attempt + 1})")
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
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json",
                            },
                            json=payload,
                        )

                    if res.status_code in (401, 403):
                        raise PermissionError(f"Groq auth error ({res.status_code}): {res.text}")
                    if res.status_code == 404:
                        logger.warning(f"Groq model {model_name} returned 404, skipping.")
                        break
                    if res.status_code == 429:
                        raise RuntimeError(f"Groq rate limit exceeded (429): {res.text}")
                    if res.status_code != 200:
                        raise RuntimeError(f"Groq API returned HTTP {res.status_code}: {res.text}")

                    data = res.json()
                    content_str = data["choices"][0]["message"]["content"]
                    content = self.parse_and_validate(content_str, selected_projects)
                    return content, f"groq/{model_name}"

                except Exception as e:
                    last_err = e
                    if isinstance(e, PermissionError) or "rate limit" in str(e).lower():
                        raise
                    logger.warning(f"Groq error with {model_name}: {e}")

        raise RuntimeError(f"All Groq models failed. Last error: {last_err}")
