"""Pydantic schemas for Job Descriptions, Candidate Matching, Resume Generation, Approval, and ATS Evaluation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# 1. Job Description Schemas
# ==============================================================================

class JobDescriptionBase(BaseModel):
    job_title: Optional[str] = Field(None, max_length=255, description="Job role or title", examples=["Full Stack Developer"])
    company_name: Optional[str] = Field(None, max_length=255, description="Hiring company name", examples=["Google"])
    raw_text: str = Field(..., min_length=20, max_length=50000, description="Full job description text")
    source_url: Optional[str] = Field(None, max_length=2048, description="Optional job posting source URL")


class JobDescriptionCreate(JobDescriptionBase):
    profile_id: Optional[str] = Field(None, description="Target candidate profile UUID or slug")


class JobDescriptionUpdate(BaseModel):
    job_title: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    raw_text: Optional[str] = Field(None, min_length=20, max_length=50000)
    source_url: Optional[str] = Field(None, max_length=2048)


class JobDescriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    profile_id: Optional[uuid.UUID] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    raw_text: str
    source_url: Optional[str] = None
    extracted_skills: List[str] = Field(default_factory=list)
    match_percentage: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionPaginationResponse(BaseModel):
    items: List[JobDescriptionResponse]
    total: int
    page: int
    size: int
    pages: int


class JobDescriptionAnalysisResponse(BaseModel):
    id: uuid.UUID
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    technical_stack: Dict[str, List[str]] = Field(default_factory=dict)
    responsibilities: List[str] = Field(default_factory=list)
    experience_requirements: Optional[str] = None
    education_requirements: Optional[str] = None
    domain: Optional[str] = None
    important_keywords: List[str] = Field(default_factory=list)
    match_percentage: Optional[float] = None
    is_ai_extracted: bool = False
    confidence_note: str = "Analysis extracted for human review. Verify before treating as definitive fact."


# ==============================================================================
# 2. Candidate Matching & Recommendation Schemas
# ==============================================================================

class ProjectMatchScore(BaseModel):
    project_id: str
    title: str
    subtitle: str
    is_fixed: bool = False
    fixed_position: Optional[int] = None
    overall_score: float
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Component breakdown: required_skills (45%), responsibilities (25%), tech_stack (20%), domain (10%)",
    )
    ranking_explanation: str


class CandidateMatchResponse(BaseModel):
    candidate_id: uuid.UUID
    candidate_slug: str
    job_description_id: uuid.UUID
    overall_match_percentage: float
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    unsupported_skills: List[str] = Field(default_factory=list)
    recommended_projects: List[ProjectMatchScore] = Field(default_factory=list)
    project_selection_warnings: Optional[str] = None


# ==============================================================================
# 3. Resume Generation & Editing Schemas
# ==============================================================================

class ResumeGenerateRequest(BaseModel):
    profile_id: str = Field(..., description="Candidate profile UUID or slug")
    job_description_id: uuid.UUID = Field(..., description="Target Job Description UUID")
    selected_project_ids: Optional[List[str]] = Field(
        None,
        description="Optional explicit project selection (max 4). If omitted, recommended projects are used.",
    )
    selected_skills: Optional[List[str]] = Field(None, description="Optional custom skill selections")
    provider_override: Optional[str] = Field(None, description="Optional AI provider override e.g. 'gemini', 'groq', 'offline'")
    resume_title: Optional[str] = Field(None, description="Optional custom title for this resume")


class ResumeUpdateRequest(BaseModel):
    resume_title: Optional[str] = None
    editable_manifest: Optional[Dict[str, Any]] = None


class ResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    profile_id: uuid.UUID
    job_description_id: Optional[uuid.UUID] = None
    resume_title: str
    status: str = Field("draft", description="'draft' or 'approved'")
    current_version: int
    editable_manifest: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumePaginationResponse(BaseModel):
    items: List[ResumeResponse]
    total: int
    page: int
    size: int
    pages: int


class ResumeApprovalResponse(BaseModel):
    id: uuid.UUID
    status: str = "approved"
    approved_version: int
    message: str


class ResumeVersionResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    version_number: int
    manifest_snapshot: Dict[str, Any] = Field(default_factory=dict)
    pdf_storage_key: Optional[str] = None
    docx_storage_key: Optional[str] = None
    preview_storage_key: Optional[str] = None
    ats_score: Optional[int] = None
    ats_analysis: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 4. ATS Evaluation Schemas
# ==============================================================================

class ATSEvaluationResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    overall_score: int
    format_score: Optional[int] = None
    relevance_score: Optional[int] = None
    quality_score: Optional[int] = None
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "This evaluation is a local heuristic estimate and does not guarantee employer or vendor ATS outcomes."
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
