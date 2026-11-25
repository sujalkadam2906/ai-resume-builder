"""SQLAlchemy models for Job Descriptions, Resumes, Versions, ATS Evaluations, and File Assets."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base, JSONVariant, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.candidate import CandidateProfile


class JobDescription(Base, TimestampMixin):
    """Target job description, parsed skills, and requirement matrix."""

    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_skills: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    requirement_matrix: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, default=dict, nullable=False)
    match_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    profile: Mapped[Optional["CandidateProfile"]] = relationship(back_populates="job_descriptions")
    resumes: Mapped[List["Resume"]] = relationship(
        back_populates="job_description",
        cascade="all, delete-orphan",
    )


class Resume(Base, TimestampMixin):
    """Resume instance tailored for a candidate profile and target JD."""

    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_description_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("job_descriptions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    resume_title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    editable_manifest: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, default=dict, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="resumes")
    job_description: Mapped[Optional["JobDescription"]] = relationship(back_populates="resumes")
    versions: Mapped[List["ResumeVersion"]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeVersion.version_number",
    )
    ats_evaluations: Mapped[List["ATSEvaluation"]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
    )


class ResumeVersion(Base, TimestampMixin):
    """Immutable snapshot of a resume generation or manual edit revision."""

    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    manifest_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, default=dict, nullable=False)
    pdf_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    docx_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preview_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ats_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ats_analysis: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, default=dict, nullable=False)

    resume: Mapped["Resume"] = relationship(back_populates="versions")


class ATSEvaluation(Base, TimestampMixin):
    """Detailed ATS scoring and keyword match analysis for a resume."""

    __tablename__ = "ats_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    format_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    relevance_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    matched_keywords: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    missing_keywords: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    critical_issues: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    warnings: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    suggestions: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)

    resume: Mapped["Resume"] = relationship(back_populates="ats_evaluations")


class FileAsset(Base, TimestampMixin):
    """Metadata for uploaded and generated document assets in local/cloud storage."""

    __tablename__ = "file_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    profile: Mapped[Optional["CandidateProfile"]] = relationship(back_populates="file_assets")
