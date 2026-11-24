"""SQLAlchemy models export for AI Resume Builder Platform."""

from backend.app.database.base import Base, TimestampMixin, JSONVariant
from backend.app.models.candidate import (
    CandidateProfile,
    Education,
    Experience,
    Skill,
    Project,
    Certification,
    Achievement,
    ProfessionalDevelopment,
)
from backend.app.models.resume import (
    JobDescription,
    Resume,
    ResumeVersion,
    ATSEvaluation,
    FileAsset,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "JSONVariant",
    "CandidateProfile",
    "Education",
    "Experience",
    "Skill",
    "Project",
    "Certification",
    "Achievement",
    "ProfessionalDevelopment",
    "JobDescription",
    "Resume",
    "ResumeVersion",
    "ATSEvaluation",
    "FileAsset",
]
