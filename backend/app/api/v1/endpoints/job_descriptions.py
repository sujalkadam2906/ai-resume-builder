"""Job Description management, analysis, and candidate matching API endpoints."""

import math
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.auth import AuthenticatedUser, get_current_user
from backend.app.core.rate_limiter import user_rate_limit
from backend.app.database.session import get_db
from backend.app.schemas.resume import (
    CandidateMatchResponse,
    JobDescriptionAnalysisResponse,
    JobDescriptionCreate,
    JobDescriptionPaginationResponse,
    JobDescriptionResponse,
    JobDescriptionUpdate,
)
from backend.app.services.job_description_service import JobDescriptionService
from backend.app.services.matching_service import CandidateMatchingService
from backend.app.services.profile_service import ProfileService

router = APIRouter(prefix="/job-descriptions", tags=["Job Descriptions"])


def _resolve_jd_or_404(session: Session, jd_id: uuid.UUID, current_user: AuthenticatedUser):
    """Helper to resolve Job Description by UUID and ownership or raise 404."""
    jd = JobDescriptionService.get_job_description(session, jd_id)
    is_owner = jd and ((jd.user_id == current_user.user_uuid) or (
        not settings.is_production
        and jd.user_id is None
        and current_user.user_uuid == uuid.uuid5(uuid.NAMESPACE_DNS, "dev-local-user")
    ))
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description '{jd_id}' not found.",
        )
    return jd


# ==============================================================================
# 1. Job Description CRUD
# ==============================================================================

@router.post(
    "",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit job description",
    description="Submit and persist a new target job description linked to an optional candidate profile and owned by the current user.",
)
def create_job_description(
    data: JobDescriptionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        jd = JobDescriptionService.create_job_description(db, data, user_id=current_user.user_uuid)
        source_url = (jd.requirement_matrix or {}).get("source_url")
        return JobDescriptionResponse(
            id=jd.id,
            profile_id=jd.profile_id,
            job_title=jd.job_title,
            company_name=jd.company_name,
            raw_text=jd.raw_text,
            source_url=source_url,
            extracted_skills=jd.extracted_skills,
            match_percentage=jd.match_percentage,
            created_at=jd.created_at,
            updated_at=jd.updated_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "",
    response_model=JobDescriptionPaginationResponse,
    summary="List job descriptions",
    description="Retrieve paginated list of job descriptions owned by the authenticated user, optionally filtered by candidate profile.",
)
def list_job_descriptions(
    profile_id: Optional[str] = Query(None, description="Filter by candidate profile slug or UUID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = JobDescriptionService.list_job_descriptions(
        db,
        profile_id=profile_id,
        user_id=current_user.user_uuid,
        page=page,
        size=size,
    )
    pages = math.ceil(total / size) if size > 0 else 1

    resp_items = [
        JobDescriptionResponse(
            id=jd.id,
            profile_id=jd.profile_id,
            job_title=jd.job_title,
            company_name=jd.company_name,
            raw_text=jd.raw_text,
            source_url=(jd.requirement_matrix or {}).get("source_url"),
            extracted_skills=jd.extracted_skills,
            match_percentage=jd.match_percentage,
            created_at=jd.created_at,
            updated_at=jd.updated_at,
        )
        for jd in items
    ]

    return JobDescriptionPaginationResponse(
        items=resp_items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/{jd_id}",
    response_model=JobDescriptionResponse,
    summary="Get job description",
    description="Retrieve specific job description by UUID.",
)
def get_job_description(
    jd_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = _resolve_jd_or_404(db, jd_id, current_user)
    return JobDescriptionResponse(
        id=jd.id,
        profile_id=jd.profile_id,
        job_title=jd.job_title,
        company_name=jd.company_name,
        raw_text=jd.raw_text,
        source_url=(jd.requirement_matrix or {}).get("source_url"),
        extracted_skills=jd.extracted_skills,
        match_percentage=jd.match_percentage,
        created_at=jd.created_at,
        updated_at=jd.updated_at,
    )


@router.patch(
    "/{jd_id}",
    response_model=JobDescriptionResponse,
    summary="Update job description",
    description="Partially update an existing job description owned by the current user.",
)
def update_job_description(
    jd_id: uuid.UUID,
    data: JobDescriptionUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = _resolve_jd_or_404(db, jd_id, current_user)
    updated = JobDescriptionService.update_job_description(db, jd, data)
    return JobDescriptionResponse(
        id=updated.id,
        profile_id=updated.profile_id,
        job_title=updated.job_title,
        company_name=updated.company_name,
        raw_text=updated.raw_text,
        source_url=(updated.requirement_matrix or {}).get("source_url"),
        extracted_skills=updated.extracted_skills,
        match_percentage=updated.match_percentage,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete(
    "/{jd_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job description",
    description="Permanently delete a job description owned by the current user.",
)
def delete_job_description(
    jd_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = _resolve_jd_or_404(db, jd_id, current_user)
    JobDescriptionService.delete_job_description(db, jd)
    return None


# ==============================================================================
# 2. Job Description Analysis & Candidate Matching
# ==============================================================================

@router.post(
    "/{jd_id}/analyze",
    response_model=JobDescriptionAnalysisResponse,
    summary="Analyze job description",
    description="Extract required skills, preferred skills, technical stack, responsibilities, and keywords.",
    dependencies=[Depends(user_rate_limit(max_requests=settings.rate_limit_analysis_per_minute, window_seconds=60))],
)
def analyze_job_description(
    jd_id: uuid.UUID,
    profile_id: Optional[str] = Query(None, description="Optional candidate profile slug/UUID to contextualize match"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = _resolve_jd_or_404(db, jd_id, current_user)
    cand_profile = None
    if profile_id:
        cand_profile = ProfileService.get_profile_by_id_or_slug(db, profile_id, user_id=current_user.user_uuid)
        if not cand_profile:
            raise HTTPException(status_code=404, detail=f"Candidate profile '{profile_id}' not found.")
    return JobDescriptionService.analyze_job_description(db, jd, candidate_profile=cand_profile)


@router.get(
    "/{jd_id}/analysis",
    response_model=JobDescriptionAnalysisResponse,
    summary="Get job description analysis",
    description="Retrieve saved structured analysis and requirement matrix for human review.",
)
def get_job_description_analysis(
    jd_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = _resolve_jd_or_404(db, jd_id, current_user)
    return JobDescriptionService.get_analysis(jd)


@router.get(
    "/{jd_id}/match",
    response_model=CandidateMatchResponse,
    summary="Match candidate against job description",
    description="Calculate match percentage, matched/missing skills, and explainable 45/25/20/10 project ranking.",
)
def match_candidate(
    jd_id: uuid.UUID,
    profile_id: str = Query(..., description="Candidate profile slug or UUID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jd = _resolve_jd_or_404(db, jd_id, current_user)
    candidate = ProfileService.get_profile_by_id_or_slug(db, profile_id, user_id=current_user.user_uuid)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate profile '{profile_id}' not found.")
    return CandidateMatchingService.match_candidate_to_jd(db, candidate, jd)
