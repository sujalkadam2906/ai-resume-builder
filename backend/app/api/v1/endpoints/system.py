"""System inspection and AI provider health endpoints."""

import os
import platform
import sys
from typing import Any, Dict
from fastapi import APIRouter

from backend.app.config import settings

router = APIRouter(prefix="/system", tags=["System & Providers"])


@router.get("/info", summary="System Information")
def system_info() -> Dict[str, Any]:
    """Returns safe, non-sensitive system environment metadata."""
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "storage_backend": settings.storage_backend,
    }


@router.get("/providers", summary="AI Provider Status & Health")
def ai_providers_status() -> Dict[str, Any]:
    """
    Invokes the core resume engine's ProviderManager to run non-invasive health checks
    across all 6 AI providers (Gemini, Groq, Cohere, OpenRouter, Cloudflare, Offline).
    Guarantees zero leakage of actual API keys or secret tokens.
    """
    try:
        from resume_builder.ai.provider_manager import ProviderManager
        mgr = ProviderManager()
        report = mgr.check_all_providers()
        return {
            "status": "success",
            "primary_provider": report.get("selected_primary", "Offline Python Engine"),
            "fallback_sequence": report.get("fallback_sequence", []),
            "providers": report.get("providers", []),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to inspect AI providers: {e}",
            "providers": [],
        }
