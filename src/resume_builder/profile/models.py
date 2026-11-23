"""Pydantic models for candidate profile, projects, and metadata."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    full_name: str
    display_name: str
    phone: str
    email: str
    location: str
    open_to_relocate: bool = True
    immediate_joiner: bool = True


class LinkItem(BaseModel):
    url: str
    display: str


class LinksProfile(BaseModel):
    linkedin: LinkItem
    github: LinkItem
    portfolio: LinkItem


class EducationItem(BaseModel):
    degree: str
    institution: str
    duration: str
    start_year: int = 2022
    end_year: int = 2026
    cgpa: str = "8.23 / 10"
    score: str = "8.23"
    scale: str = "10"
    source: str = "verified_both"


class LeadershipItem(BaseModel):
    id: str
    role: str
    organization: str
    duration: Optional[str] = "2024 – 2026"
    metrics: Optional[str] = None
    description: str
    bullets: List[str] = Field(default_factory=list)
    source: str = "verified_both"


class ProfessionalDevelopmentItem(BaseModel):
    id: str
    title: str
    organization: str
    date: str
    bullets: List[str] = Field(default_factory=list)
    source: str = "Sujal_Kadam_Resume_new.pdf"
    conflict_note: Optional[str] = None


class AchievementItem(BaseModel):
    id: str
    title: str
    description: str
    bullets: List[str] = Field(default_factory=list)
    source: str = "verified_both"


class ResearchPublication(BaseModel):
    title: str
    venue: str
    year: int = 2026
    doi: Optional[str] = None
    doi_url: Optional[str] = None


class TechnicalSkills(BaseModel):
    languages: List[str] = Field(default_factory=list)
    backend_and_java: List[str] = Field(default_factory=list)
    databases_and_sql: List[str] = Field(default_factory=list)
    cloud_devops_and_deployment: List[str] = Field(default_factory=list)
    frontend: List[str] = Field(default_factory=list)
    core_cs_and_ml: List[str] = Field(default_factory=list)
    testing_and_tools: List[str] = Field(default_factory=list)

    def get_all_skills_flat(self) -> List[str]:
        all_s = []
        for lst in [
            self.languages,
            self.backend_and_java,
            self.databases_and_sql,
            self.cloud_devops_and_deployment,
            self.frontend,
            self.core_cs_and_ml,
            self.testing_and_tools,
        ]:
            all_s.extend(lst)
        return all_s


class ProjectLink(BaseModel):
    label: str
    url: str


class ProjectItem(BaseModel):
    id: str
    title: str
    subtitle: str
    notice: Optional[str] = None
    is_fixed_project: bool = False
    fixed_position: Optional[int] = None
    categories: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    links: List[ProjectLink] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    evidence_source: str
    verification_status: str = "verified"


class ReconciledConflict(BaseModel):
    field: str
    detail: str


class MasterProfile(BaseModel):
    personal_info: PersonalInfo
    links: LinksProfile
    headlines: Union[Dict[str, str], List[str]] = Field(default_factory=dict)
    summaries: Union[Dict[str, str], List[str]] = Field(default_factory=dict)
    education: List[EducationItem] = Field(default_factory=list)
    technical_skills: TechnicalSkills
    leadership_and_experience: List[LeadershipItem] = Field(default_factory=list)
    professional_development: List[ProfessionalDevelopmentItem] = Field(default_factory=list)
    achievements: List[AchievementItem] = Field(default_factory=list)
    research_publications: List[ResearchPublication] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    reconciliation_metadata: Optional[Dict[str, Any]] = None


# ==============================================================================
# MULTI-PROFILE CONFIGURATION & REGISTRY MODELS
# ==============================================================================


class FixedProjectRule(BaseModel):
    id: str = "bearing_fault_diagnosis"
    title: str = "Bearing Fault Diagnosis Using Machine Learning"
    position: int = 2


class ProjectSelectionConfig(BaseModel):
    target_count: int = 4
    has_fixed_project: bool = True
    fixed_project: Optional[FixedProjectRule] = Field(default_factory=FixedProjectRule)
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "required_skills_coverage": 0.45,
            "responsibilities_alignment": 0.25,
            "tech_stack_similarity": 0.20,
            "domain_relevance": 0.10,
        }
    )


class HeadlineRule(BaseModel):
    mode: str = "permanent"  # "permanent" or "dynamic"
    permanent_headline: Optional[str] = None


class SummaryRule(BaseModel):
    mode: str = "permanent"  # "permanent" or "dynamic"
    permanent_summary: Optional[str] = None


class ProfileConfig(BaseModel):
    profile_id: str
    display_name: str
    is_synthetic: bool = False
    headline_rule: HeadlineRule = Field(default_factory=HeadlineRule)
    summary_rule: SummaryRule = Field(default_factory=SummaryRule)
    prohibited_terms: List[str] = Field(default_factory=list)
    project_selection: ProjectSelectionConfig = Field(
        default_factory=ProjectSelectionConfig
    )
    sections_order: List[str] = Field(
        default_factory=lambda: [
            "header",
            "summary",
            "technical_skills",
            "projects",
            "professional_development",
            "education",
            "leadership_and_achievements",
            "certifications",
        ]
    )
    theme: str = "editorial_teal_copper"


class ProfileRegistryEntry(BaseModel):
    profile_id: str
    candidate_display_name: str
    created_at: str
    updated_at: str
    source_status: str = "verified_source"
    is_active: bool = True
    schema_version: str = "2.0.0"


class ProfileRegistry(BaseModel):
    profiles: Dict[str, ProfileRegistryEntry] = Field(default_factory=dict)
