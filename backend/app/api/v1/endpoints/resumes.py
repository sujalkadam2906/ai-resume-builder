"""Resume Generation, Manual Editing, Versioning, Approval, Export, and ATS Evaluation endpoints."""

import math
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.auth import AuthenticatedUser, get_current_user
from backend.app.core.rate_limiter import user_rate_limit
from backend.app.database.session import get_db
from backend.app.schemas.resume import (
    ATSEvaluationResponse,
    ResumeApprovalResponse,
    ResumeGenerateRequest,
    ResumePaginationResponse,
    ResumeResponse,
    ResumeUpdateRequest,
    ResumeVersionResponse,
)
from backend.app.services.ats_evaluation_service import ATSEvaluationService
from backend.app.services.resume_approval_service import ResumeApprovalService
from backend.app.services.resume_export_service import ResumeExportService
from backend.app.services.resume_generation_service import ResumeGenerationService

router = APIRouter(prefix="/resumes", tags=["Resumes"])


def _resolve_resume_or_404(session: Session, resume_id: uuid.UUID, current_user: AuthenticatedUser):
    """Helper to resolve Resume by UUID and user ownership or raise 404."""
    resume = ResumeApprovalService.get_resume(session, resume_id)
    is_owner = resume and ((resume.user_id == current_user.user_uuid) or (
        not settings.is_production
        and resume.user_id is None
        and current_user.user_uuid == uuid.uuid5(uuid.NAMESPACE_DNS, "dev-local-user")
    ))
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume '{resume_id}' not found.",
        )
    return resume


# ==============================================================================
# 1. Resume Generation & Lifecycle
# ==============================================================================

