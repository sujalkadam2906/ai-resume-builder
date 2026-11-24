"""Health and readiness probe endpoints."""

from datetime import datetime, timezone
import os
import shutil
from typing import Any, Dict
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import check_db_connection

router = APIRouter(tags=["Health & Probes"])


@router.get("/health", summary="Liveness Probe")
def liveness_probe() -> Dict[str, Any]:
    """
    Lightweight probe to verify the application process is running and accepting HTTP requests.
    Used by orchestrators (Docker, Render, Kubernetes) for health checks.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready", summary="Readiness Probe")
def readiness_probe() -> JSONResponse:
    """
    In-depth readiness probe checking storage, engine module availability,
    and database configuration.
    """
    checks: Dict[str, Any] = {}
    is_ready = True

    # 1. Storage write test
    try:
        test_file = settings.storage_path / ".healthcheck.tmp"
        test_file.write_text("health", encoding="utf-8")
        test_file.unlink()
        checks["storage"] = {
            "status": "ok",
            "backend": settings.storage_backend,
            "path": str(settings.storage_path),
        }
    except Exception as e:
        checks["storage"] = {"status": "error", "detail": str(e)}
        is_ready = False

    # 2. Python Core Resume Engine availability
    try:
        import resume_builder  # noqa: F401
        from resume_builder.config import config  # noqa: F401
        from resume_builder.ai.provider_manager import ProviderManager  # noqa: F401
        checks["resume_engine"] = {
            "status": "ok",
            "version": getattr(resume_builder, "__version__", "1.1.0"),
        }
    except Exception as e:
        checks["resume_engine"] = {"status": "error", "detail": str(e)}
        is_ready = False

    # 3. Database connectivity status
    db_ok, db_msg = check_db_connection()
    checks["database"] = {
        "status": "ok" if db_ok else "error",
        "detail": db_msg,
        "target": settings.database_url.split("@")[-1] if "@" in settings.database_url else "configured",
    }
    if not db_ok:
        is_ready = False

    # 4. Security Gate status
    checks["security_gate"] = {
        "cloudflare_access_required": settings.require_cf_access,
        "status": "active" if settings.require_cf_access else "disabled (local dev mode)",
    }

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        },
    )
