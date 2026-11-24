"""Aggregated API v1 Router with Zero-Trust Authentication Gating."""

from fastapi import APIRouter, Depends
from backend.app.core.auth import get_current_user
from .endpoints import health, system, profiles, job_descriptions, resumes

api_v1_router = APIRouter()

# 1. Public monitoring probes (Liveness & Readiness for container orchestrators)
api_v1_router.include_router(health.router)

# 2. Authenticated Routes (Supabase JWT Protected)
auth_dependencies = [Depends(get_current_user)]

api_v1_router.include_router(system.router, dependencies=auth_dependencies)
api_v1_router.include_router(profiles.router, dependencies=auth_dependencies)
api_v1_router.include_router(job_descriptions.router, dependencies=auth_dependencies)
api_v1_router.include_router(resumes.router, dependencies=auth_dependencies)
