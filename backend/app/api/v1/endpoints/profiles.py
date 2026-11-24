"""Candidate Profile and child resource API endpoints."""

import math
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.profile import (
    CandidateProfileSummary,
    CandidateProfileDetail,
    CandidateProfileCreate,
    CandidateProfileUpdate,
    ProfilePaginationResponse,
    EducationCreate,
    EducationUpdate,
    EducationResponse,
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    CertificationCreate,
    CertificationUpdate,
    CertificationResponse,
    AchievementCreate,
    AchievementUpdate,
    AchievementResponse,
    ProfessionalDevelopmentCreate,
    ProfessionalDevelopmentUpdate,
    ProfessionalDevelopmentResponse,
)
from backend.app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["Candidate Profiles"])


def _resolve_profile_or_404(
    session: Session,
    profile_identifier: str,
    check_archived_mutation: bool = False,
):
    """Helper to resolve profile by slug or UUID, raising 404 if not found.
    
    If check_archived_mutation is True and profile is archived, raises 400 Bad Request.
    """
    profile = ProfileService.get_profile_by_id_or_slug(session, profile_identifier)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile '{profile_identifier}' not found.",
        )
    if check_archived_mutation and (profile.config_rules or {}).get("is_archived", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Candidate profile '{profile.slug}' is archived. Restore the profile before making modifications.",
        )
    return profile


# ==============================================================================
# 1. Candidate Profile Root Endpoints
# ==============================================================================

