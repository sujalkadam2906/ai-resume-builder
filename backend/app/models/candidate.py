"""SQLAlchemy models for candidate profiles and candidate details."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base, JSONVariant, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.resume import FileAsset, JobDescription, Resume


class CandidateProfile(Base, TimestampMixin):
    """Primary candidate profile record representing an individual."""

    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    open_to_relocate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    immediate_joiner: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    professional_headline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    professional_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headlines: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, default=dict, nullable=False)
    summaries: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, default=dict, nullable=False)
    links: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, default=dict, nullable=False)
    config_rules: Mapped[Dict[str, Any]] = mapped_column(JSONVariant, default=dict, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @property
    def is_archived(self) -> bool:
        """Dynamic flag indicating if profile is archived/soft-deleted."""
        return bool((self.config_rules or {}).get("is_archived", False))

    @property
    def archived_at(self) -> Optional[str]:
        """Timestamp when profile was soft-deleted."""
        return (self.config_rules or {}).get("archived_at", None)

    # Relationships with deliberate cascade deletion
    educations: Mapped[List["Education"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Education.display_order",
    )
    experiences: Mapped[List["Experience"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Experience.display_order",
    )
    skills: Mapped[List["Skill"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Skill.display_order",
    )
    projects: Mapped[List["Project"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Project.display_order",
    )
    certifications: Mapped[List["Certification"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Certification.display_order",
    )
    achievements: Mapped[List["Achievement"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Achievement.display_order",
    )
    professional_developments: Mapped[List["ProfessionalDevelopment"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="ProfessionalDevelopment.display_order",
    )
    job_descriptions: Mapped[List["JobDescription"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    resumes: Mapped[List["Resume"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    file_assets: Mapped[List["FileAsset"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class Education(Base, TimestampMixin):
    """Academic degree or educational milestone."""

    __tablename__ = "educations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    score: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    scale: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="verified_both", nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="educations")


class Experience(Base, TimestampMixin):
    """Work experience, internship, or leadership role."""

    __tablename__ = "experiences"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metrics: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bullets: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="verified_both", nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="experiences")


class Skill(Base, TimestampMixin):
    """Categorized technical competency or skill tag."""

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="skills")


class Project(Base, TimestampMixin):
    """Verified project with links, metrics, and bullet points."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notice: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_fixed_project: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fixed_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    categories: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    skills: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    links: Mapped[List[Dict[str, str]]] = mapped_column(JSONVariant, default=list, nullable=False)
    bullets: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    metrics: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    evidence_source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="verified", nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="projects")


class Certification(Base, TimestampMixin):
    """Professional certificate or credential."""

    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="certifications")


class Achievement(Base, TimestampMixin):
    """Notable award, honor, or competition achievement."""

    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bullets: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="verified_both", nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="achievements")


class ProfessionalDevelopment(Base, TimestampMixin):
    """Workshops, specialized courses, or continuous training."""

    __tablename__ = "professional_developments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bullets: Mapped[List[str]] = mapped_column(JSONVariant, default=list, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    conflict_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="professional_developments")
