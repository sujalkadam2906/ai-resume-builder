"""Profile service layer managing database operations for candidates and child resources.

Encapsulates business rules, cross-profile security boundaries, soft-deletion/archival,
transaction integrity, and project safeguards.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

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
from backend.app.schemas.profile import (
    CandidateProfileCreate,
    CandidateProfileUpdate,
    EducationCreate,
    EducationUpdate,
    ExperienceCreate,
    ExperienceUpdate,
    SkillCreate,
    SkillUpdate,
    ProjectCreate,
    ProjectUpdate,
    CertificationCreate,
    CertificationUpdate,
    AchievementCreate,
    AchievementUpdate,
    ProfessionalDevelopmentCreate,
    ProfessionalDevelopmentUpdate,
)


class ProfileService:
    """Production service for Candidate Profile and child resource lifecycle."""

    # --------------------------------------------------------------------------
    # Profile Lookup & Verification
    # --------------------------------------------------------------------------

    @staticmethod
    def get_profile_by_id_or_slug(
        session: Session,
        identifier: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[CandidateProfile]:
        """Resolve a candidate profile by either its UUID or natural slug.
        
        If user_id is provided, enforces that the profile is either owned by that user
        or is a synthetic shared demo template (is_synthetic=True).
        Eagerly loads all child relationships for detailed representation.
        """
        # Try resolving as UUID
        is_uuid = False
        parsed_uuid = None
        try:
            parsed_uuid = uuid.UUID(str(identifier).strip())
            is_uuid = True
        except (ValueError, AttributeError):
            is_uuid = False

        stmt = (
            select(CandidateProfile)
            .options(
                selectinload(CandidateProfile.educations),
                selectinload(CandidateProfile.experiences),
                selectinload(CandidateProfile.skills),
                selectinload(CandidateProfile.projects),
                selectinload(CandidateProfile.certifications),
                selectinload(CandidateProfile.achievements),
                selectinload(CandidateProfile.professional_developments),
            )
        )

        if is_uuid and parsed_uuid:
            stmt = stmt.filter(CandidateProfile.id == parsed_uuid)
        else:
            stmt = stmt.filter(CandidateProfile.slug == str(identifier).strip())

        if user_id is not None:
            from backend.app.config import settings
            dev_user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "dev-local-user")
            if not settings.is_production and user_id == dev_user_uuid:
                stmt = stmt.filter(
                    (CandidateProfile.user_id == user_id)
                    | (CandidateProfile.is_synthetic == True)
                    | (CandidateProfile.user_id.is_(None))
                )
            else:
                stmt = stmt.filter(
                    (CandidateProfile.user_id == user_id) | (CandidateProfile.is_synthetic == True)
                )

        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_profiles(
        session: Session,
        user_id: Optional[uuid.UUID] = None,
        page: int = 1,
        size: int = 20,
        include_archived: bool = False,
    ) -> Tuple[List[CandidateProfile], int]:
        """List candidate profiles with pagination, tenant filtering, and optional archived profile inclusion."""
        stmt = select(CandidateProfile).order_by(CandidateProfile.created_at.desc())

        if user_id is not None:
            from backend.app.config import settings
            dev_user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "dev-local-user")
            if not settings.is_production and user_id == dev_user_uuid:
                stmt = stmt.filter(
                    (CandidateProfile.user_id == user_id)
                    | (CandidateProfile.is_synthetic == True)
                    | (CandidateProfile.user_id.is_(None))
                )
            else:
                stmt = stmt.filter(
                    (CandidateProfile.user_id == user_id) | (CandidateProfile.is_synthetic == True)
                )

        all_profiles = session.execute(stmt).scalars().all()

        # Filter out archived profiles if requested
        filtered = [
            p for p in all_profiles
            if include_archived or not (p.config_rules or {}).get("is_archived", False)
        ]

        total = len(filtered)
        start = (page - 1) * size
        end = start + size
        paginated = filtered[start:end]

        return paginated, total

    # --------------------------------------------------------------------------
    # Profile CRUD & Soft-Archive
    # --------------------------------------------------------------------------

    @staticmethod
    def create_profile(
        session: Session,
        data: CandidateProfileCreate,
        user_id: Optional[uuid.UUID] = None,
    ) -> CandidateProfile:
        """Create a new candidate profile, validating unique slug and adding initial sections."""
        existing = session.execute(
            select(CandidateProfile).filter_by(slug=data.slug)
        ).scalar_one_or_none()

        if existing is not None:
            raise ValueError(f"Candidate profile with slug '{data.slug}' already exists.")

        profile_id = uuid.uuid4()
        config_rules = data.config_rules or {}
        config_rules.setdefault("is_archived", False)

        profile = CandidateProfile(
            id=profile_id,
            user_id=user_id or data.user_id,
            slug=data.slug,
            full_name=data.full_name,
            display_name=data.display_name or data.full_name,
            email=data.email,
            phone=data.phone,
            location=data.location,
            open_to_relocate=data.open_to_relocate,
            immediate_joiner=data.immediate_joiner,
            professional_headline=data.professional_headline,
            professional_summary=data.professional_summary,
            headlines=data.headlines or {},
            summaries=data.summaries or {},
            links=data.links or {},
            config_rules=config_rules,
            is_synthetic=bool(data.is_synthetic),
        )
        session.add(profile)
        session.flush()

        # Add initial child records if provided
        if data.educations:
            for idx, edu in enumerate(data.educations):
                d = edu.model_dump()
                d.setdefault("display_order", idx)
                session.add(Education(**d, profile_id=profile_id))

        if data.experiences:
            for idx, exp in enumerate(data.experiences):
                d = exp.model_dump()
                d.setdefault("display_order", idx)
                session.add(Experience(**d, profile_id=profile_id))

        if data.skills:
            for idx, sk in enumerate(data.skills):
                d = sk.model_dump()
                d.setdefault("display_order", idx)
                session.add(Skill(**d, profile_id=profile_id))

        if data.projects:
            for idx, prj in enumerate(data.projects):
                d = prj.model_dump()
                d.setdefault("display_order", idx)
                session.add(Project(**d, profile_id=profile_id))

        if data.certifications:
            for idx, cert in enumerate(data.certifications):
                d = cert.model_dump()
                d.setdefault("display_order", idx)
                session.add(Certification(**d, profile_id=profile_id))

        if data.achievements:
            for idx, ach in enumerate(data.achievements):
                d = ach.model_dump()
                d.setdefault("display_order", idx)
                session.add(Achievement(**d, profile_id=profile_id))

        if data.professional_developments:
            for idx, pd in enumerate(data.professional_developments):
                d = pd.model_dump()
                d.setdefault("display_order", idx)
                session.add(ProfessionalDevelopment(**d, profile_id=profile_id))

        session.commit()
        return ProfileService.get_profile_by_id_or_slug(session, str(profile_id))

    @staticmethod
    def update_profile(
        session: Session,
        profile: CandidateProfile,
        data: CandidateProfileUpdate,
    ) -> CandidateProfile:
        """Perform partial update (PATCH semantics) preserving metadata and child entities."""
        if profile.is_synthetic or profile.slug == "demo_candidate":
            raise ValueError("Shared demo candidate template is read-only and cannot be modified.")
        update_dict = data.model_dump(exclude_unset=True)

        for key, val in update_dict.items():
            if key == "config_rules" and isinstance(val, dict):
                # Deep merge to preserve research_publications, reconciliation_metadata, etc.
                # Strip archival control keys to prevent tampering via PATCH
                sanitized_val = {k: v for k, v in val.items() if k not in ("is_archived", "archived_at")}
                merged_rules = dict(profile.config_rules or {})
                merged_rules.update(sanitized_val)
                profile.config_rules = merged_rules
            elif hasattr(profile, key):
                setattr(profile, key, val)

        session.commit()
        return ProfileService.get_profile_by_id_or_slug(session, str(profile.id))

    @staticmethod
    def archive_profile(session: Session, profile: CandidateProfile) -> CandidateProfile:
        """Soft-delete / archive candidate profile without deleting data."""
        if profile.is_synthetic or profile.slug == "demo_candidate":
            raise ValueError("Shared demo candidate template cannot be archived or deleted.")
        rules = dict(profile.config_rules or {})
        rules["is_archived"] = True
        rules["archived_at"] = datetime.now(timezone.utc).isoformat()
        profile.config_rules = rules
        session.commit()
        return ProfileService.get_profile_by_id_or_slug(session, str(profile.id))

    @staticmethod
    def restore_profile(session: Session, profile: CandidateProfile) -> CandidateProfile:
        """Restore an archived candidate profile."""
        if profile.is_synthetic or profile.slug == "demo_candidate":
            raise ValueError("Shared demo candidate template cannot be modified.")
        rules = dict(profile.config_rules or {})
        rules["is_archived"] = False
        rules.pop("archived_at", None)
        profile.config_rules = rules
        session.commit()
        return ProfileService.get_profile_by_id_or_slug(session, str(profile.id))

    @staticmethod
    def clone_profile(
        session: Session,
        source_profile_id: str,
        user_id: uuid.UUID,
        new_slug: Optional[str] = None,
        new_name: Optional[str] = None,
    ) -> CandidateProfile:
        """Clone an accessible candidate profile (e.g. demo_candidate) into the user's workspace."""
        source = ProfileService.get_profile_by_id_or_slug(session, source_profile_id, user_id=user_id)
        if not source:
            raise ValueError(f"Source candidate profile '{source_profile_id}' not found.")

        # Determine target slug
        if new_slug:
            target_slug = new_slug.strip().lower()
            existing = session.execute(
                select(CandidateProfile).filter_by(slug=target_slug)
            ).scalar_one_or_none()
            if existing:
                raise ValueError(f"Candidate profile with slug '{target_slug}' already exists.")
        else:
            base_slug = f"{source.slug}_copy"
            target_slug = base_slug
            counter = 1
            while session.execute(select(CandidateProfile).filter_by(slug=target_slug)).scalar_one_or_none() is not None:
                target_slug = f"{base_slug}_{counter}"
                counter += 1

        new_profile_id = uuid.uuid4()
        config_rules = dict(source.config_rules or {})
        config_rules["is_archived"] = False
        config_rules.pop("archived_at", None)

        cloned_profile = CandidateProfile(
            id=new_profile_id,
            user_id=user_id,
            slug=target_slug,
            full_name=new_name or source.full_name,
            display_name=new_name or source.display_name,
            email=source.email,
            phone=source.phone,
            location=source.location,
            open_to_relocate=source.open_to_relocate,
            immediate_joiner=source.immediate_joiner,
            professional_headline=source.professional_headline,
            professional_summary=source.professional_summary,
            headlines=dict(source.headlines or {}),
            summaries=dict(source.summaries or {}),
            links=dict(source.links or {}),
            config_rules=config_rules,
            is_synthetic=False,
        )
        session.add(cloned_profile)
        session.flush()

        # Deep copy child entities
        for edu in (source.educations or []):
            session.add(Education(
                id=uuid.uuid4(),
                profile_id=new_profile_id,
                degree=edu.degree,
                institution=edu.institution,
                duration=edu.duration,
                start_year=edu.start_year,
                end_year=edu.end_year,
                cgpa=edu.cgpa,
                score=edu.score,
                scale=edu.scale,
                source=edu.source,
                display_order=edu.display_order,
            ))

        for exp in (source.experiences or []):
            session.add(Experience(
                id=uuid.uuid4(),
                profile_id=new_profile_id,
                role=exp.role,
                organization=exp.organization,
                duration=exp.duration,
                metrics=exp.metrics,
                description=exp.description,
                bullets=list(exp.bullets or []),
                source=exp.source,
                display_order=exp.display_order,
            ))

        for sk in (source.skills or []):
            session.add(Skill(
                id=uuid.uuid4(),
                profile_id=new_profile_id,
                category=sk.category,
                skill_name=sk.skill_name,
                display_order=sk.display_order,
            ))

        for prj in (source.projects or []):
            session.add(Project(
                id=uuid.uuid4(),
                profile_id=new_profile_id,
                slug=prj.slug,
                title=prj.title,
                subtitle=prj.subtitle,
                notice=prj.notice,
                is_fixed_project=prj.is_fixed_project,
                fixed_position=prj.fixed_position,
                display_order=prj.display_order,
                categories=list(prj.categories or []),
                skills=list(prj.skills or []),
                links=list(prj.links or []) if isinstance(prj.links, list) else prj.links,
                bullets=list(prj.bullets or []),
                metrics=list(prj.metrics or []),
                evidence_source=prj.evidence_source,
                verification_status=prj.verification_status,
            ))

        for cert in (source.certifications or []):
            session.add(Certification(
                id=uuid.uuid4(),
                profile_id=new_profile_id,
                name=cert.name,
                issuer=cert.issuer,
                issue_date=cert.issue_date,
                display_order=cert.display_order,
            ))

        for ach in (source.achievements or []):
            session.add(Achievement(
                id=uuid.uuid4(),
                profile_id=new_profile_id,
                title=ach.title,
                description=ach.description,
                bullets=list(ach.bullets or []),
                source=ach.source,
                display_order=ach.display_order,
            ))

        for pd in (source.professional_developments or []):
            session.add(ProfessionalDevelopment(
                id=uuid.uuid4(),
                profile_id=new_profile_id,
                title=pd.title,
                organization=pd.organization,
                date=pd.date,
                bullets=list(pd.bullets or []),
                source=pd.source,
                conflict_note=pd.conflict_note,
                display_order=pd.display_order,
            ))

        session.commit()
        return ProfileService.get_profile_by_id_or_slug(session, str(new_profile_id), user_id=user_id)

    # --------------------------------------------------------------------------
    # Education Child Operations
    # --------------------------------------------------------------------------

    @staticmethod
    def list_educations(session: Session, profile_id: uuid.UUID) -> List[Education]:
        return session.execute(
            select(Education).filter_by(profile_id=profile_id).order_by(Education.display_order)
        ).scalars().all()

    @staticmethod
    def get_education(session: Session, profile_id: uuid.UUID, edu_id: uuid.UUID) -> Optional[Education]:
        return session.execute(
            select(Education).filter_by(id=edu_id, profile_id=profile_id)
        ).scalar_one_or_none()

    @staticmethod
    def create_education(session: Session, profile_id: uuid.UUID, data: EducationCreate) -> Education:
        edu = Education(**data.model_dump(), profile_id=profile_id)
        session.add(edu)
        session.commit()
        session.refresh(edu)
        return edu

    @staticmethod
    def update_education(
        session: Session,
        profile_id: uuid.UUID,
        edu_id: uuid.UUID,
        data: EducationUpdate,
    ) -> Optional[Education]:
        edu = ProfileService.get_education(session, profile_id, edu_id)
        if not edu:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(edu, k, v)
        session.commit()
        session.refresh(edu)
        return edu

    @staticmethod
    def delete_education(session: Session, profile_id: uuid.UUID, edu_id: uuid.UUID) -> bool:
        edu = ProfileService.get_education(session, profile_id, edu_id)
        if not edu:
            return False
        session.delete(edu)
        session.commit()
        return True

    # --------------------------------------------------------------------------
    # Experience Child Operations
    # --------------------------------------------------------------------------

    @staticmethod
    def list_experiences(session: Session, profile_id: uuid.UUID) -> List[Experience]:
        return session.execute(
            select(Experience).filter_by(profile_id=profile_id).order_by(Experience.display_order)
        ).scalars().all()

    @staticmethod
    def get_experience(session: Session, profile_id: uuid.UUID, exp_id: uuid.UUID) -> Optional[Experience]:
        return session.execute(
            select(Experience).filter_by(id=exp_id, profile_id=profile_id)
        ).scalar_one_or_none()

    @staticmethod
    def create_experience(session: Session, profile_id: uuid.UUID, data: ExperienceCreate) -> Experience:
        exp = Experience(**data.model_dump(), profile_id=profile_id)
        session.add(exp)
        session.commit()
        session.refresh(exp)
        return exp

    @staticmethod
    def update_experience(
        session: Session,
        profile_id: uuid.UUID,
        exp_id: uuid.UUID,
        data: ExperienceUpdate,
    ) -> Optional[Experience]:
        exp = ProfileService.get_experience(session, profile_id, exp_id)
        if not exp:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(exp, k, v)
        session.commit()
        session.refresh(exp)
        return exp

    @staticmethod
    def delete_experience(session: Session, profile_id: uuid.UUID, exp_id: uuid.UUID) -> bool:
        exp = ProfileService.get_experience(session, profile_id, exp_id)
        if not exp:
            return False
        session.delete(exp)
        session.commit()
        return True

    # --------------------------------------------------------------------------
    # Skill Child Operations
    # --------------------------------------------------------------------------

    @staticmethod
    def list_skills(session: Session, profile_id: uuid.UUID) -> List[Skill]:
        return session.execute(
            select(Skill).filter_by(profile_id=profile_id).order_by(Skill.category, Skill.display_order)
        ).scalars().all()

    @staticmethod
    def get_skill(session: Session, profile_id: uuid.UUID, skill_id: uuid.UUID) -> Optional[Skill]:
        return session.execute(
            select(Skill).filter_by(id=skill_id, profile_id=profile_id)
        ).scalar_one_or_none()

    @staticmethod
    def create_skill(session: Session, profile_id: uuid.UUID, data: SkillCreate) -> Skill:
        sk = Skill(**data.model_dump(), profile_id=profile_id)
        session.add(sk)
        session.commit()
        session.refresh(sk)
        return sk

    @staticmethod
    def update_skill(
        session: Session,
        profile_id: uuid.UUID,
        skill_id: uuid.UUID,
        data: SkillUpdate,
    ) -> Optional[Skill]:
        sk = ProfileService.get_skill(session, profile_id, skill_id)
        if not sk:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(sk, k, v)
        session.commit()
        session.refresh(sk)
        return sk

    @staticmethod
    def delete_skill(session: Session, profile_id: uuid.UUID, skill_id: uuid.UUID) -> bool:
        sk = ProfileService.get_skill(session, profile_id, skill_id)
        if not sk:
            return False
        session.delete(sk)
        session.commit()
        return True

    # --------------------------------------------------------------------------
    # Project Child Operations & Bearing Fault Safeguard
    # --------------------------------------------------------------------------

    @staticmethod
    def list_projects(session: Session, profile_id: uuid.UUID) -> List[Project]:
        return session.execute(
            select(Project).filter_by(profile_id=profile_id).order_by(Project.display_order)
        ).scalars().all()

    @staticmethod
    def get_project(session: Session, profile_id: uuid.UUID, project_identifier: str) -> Optional[Project]:
        """Lookup project by UUID or slug, scoped to profile."""
        stmt = select(Project).filter(Project.profile_id == profile_id)
        try:
            p_uuid = uuid.UUID(str(project_identifier).strip())
            stmt = stmt.filter(Project.id == p_uuid)
        except (ValueError, AttributeError):
            stmt = stmt.filter(Project.slug == str(project_identifier).strip())

        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_project(session: Session, profile_id: uuid.UUID, data: ProjectCreate) -> Project:
        # Check slug uniqueness within profile
        existing = session.execute(
            select(Project).filter_by(profile_id=profile_id, slug=data.slug)
        ).scalar_one_or_none()
        if existing:
            raise ValueError(f"Project with slug '{data.slug}' already exists for this profile.")

        # Business safeguard: Check if trying to create an additional fixed project
        if data.is_fixed_project or data.fixed_position is not None:
            fixed_existing = session.execute(
                select(Project).filter_by(profile_id=profile_id, is_fixed_project=True)
            ).scalar_one_or_none()
            if fixed_existing:
                raise ValueError(
                    f"Candidate profile already has a fixed pinned project ({fixed_existing.title}). Multiple fixed projects are not permitted."
                )

        proj_data = data.model_dump()
        # Convert links to list of dicts if needed
        proj = Project(**proj_data, profile_id=profile_id)
        session.add(proj)
        session.commit()
        session.refresh(proj)
        return proj

    @staticmethod
    def update_project(
        session: Session,
        profile_id: uuid.UUID,
        project_identifier: str,
        data: ProjectUpdate,
    ) -> Optional[Project]:
        proj = ProfileService.get_project(session, profile_id, project_identifier)
        if not proj:
            return None

        update_dict = data.model_dump(exclude_unset=True)

        # CRITICAL BUSINESS RULE: Safeguard fixed project positions
        if proj.is_fixed_project:
            if "is_fixed_project" in update_dict and not update_dict["is_fixed_project"]:
                raise ValueError("Cannot unpin fixed project safeguard: this project is permanently pinned.")
            if "fixed_position" in update_dict and update_dict["fixed_position"] != proj.fixed_position:
                raise ValueError(
                    f"Cannot modify fixed project position: {proj.title} is permanently pinned at position {proj.fixed_position}."
                )

        for k, v in update_dict.items():
            setattr(proj, k, v)

        session.commit()
        session.refresh(proj)
        return proj

    @staticmethod
    def delete_project(session: Session, profile_id: uuid.UUID, project_identifier: str) -> bool:
        proj = ProfileService.get_project(session, profile_id, project_identifier)
        if not proj:
            return False

        # CRITICAL BUSINESS RULE: Safeguard fixed projects from deletion
        if proj.is_fixed_project:
            raise ValueError(
                f"Cannot delete pinned project safeguard: {proj.title} is permanent and required by candidate rules."
            )

        session.delete(proj)
        session.commit()
        return True

    # --------------------------------------------------------------------------
    # Certification Child Operations
    # --------------------------------------------------------------------------

    @staticmethod
    def list_certifications(session: Session, profile_id: uuid.UUID) -> List[Certification]:
        return session.execute(
            select(Certification).filter_by(profile_id=profile_id).order_by(Certification.display_order)
        ).scalars().all()

    @staticmethod
    def get_certification(session: Session, profile_id: uuid.UUID, cert_id: uuid.UUID) -> Optional[Certification]:
        return session.execute(
            select(Certification).filter_by(id=cert_id, profile_id=profile_id)
        ).scalar_one_or_none()

    @staticmethod
    def create_certification(session: Session, profile_id: uuid.UUID, data: CertificationCreate) -> Certification:
        cert = Certification(**data.model_dump(), profile_id=profile_id)
        session.add(cert)
        session.commit()
        session.refresh(cert)
        return cert

    @staticmethod
    def update_certification(
        session: Session,
        profile_id: uuid.UUID,
        cert_id: uuid.UUID,
        data: CertificationUpdate,
    ) -> Optional[Certification]:
        cert = ProfileService.get_certification(session, profile_id, cert_id)
        if not cert:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(cert, k, v)
        session.commit()
        session.refresh(cert)
        return cert

    @staticmethod
    def delete_certification(session: Session, profile_id: uuid.UUID, cert_id: uuid.UUID) -> bool:
        cert = ProfileService.get_certification(session, profile_id, cert_id)
        if not cert:
            return False
        session.delete(cert)
        session.commit()
        return True

    # --------------------------------------------------------------------------
    # Achievement Child Operations
    # --------------------------------------------------------------------------

    @staticmethod
    def list_achievements(session: Session, profile_id: uuid.UUID) -> List[Achievement]:
        return session.execute(
            select(Achievement).filter_by(profile_id=profile_id).order_by(Achievement.display_order)
        ).scalars().all()

    @staticmethod
    def get_achievement(session: Session, profile_id: uuid.UUID, ach_id: uuid.UUID) -> Optional[Achievement]:
        return session.execute(
            select(Achievement).filter_by(id=ach_id, profile_id=profile_id)
        ).scalar_one_or_none()

    @staticmethod
    def create_achievement(session: Session, profile_id: uuid.UUID, data: AchievementCreate) -> Achievement:
        ach = Achievement(**data.model_dump(), profile_id=profile_id)
        session.add(ach)
        session.commit()
        session.refresh(ach)
        return ach

    @staticmethod
    def update_achievement(
        session: Session,
        profile_id: uuid.UUID,
        ach_id: uuid.UUID,
        data: AchievementUpdate,
    ) -> Optional[Achievement]:
        ach = ProfileService.get_achievement(session, profile_id, ach_id)
        if not ach:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(ach, k, v)
        session.commit()
        session.refresh(ach)
        return ach

    @staticmethod
    def delete_achievement(session: Session, profile_id: uuid.UUID, ach_id: uuid.UUID) -> bool:
        ach = ProfileService.get_achievement(session, profile_id, ach_id)
        if not ach:
            return False
        session.delete(ach)
        session.commit()
        return True

    # --------------------------------------------------------------------------
    # Professional Development Child Operations
    # --------------------------------------------------------------------------

    @staticmethod
    def list_professional_developments(session: Session, profile_id: uuid.UUID) -> List[ProfessionalDevelopment]:
        return session.execute(
            select(ProfessionalDevelopment).filter_by(profile_id=profile_id).order_by(ProfessionalDevelopment.display_order)
        ).scalars().all()

    @staticmethod
    def get_professional_development(
        session: Session,
        profile_id: uuid.UUID,
        pd_id: uuid.UUID,
    ) -> Optional[ProfessionalDevelopment]:
        return session.execute(
            select(ProfessionalDevelopment).filter_by(id=pd_id, profile_id=profile_id)
        ).scalar_one_or_none()

    @staticmethod
    def create_professional_development(
        session: Session,
        profile_id: uuid.UUID,
        data: ProfessionalDevelopmentCreate,
    ) -> ProfessionalDevelopment:
        pd = ProfessionalDevelopment(**data.model_dump(), profile_id=profile_id)
        session.add(pd)
        session.commit()
        session.refresh(pd)
        return pd

    @staticmethod
    def update_professional_development(
        session: Session,
        profile_id: uuid.UUID,
        pd_id: uuid.UUID,
        data: ProfessionalDevelopmentUpdate,
    ) -> Optional[ProfessionalDevelopment]:
        pd = ProfileService.get_professional_development(session, profile_id, pd_id)
        if not pd:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(pd, k, v)
        session.commit()
        session.refresh(pd)
        return pd

    @staticmethod
    def delete_professional_development(session: Session, profile_id: uuid.UUID, pd_id: uuid.UUID) -> bool:
        pd = ProfileService.get_professional_development(session, profile_id, pd_id)
        if not pd:
            return False
        session.delete(pd)
        session.commit()
        return True
