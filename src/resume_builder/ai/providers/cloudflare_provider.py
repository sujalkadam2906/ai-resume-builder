"""Cloudflare Workers AI Provider Adapter (Edge serverless inference)."""

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

logger = logging.getLogger("resume_builder.ai.cloudflare")


class CloudflareProvider(BaseAIProvider):
    """Cloudflare Workers AI Provider with generous free daily neurons tier."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        super().__init__(name="cloudflare", display_name="Cloudflare Workers AI", config_dict=config_dict)
        self.api_token = config.cloudflare_api_token
        self.account_id = config.cloudflare_account_id

    def is_configured(self) -> bool:
        return bool(
            self.api_token
            and len(self.api_token.strip()) > 5
            and self.account_id
            and len(self.account_id.strip()) > 5
        )

    def check_health(self) -> Dict[str, Any]:
        if not self.is_configured():
            missing = []
            if not self.api_token:
                missing.append("CLOUDFLARE_API_TOKEN")
            if not self.account_id:
                missing.append("CLOUDFLARE_ACCOUNT_ID")
            return {
                "provider": self.display_name,
                "configured": False,
                "auth_status": "Missing Credentials",
                "connectivity": "Untested",
                "model_status": "N/A",
                "free_tier": True,
                "details": f"Missing: {', '.join(missing)} in .env.",
            }

        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/models/search"
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    url,
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("result", []) if "name" in m]
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Valid",
                        "connectivity": "Reachable",
                        "model_status": f"Available ({len(models)} models)",
                        "free_tier": True,
                        "details": "Free tier (10,000 neurons/day included).",
                    }
                elif res.status_code in (401, 403):
                    return {
                        "provider": self.display_name,
                        "configured": True,
                        "auth_status": "Unauthorized",
                        "connectivity": "Reachable",
                        "model_status": "Invalid Token",
                        "free_tier": True,
                        "details": f"Cloudflare rejected API token (HTTP {res.status_code}).",
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
                "details": f"Network error connecting to Cloudflare: {e}",
            }

    def discover_models(self) -> List[str]:
        return self.candidate_models or [
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            "@cf/meta/llama-3.1-8b-instruct",
            "@cf/mistral/mistral-7b-instruct-v0.2",
        ]

    def generate_tailored_content(
        self,
        profile: MasterProfile,
        selected_projects: List[ProjectItem],
        jd: JobDescription,
        req_matrix: RequirementMatrix,
    ) -> Tuple[TailoredResumeContent, str]:
        if not self.is_configured():
            raise ValueError("Cloudflare API credentials not configured.")

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
                    logger.info(f"Cloudflare calling model: {model_name} (attempt {attempt + 1})")
                    url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{model_name}"
                    payload = {
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": self.temperature,
                    }

                    headers = {
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json",
                    }

                    with httpx.Client(timeout=float(self.timeout_seconds)) as client:
                        res = client.post(url, headers=headers, json=payload)

                    if res.status_code in (401, 403):
                        raise PermissionError(f"Cloudflare auth error ({res.status_code}): {res.text}")
                    if res.status_code == 404:
                        logger.warning(f"Cloudflare model {model_name} returned 404, skipping.")
                        break
                    if res.status_code == 429:
                        raise RuntimeError(f"Cloudflare rate limit exceeded (429): {res.text}")
                    if res.status_code != 200:
                        raise RuntimeError(f"Cloudflare API returned HTTP {res.status_code}: {res.text}")

                    data = res.json()
                    # Result structure in Cloudflare Workers AI
                    content_str = data.get("result", {}).get("response", "")
                    content = self.parse_and_validate(content_str, selected_projects)
                    return content, f"cloudflare/{model_name}"

                except Exception as e:
                    last_err = e
                    if isinstance(e, PermissionError) or "rate limit" in str(e).lower():
                        raise
                    logger.warning(f"Cloudflare error with {model_name}: {e}")

        raise RuntimeError(f"All Cloudflare models failed. Last error: {last_err}")
