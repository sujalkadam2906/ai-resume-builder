"""Complete Resume Content Manifest model used for rendering documents."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ..profile.models import (
    AchievementItem,
    EducationItem,
    LeadershipItem,
    LinkItem,
    LinksProfile,
    PersonalInfo,
    ProfessionalDevelopmentItem,
    ProjectItem,
    ResearchPublication,
)


class ManifestProject(BaseModel):
    id: str
    title: str
    subtitle: str
    is_fixed: bool = False
    bullets: List[str] = Field(default_factory=list)
    links: List[Dict[str, str]] = Field(default_factory=list)


class ResumeContentManifest(BaseModel):
    target_company: str
    target_role: str
    model_used: str
    personal_info: PersonalInfo
    links: LinksProfile
    headline: str
    summary: str
    ordered_skills: Dict[str, List[str]]
    projects: List[ManifestProject]
    leadership: List[LeadershipItem]
    professional_development: List[ProfessionalDevelopmentItem] = Field(default_factory=list)
    education: List[EducationItem]
    achievements: List[AchievementItem]
    research_publications: List[ResearchPublication]
    certifications: List[str]
    tailoring_notes: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