@router.get(
    "",
    response_model=ProfilePaginationResponse,
    summary="List candidate profiles",
    description="Retrieve paginated candidate profiles with optional inclusion of archived profiles.",
)
def list_profiles(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_archived: bool = Query(False, description="Whether to include soft-deleted/archived profiles"),
    db: Session = Depends(get_db),
):
    items, total = ProfileService.list_profiles(db, page=page, size=size, include_archived=include_archived)
    pages = math.ceil(total / size) if size > 0 else 1

    summary_items = [
        CandidateProfileSummary(
            id=p.id,
            slug=p.slug,
            full_name=p.full_name,
            display_name=p.display_name,
            professional_headline=p.professional_headline,
            location=p.location,
            is_synthetic=p.is_synthetic,
            is_archived=(p.config_rules or {}).get("is_archived", False),
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in items
    ]

    return ProfilePaginationResponse(
        items=summary_items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.post(
    "",
    response_model=CandidateProfileDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create candidate profile",
    description="Register a new candidate profile with unique slug and optional initial sections.",
)
def create_profile(
    data: CandidateProfileCreate,
    db: Session = Depends(get_db),
):
    try:
        profile = ProfileService.create_profile(db, data)
        return profile
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{profile_id}",
    response_model=CandidateProfileDetail,
    summary="Get complete candidate profile",
    description="Retrieve full candidate profile by UUID or slug, including all nested child resources.",
)
def get_profile(
    profile_id: str,
    db: Session = Depends(get_db),
):
    return _resolve_profile_or_404(db, profile_id)


@router.patch(
    "/{profile_id}",
    response_model=CandidateProfileDetail,
    summary="Patch candidate profile",
    description="Partially update candidate demographics and configuration rules.",
)
def update_profile(
    profile_id: str,
    data: CandidateProfileUpdate,
    db: Session = Depends(get_db),
):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    return ProfileService.update_profile(db, profile, data)


@router.delete(
    "/{profile_id}",
    summary="Archive candidate profile (soft-delete)",
    description="Soft-deletes candidate profile by flagging it as archived without deleting data.",
)
def archive_profile(
    profile_id: str,
    db: Session = Depends(get_db),
):
    profile = _resolve_profile_or_404(db, profile_id)
    ProfileService.archive_profile(db, profile)
    return {
        "status": "archived",
        "profile_id": str(profile.id),
        "slug": profile.slug,
        "message": f"Candidate profile '{profile.slug}' successfully archived.",
    }


@router.post(
    "/{profile_id}/restore",
    summary="Restore archived candidate profile",
    description="Restores a previously soft-deleted candidate profile to active listings.",
)
def restore_profile(
    profile_id: str,
    db: Session = Depends(get_db),
):
    profile = _resolve_profile_or_404(db, profile_id)
    ProfileService.restore_profile(db, profile)
    return {
        "status": "restored",
        "profile_id": str(profile.id),
        "slug": profile.slug,
        "message": f"Candidate profile '{profile.slug}' successfully restored.",
    }


# ==============================================================================
# 2. Education Child Endpoints
# ==============================================================================

@router.get("/{profile_id}/education", response_model=List[EducationResponse], summary="List education records")
def list_education(profile_id: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    return ProfileService.list_educations(db, profile.id)


@router.post("/{profile_id}/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED, summary="Add education record")
def create_education(profile_id: str, data: EducationCreate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    return ProfileService.create_education(db, profile.id, data)


@router.get("/{profile_id}/education/{education_id}", response_model=EducationResponse, summary="Get education record")
def get_education(profile_id: str, education_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    edu = ProfileService.get_education(db, profile.id, education_id)
    if not edu:
        raise HTTPException(status_code=404, detail="Education record not found for this profile.")
    return edu


@router.patch("/{profile_id}/education/{education_id}", response_model=EducationResponse, summary="Update education record")
def update_education(profile_id: str, education_id: uuid.UUID, data: EducationUpdate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    edu = ProfileService.update_education(db, profile.id, education_id, data)
    if not edu:
        raise HTTPException(status_code=404, detail="Education record not found for this profile.")
    return edu


@router.delete("/{profile_id}/education/{education_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete education record")
def delete_education(profile_id: str, education_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    if not ProfileService.delete_education(db, profile.id, education_id):
        raise HTTPException(status_code=404, detail="Education record not found for this profile.")
    return None


# ==============================================================================
# 3. Experience Child Endpoints
# ==============================================================================

@router.get("/{profile_id}/experience", response_model=List[ExperienceResponse], summary="List experience records")
def list_experience(profile_id: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    return ProfileService.list_experiences(db, profile.id)


@router.post("/{profile_id}/experience", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED, summary="Add experience record")
def create_experience(profile_id: str, data: ExperienceCreate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    return ProfileService.create_experience(db, profile.id, data)


@router.get("/{profile_id}/experience/{experience_id}", response_model=ExperienceResponse, summary="Get experience record")
def get_experience(profile_id: str, experience_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    exp = ProfileService.get_experience(db, profile.id, experience_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experience record not found for this profile.")
    return exp


@router.patch("/{profile_id}/experience/{experience_id}", response_model=ExperienceResponse, summary="Update experience record")
def update_experience(profile_id: str, experience_id: uuid.UUID, data: ExperienceUpdate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    exp = ProfileService.update_experience(db, profile.id, experience_id, data)
    if not exp:
        raise HTTPException(status_code=404, detail="Experience record not found for this profile.")
    return exp


@router.delete("/{profile_id}/experience/{experience_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete experience record")
def delete_experience(profile_id: str, experience_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    if not ProfileService.delete_experience(db, profile.id, experience_id):
        raise HTTPException(status_code=404, detail="Experience record not found for this profile.")
    return None


# ==============================================================================
# 4. Skills Child Endpoints
# ==============================================================================

@router.get("/{profile_id}/skills", response_model=List[SkillResponse], summary="List categorized skills")
def list_skills(profile_id: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    return ProfileService.list_skills(db, profile.id)


@router.post("/{profile_id}/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED, summary="Add single skill")
def create_skill(profile_id: str, data: SkillCreate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    return ProfileService.create_skill(db, profile.id, data)


@router.get("/{profile_id}/skills/{skill_id}", response_model=SkillResponse, summary="Get skill record")
def get_skill(profile_id: str, skill_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    sk = ProfileService.get_skill(db, profile.id, skill_id)
    if not sk:
        raise HTTPException(status_code=404, detail="Skill record not found for this profile.")
    return sk


@router.patch("/{profile_id}/skills/{skill_id}", response_model=SkillResponse, summary="Update skill record")
def update_skill(profile_id: str, skill_id: uuid.UUID, data: SkillUpdate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    sk = ProfileService.update_skill(db, profile.id, skill_id, data)
    if not sk:
        raise HTTPException(status_code=404, detail="Skill record not found for this profile.")
    return sk


@router.delete("/{profile_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete skill record")
def delete_skill(profile_id: str, skill_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    if not ProfileService.delete_skill(db, profile.id, skill_id):
        raise HTTPException(status_code=404, detail="Skill record not found for this profile.")
    return None


# ==============================================================================
# 5. Projects Child Endpoints & Pinning Safeguards
# ==============================================================================

@router.get("/{profile_id}/projects", response_model=List[ProjectResponse], summary="List candidate projects")
def list_projects(profile_id: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    return ProfileService.list_projects(db, profile.id)


@router.post("/{profile_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create project")
def create_project(profile_id: str, data: ProjectCreate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    try:
        return ProfileService.create_project(db, profile.id, data)
    except ValueError as exc:
        err_msg = str(exc)
        if "already exists" in err_msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


@router.get("/{profile_id}/projects/{project_identifier}", response_model=ProjectResponse, summary="Get project by UUID or slug")
def get_project(profile_id: str, project_identifier: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    proj = ProfileService.get_project(db, profile.id, project_identifier)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_identifier}' not found for this profile.")
    return proj


@router.patch("/{profile_id}/projects/{project_identifier}", response_model=ProjectResponse, summary="Update project")
def update_project(
    profile_id: str,
    project_identifier: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    try:
        proj = ProfileService.update_project(db, profile.id, project_identifier, data)
        if not proj:
            raise HTTPException(status_code=404, detail=f"Project '{project_identifier}' not found for this profile.")
        return proj
    except ValueError as exc:
        # Enforce business safeguard against altering fixed position
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{profile_id}/projects/{project_identifier}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
def delete_project(profile_id: str, project_identifier: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    try:
        success = ProfileService.delete_project(db, profile.id, project_identifier)
        if not success:
            raise HTTPException(status_code=404, detail=f"Project '{project_identifier}' not found for this profile.")
        return None
    except ValueError as exc:
        # Enforce business safeguard against deleting fixed projects
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ==============================================================================
# 6. Certifications Child Endpoints
# ==============================================================================

@router.get("/{profile_id}/certifications", response_model=List[CertificationResponse], summary="List certifications")
def list_certifications(profile_id: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    return ProfileService.list_certifications(db, profile.id)


@router.post("/{profile_id}/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED, summary="Add certification")
def create_certification(profile_id: str, data: CertificationCreate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    return ProfileService.create_certification(db, profile.id, data)


@router.get("/{profile_id}/certifications/{cert_id}", response_model=CertificationResponse, summary="Get certification")
def get_certification(profile_id: str, cert_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    c = ProfileService.get_certification(db, profile.id, cert_id)
    if not c:
        raise HTTPException(status_code=404, detail="Certification not found for this profile.")
    return c


@router.patch("/{profile_id}/certifications/{cert_id}", response_model=CertificationResponse, summary="Update certification")
def update_certification(profile_id: str, cert_id: uuid.UUID, data: CertificationUpdate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    c = ProfileService.update_certification(db, profile.id, cert_id, data)
    if not c:
        raise HTTPException(status_code=404, detail="Certification not found for this profile.")
    return c


@router.delete("/{profile_id}/certifications/{cert_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete certification")
def delete_certification(profile_id: str, cert_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    if not ProfileService.delete_certification(db, profile.id, cert_id):
        raise HTTPException(status_code=404, detail="Certification not found for this profile.")
    return None


# ==============================================================================
# 7. Achievements Child Endpoints
# ==============================================================================

@router.get("/{profile_id}/achievements", response_model=List[AchievementResponse], summary="List achievements")
def list_achievements(profile_id: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    return ProfileService.list_achievements(db, profile.id)


@router.post("/{profile_id}/achievements", response_model=AchievementResponse, status_code=status.HTTP_201_CREATED, summary="Add achievement")
def create_achievement(profile_id: str, data: AchievementCreate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    return ProfileService.create_achievement(db, profile.id, data)


@router.get("/{profile_id}/achievements/{ach_id}", response_model=AchievementResponse, summary="Get achievement")
def get_achievement(profile_id: str, ach_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    ach = ProfileService.get_achievement(db, profile.id, ach_id)
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found for this profile.")
    return ach


@router.patch("/{profile_id}/achievements/{ach_id}", response_model=AchievementResponse, summary="Update achievement")
def update_achievement(profile_id: str, ach_id: uuid.UUID, data: AchievementUpdate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    ach = ProfileService.update_achievement(db, profile.id, ach_id, data)
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found for this profile.")
    return ach


@router.delete("/{profile_id}/achievements/{ach_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete achievement")
def delete_achievement(profile_id: str, ach_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    if not ProfileService.delete_achievement(db, profile.id, ach_id):
        raise HTTPException(status_code=404, detail="Achievement not found for this profile.")
    return None


# ==============================================================================
# 8. Professional Development Child Endpoints
# ==============================================================================

@router.get("/{profile_id}/professional-development", response_model=List[ProfessionalDevelopmentResponse], summary="List professional developments")
def list_professional_development(profile_id: str, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    return ProfileService.list_professional_developments(db, profile.id)


@router.post("/{profile_id}/professional-development", response_model=ProfessionalDevelopmentResponse, status_code=status.HTTP_201_CREATED, summary="Add professional development")
def create_professional_development(profile_id: str, data: ProfessionalDevelopmentCreate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    return ProfileService.create_professional_development(db, profile.id, data)


@router.get("/{profile_id}/professional-development/{pd_id}", response_model=ProfessionalDevelopmentResponse, summary="Get professional development")
def get_professional_development(profile_id: str, pd_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id)
    pd = ProfileService.get_professional_development(db, profile.id, pd_id)
    if not pd:
        raise HTTPException(status_code=404, detail="Professional development record not found for this profile.")
    return pd


@router.patch("/{profile_id}/professional-development/{pd_id}", response_model=ProfessionalDevelopmentResponse, summary="Update professional development")
def update_professional_development(profile_id: str, pd_id: uuid.UUID, data: ProfessionalDevelopmentUpdate, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    pd = ProfileService.update_professional_development(db, profile.id, pd_id, data)
    if not pd:
        raise HTTPException(status_code=404, detail="Professional development record not found for this profile.")
    return pd


@router.delete("/{profile_id}/professional-development/{pd_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete professional development")
def delete_professional_development(profile_id: str, pd_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = _resolve_profile_or_404(db, profile_id, check_archived_mutation=True)
    if not ProfileService.delete_professional_development(db, profile.id, pd_id):
        raise HTTPException(status_code=404, detail="Professional development record not found for this profile.")
    return None
