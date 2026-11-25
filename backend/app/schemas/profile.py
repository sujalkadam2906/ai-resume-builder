"""Pydantic schemas for candidate profiles and child resources."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------------------
# Common Web Link Schemas
# ------------------------------------------------------------------------------

class LinkItemSchema(BaseModel):
    url: str
    display: str


class ProjectLinkSchema(BaseModel):
    label: str
    url: str


# ------------------------------------------------------------------------------
# Education Schemas
# ------------------------------------------------------------------------------

class EducationBase(BaseModel):
    degree: str = Field(..., description="Academic degree name", examples=["B.Tech Computer Science and Engineering"])
    institution: str = Field(..., description="Educational institution", examples=["Pune Institute of Computer Technology"])
    duration: Optional[str] = Field(None, description="Time duration string", examples=["2021-2025"])
    start_year: Optional[int] = Field(None, description="Start year", examples=[2021])
    end_year: Optional[int] = Field(None, description="Graduation year", examples=[2025])
    cgpa: Optional[str] = Field(None, description="CGPA or grade", examples=["8.50/10"])
    score: Optional[str] = Field(None, description="Score portion", examples=["8.50"])
    scale: Optional[str] = Field(None, description="Grading scale", examples=["10"])
    source: str = Field("verified_both", description="Verification source", examples=["verified_both"])
    display_order: int = Field(0, description="Display sorting order", examples=[0])


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    duration: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    cgpa: Optional[str] = None
    score: Optional[str] = None
    scale: Optional[str] = None
    source: Optional[str] = None
    display_order: Optional[int] = None


class EducationResponse(EducationBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Experience Schemas
# ------------------------------------------------------------------------------

class ExperienceBase(BaseModel):
    role: str = Field(..., description="Job title or role", examples=["Full Stack Developer Intern"])
    organization: str = Field(..., description="Company or organization", examples=["CloudScale Technologies"])
    duration: Optional[str] = Field(None, description="Employment timeframe", examples=["Jan 2024 - Jun 2024"])
    metrics: Optional[str] = Field(None, description="Summary metric", examples=["40% latency reduction"])
    description: Optional[str] = Field(None, description="Narrative summary")
    bullets: List[str] = Field(default_factory=list, description="Key accomplishment bullet points")
    source: str = Field("verified_both", description="Provenance tracking", examples=["verified_both"])
    display_order: int = Field(0, description="Display order", examples=[0])


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    role: Optional[str] = None
    organization: Optional[str] = None
    duration: Optional[str] = None
    metrics: Optional[str] = None
    description: Optional[str] = None
    bullets: Optional[List[str]] = None
    source: Optional[str] = None
    display_order: Optional[int] = None


class ExperienceResponse(ExperienceBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Skill Schemas
# ------------------------------------------------------------------------------

class SkillBase(BaseModel):
    category: str = Field(..., description="Skill category key", examples=["languages", "backend_and_java", "frontend"])
    skill_name: str = Field(..., description="Technical competency title", examples=["Python", "FastAPI"])
    display_order: int = Field(0, description="Sort order within category", examples=[0])


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    category: Optional[str] = None
    skill_name: Optional[str] = None
    display_order: Optional[int] = None


class SkillResponse(SkillBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BulkSkillUpdate(BaseModel):
    skills_by_category: Dict[str, List[str]] = Field(
        ...,
        description="Dictionary mapping categories to lists of skill strings",
        examples=[{"languages": ["Python", "Java", "TypeScript"]}]
    )


# ------------------------------------------------------------------------------
# Project Schemas
# ------------------------------------------------------------------------------

class ProjectBase(BaseModel):
    slug: str = Field(..., description="Unique project slug within profile", examples=["cloud_canvas_ui"])
    title: str = Field(..., description="Project title", examples=["CloudCanvas UI"])
    subtitle: Optional[str] = Field(None, description="Tech stack headline", examples=["React 18 · TypeScript · Tailwind CSS"])
    notice: Optional[str] = Field(None, description="Demonstration or synthetic notice")
    is_fixed_project: bool = Field(False, description="Pinning safeguard flag")
    fixed_position: Optional[int] = Field(None, description="Pinned position in resume", examples=[2])
    display_order: int = Field(0, description="Display order", examples=[0])
    categories: List[str] = Field(default_factory=list, description="Domain categories")
    skills: List[str] = Field(default_factory=list, description="Specific technologies used")
    links: List[ProjectLinkSchema] = Field(default_factory=list, description="Live web hyperlinks")
    bullets: List[str] = Field(default_factory=list, description="Impact bullet points")
    metrics: List[str] = Field(default_factory=list, description="Quantified results")
    evidence_source: Optional[str] = Field(None, description="Verification evidence")
    verification_status: str = Field("verified", description="Integrity status", examples=["verified"])


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    notice: Optional[str] = None
    is_fixed_project: Optional[bool] = None
    fixed_position: Optional[int] = None
    display_order: Optional[int] = None
    categories: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    links: Optional[List[ProjectLinkSchema]] = None
    bullets: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    evidence_source: Optional[str] = None
    verification_status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Certification Schemas
# ------------------------------------------------------------------------------

class CertificationBase(BaseModel):
    name: str = Field(..., description="Certification credential title", examples=["AWS Certified Developer - Associate"])
    issuer: Optional[str] = Field(None, description="Issuing authority", examples=["Amazon Web Services"])
    issue_date: Optional[str] = Field(None, description="Issue date or year", examples=["2024"])
    display_order: int = Field(0, description="Display sort order", examples=[0])


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    display_order: Optional[int] = None


class CertificationResponse(CertificationBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Achievement Schemas
# ------------------------------------------------------------------------------

class AchievementBase(BaseModel):
    title: str = Field(..., description="Award or achievement title", examples=["1st Place National Hackathon"])
    description: Optional[str] = Field(None, description="Contextual description")
    bullets: List[str] = Field(default_factory=list, description="Achievement highlights")
    source: str = Field("verified_both", description="Verification source", examples=["verified_both"])
    display_order: int = Field(0, description="Display sort order", examples=[0])


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    bullets: Optional[List[str]] = None
    source: Optional[str] = None
    display_order: Optional[int] = None


class AchievementResponse(AchievementBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Professional Development Schemas
# ------------------------------------------------------------------------------

class ProfessionalDevelopmentBase(BaseModel):
    title: str = Field(..., description="Training course or workshop title", examples=["Advanced Distributed Systems"])
    organization: str = Field(..., description="Providing organization or platform", examples=["Coursera"])
    date: Optional[str] = Field(None, description="Completion timeframe", examples=["2024"])
    bullets: List[str] = Field(default_factory=list, description="Key syllabus learnings")
    source: Optional[str] = Field(None, description="Evidence document")
    conflict_note: Optional[str] = Field(None, description="Reconciliation notes")
    display_order: int = Field(0, description="Display sort order", examples=[0])


class ProfessionalDevelopmentCreate(ProfessionalDevelopmentBase):
    pass


class ProfessionalDevelopmentUpdate(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    date: Optional[str] = None
    bullets: Optional[List[str]] = None
    source: Optional[str] = None
    conflict_note: Optional[str] = None
    display_order: Optional[int] = None


class ProfessionalDevelopmentResponse(ProfessionalDevelopmentBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Candidate Profile Schemas
# ------------------------------------------------------------------------------

class CandidateProfileSummary(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = Field(None, description="Supabase Auth user UUID owner")
    slug: str = Field(..., description="Candidate unique slug", examples=["sujal", "demo_candidate"])
    full_name: str = Field(..., description="Candidate full name", examples=["Sujal Sunil Kadam"])
    display_name: str = Field(..., description="Header display name", examples=["SUJAL KADAM"])
    professional_headline: Optional[str] = Field(None, description="Primary professional headline")
    location: Optional[str] = Field(None, description="Location", examples=["Bengaluru, India"])
    is_synthetic: bool = Field(False, description="Whether this is a synthetic demonstration profile")
    is_archived: bool = Field(False, description="Soft deletion archive status")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateProfileDetail(CandidateProfileSummary):
    email: Optional[str] = None
    phone: Optional[str] = None
    open_to_relocate: bool = True
    immediate_joiner: bool = True
    professional_summary: Optional[str] = None
    headlines: Dict[str, Any] = Field(default_factory=dict)
    summaries: Dict[str, Any] = Field(default_factory=dict)
    links: Dict[str, Any] = Field(default_factory=dict)
    config_rules: Dict[str, Any] = Field(default_factory=dict)

    # Child resources
    educations: List[EducationResponse] = Field(default_factory=list)
    experiences: List[ExperienceResponse] = Field(default_factory=list)
    skills: List[SkillResponse] = Field(default_factory=list)
    projects: List[ProjectResponse] = Field(default_factory=list)
    certifications: List[CertificationResponse] = Field(default_factory=list)
    achievements: List[AchievementResponse] = Field(default_factory=list)
    professional_developments: List[ProfessionalDevelopmentResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CandidateProfileCreate(BaseModel):
    user_id: Optional[uuid.UUID] = Field(None, description="Supabase Auth user UUID owner")
    slug: str = Field(..., pattern=r"^[a-z0-9_-]+$", description="Lowercase alphanumeric slug with underscores/hyphens", examples=["john_doe"])
    full_name: str = Field(..., description="Candidate full legal name", examples=["John Doe"])
    display_name: Optional[str] = Field(None, description="Header display name", examples=["JOHN DOE"])
    email: Optional[str] = Field(None, examples=["john.doe@example.com"])
    phone: Optional[str] = Field(None, examples=["+91 9876543210"])
    location: Optional[str] = Field(None, examples=["Pune, Maharashtra, India"])
    open_to_relocate: bool = True
    immediate_joiner: bool = True
    professional_headline: Optional[str] = None
    professional_summary: Optional[str] = None
    headlines: Dict[str, Any] = Field(default_factory=dict)
    summaries: Dict[str, Any] = Field(default_factory=dict)
    links: Dict[str, Any] = Field(default_factory=dict)
    config_rules: Dict[str, Any] = Field(default_factory=dict)
    is_synthetic: bool = False

    # Optional initial children
    educations: Optional[List[EducationCreate]] = None
    experiences: Optional[List[ExperienceCreate]] = None
    skills: Optional[List[SkillCreate]] = None
    projects: Optional[List[ProjectCreate]] = None
    certifications: Optional[List[CertificationCreate]] = None
    achievements: Optional[List[AchievementCreate]] = None
    professional_developments: Optional[List[ProfessionalDevelopmentCreate]] = None


class CandidateProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    open_to_relocate: Optional[bool] = None
    immediate_joiner: Optional[bool] = None
    professional_headline: Optional[str] = None
    professional_summary: Optional[str] = None
    headlines: Optional[Dict[str, Any]] = None
    summaries: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None
    config_rules: Optional[Dict[str, Any]] = None
    is_synthetic: Optional[bool] = None


class CandidateProfileClone(BaseModel):
    new_slug: Optional[str] = Field(None, description="Optional custom slug for the cloned profile")
    new_name: Optional[str] = Field(None, description="Optional custom full name for the cloned profile")


class ProfilePaginationResponse(BaseModel):
    items: List[CandidateProfileSummary]
    total: int
    page: int
    size: int
    pages: int