@router.post(
    "/generate",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate tailored resume draft",
    description="Generate a new draft resume tailored for a target JD, selecting relevant projects and skills.",
    dependencies=[Depends(user_rate_limit(max_requests=settings.rate_limit_generation_per_minute, window_seconds=60))],
)
def generate_resume(
    request: ResumeGenerateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        resume = ResumeGenerationService.generate_draft(db, request, user_id=current_user.user_uuid)
        return resume
    except ValueError as exc:
        err_msg = str(exc)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        if "different candidate" in err_msg.lower() or "archived" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


@router.get(
    "",
    response_model=ResumePaginationResponse,
    summary="List resumes",
    description="Retrieve paginated list of resumes owned by the authenticated user with optional profile or status filters.",
)
def list_resumes(
    profile_id: Optional[str] = Query(None, description="Filter by candidate profile slug or UUID"),
    status: Optional[str] = Query(None, description="Filter by status e.g. 'draft' or 'approved'"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = ResumeApprovalService.list_resumes(
        db,
        profile_id=profile_id,
        user_id=current_user.user_uuid,
        status_filter=status,
        page=page,
        size=size,
    )
    pages = math.ceil(total / size) if size > 0 else 1

    return ResumePaginationResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get resume details",
    description="Retrieve complete resume record including editable manifest.",
)
def get_resume(
    resume_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _resolve_resume_or_404(db, resume_id, current_user)


@router.patch(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Update resume draft",
    description="Apply manual edits to resume manifest. If previously approved, increments version to protect history.",
)
def update_resume(
    resume_id: uuid.UUID,
    data: ResumeUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = _resolve_resume_or_404(db, resume_id, current_user)
    try:
        updated = ResumeApprovalService.update_resume(db, resume, data)
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/{resume_id}/approve",
    response_model=ResumeApprovalResponse,
    summary="Approve resume",
    description="Mark resume draft as approved, locking its current version for export.",
)
def approve_resume(
    resume_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = _resolve_resume_or_404(db, resume_id, current_user)
    try:
        return ResumeApprovalService.approve_resume(db, resume)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ==============================================================================
# 2. Version History
# ==============================================================================

@router.get(
    "/{resume_id}/versions",
    response_model=List[ResumeVersionResponse],
    summary="List resume versions",
    description="Retrieve historical version snapshots for a resume.",
)
def list_resume_versions(
    resume_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _resolve_resume_or_404(db, resume_id, current_user)
    return ResumeApprovalService.list_versions(db, resume_id)


@router.get(
    "/{resume_id}/versions/{version_number}",
    response_model=ResumeVersionResponse,
    summary="Get resume version snapshot",
    description="Retrieve an immutable historical version snapshot by version number.",
)
def get_resume_version(
    resume_id: uuid.UUID,
    version_number: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _resolve_resume_or_404(db, resume_id, current_user)
    ver = ResumeApprovalService.get_version(db, resume_id, version_number)
    if not ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_number} not found for resume '{resume_id}'.",
        )
    return ver


# ==============================================================================
# 3. Document Export (PDF & DOCX)
# ==============================================================================

@router.get(
    "/{resume_id}/export/pdf",
    summary="Export resume to PDF",
    description="Download guaranteed one-page ReportLab PDF. Requires approved resume status.",
    dependencies=[Depends(user_rate_limit(max_requests=settings.rate_limit_export_per_minute, window_seconds=60))],
)
def export_pdf(
    resume_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = _resolve_resume_or_404(db, resume_id, current_user)
    try:
        pdf_path = ResumeExportService.export_pdf(db, resume, enforce_approved=True)
        return FileResponse(
            path=str(pdf_path),
            filename=pdf_path.name,
            media_type="application/pdf",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {exc}")


@router.get(
    "/{resume_id}/export/docx",
    summary="Export resume to DOCX",
    description="Download python-docx DOCX matching design system. Requires approved resume status.",
    dependencies=[Depends(user_rate_limit(max_requests=settings.rate_limit_export_per_minute, window_seconds=60))],
)
def export_docx(
    resume_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = _resolve_resume_or_404(db, resume_id, current_user)
    try:
        docx_path = ResumeExportService.export_docx(db, resume, enforce_approved=True)
        return FileResponse(
            path=str(docx_path),
            filename=docx_path.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {exc}")


# ==============================================================================
# 4. ATS Evaluation
# ==============================================================================

@router.post(
    "/{resume_id}/evaluate",
    response_model=ATSEvaluationResponse,
    summary="Run ATS evaluation",
    description="Perform deterministic ATS evaluation (Format 30%, Relevance 50%, Quality 20%) and persist score.",
    dependencies=[Depends(user_rate_limit(max_requests=settings.rate_limit_analysis_per_minute, window_seconds=60))],
)
def evaluate_resume(
    resume_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = _resolve_resume_or_404(db, resume_id, current_user)
    try:
        return ATSEvaluationService.evaluate_resume(db, resume)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"ATS evaluation failed: {exc}")


@router.get(
    "/{resume_id}/evaluations",
    response_model=List[ATSEvaluationResponse],
    summary="List ATS evaluations",
    description="Retrieve all historical ATS evaluation records for a resume.",
)
def list_evaluations(
    resume_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _resolve_resume_or_404(db, resume_id, current_user)
    records = ATSEvaluationService.list_evaluations(db, resume_id)
    return [
        ATSEvaluationResponse(
            id=ev.id,
            resume_id=ev.resume_id,
            overall_score=ev.overall_score,
            format_score=ev.format_score,
            relevance_score=ev.relevance_score,
            quality_score=ev.quality_score,
            score_breakdown={
                "ats_format_compatibility": {"score": ev.format_score, "max": 30},
                "jd_relevance": {"score": ev.relevance_score, "max": 50},
                "content_quality": {"score": ev.quality_score, "max": 20},
            },
            matched_keywords=ev.matched_keywords,
            missing_keywords=ev.missing_keywords,
            critical_issues=ev.critical_issues,
            warnings=ev.warnings,
            suggestions=ev.suggestions,
            disclaimer="This evaluation is a local heuristic estimate and does not guarantee employer or vendor ATS outcomes.",
            created_at=ev.created_at,
        )
        for ev in records
    ]
