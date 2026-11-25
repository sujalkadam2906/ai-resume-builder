"""Resume human review, manual editing, versioning, and approval service."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.candidate import CandidateProfile
from backend.app.models.resume import Resume as DBResume, ResumeVersion as DBResumeVersion
from backend.app.schemas.resume import (
    ResumeApprovalResponse,
    ResumeUpdateRequest,
)
from backend.app.services.profile_service import ProfileService
from src.resume_builder.content.generator import validate_no_prohibited_terms
from src.resume_builder.content.manifest import ResumeContentManifest


class ResumeApprovalService:
    """Manages human-in-the-loop review, edits, version immutability, and approval workflow."""

    @staticmethod
    def get_resume(
        session: Session,
        resume_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[DBResume]:
        """Fetch complete resume record by UUID and optional user ownership."""
        stmt = (
            select(DBResume)
            .options(
                selectinload(DBResume.versions),
                selectinload(DBResume.ats_evaluations),
            )
            .filter_by(id=resume_id)
        )
        if user_id is not None:
            from backend.app.config import settings
            dev_user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "dev-local-user")
            if not settings.is_production and user_id == dev_user_uuid:
                stmt = stmt.filter((DBResume.user_id == user_id) | (DBResume.user_id.is_(None)))
            else:
                stmt = stmt.filter(DBResume.user_id == user_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_resumes(
        session: Session,
        profile_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[DBResume], int]:
        """List resumes with optional tenant/profile/status filtering and pagination."""
        stmt = select(DBResume).order_by(desc(DBResume.created_at))

        if user_id is not None:
            from backend.app.config import settings
            dev_user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "dev-local-user")
            if not settings.is_production and user_id == dev_user_uuid:
                stmt = stmt.filter((DBResume.user_id == user_id) | (DBResume.user_id.is_(None)))
            else:
                stmt = stmt.filter(DBResume.user_id == user_id)

        if profile_id:
            profile = ProfileService.get_profile_by_id_or_slug(session, profile_id, user_id=user_id)
            if profile:
                stmt = stmt.filter(DBResume.profile_id == profile.id)
            else:
                return [], 0

        if status_filter:
            stmt = stmt.filter(DBResume.status == status_filter.lower().strip())

        all_records = session.execute(stmt).scalars().all()
        total = len(all_records)
        start = (page - 1) * size
        paginated = all_records[start : start + size]
        return paginated, total

    @staticmethod
    def update_resume(
        session: Session,
        resume: DBResume,
        data: ResumeUpdateRequest,
    ) -> DBResume:
        """Apply manual edits to resume manifest or title.
        
        If resume is in 'draft' status: updates current manifest directly.
        If resume is in 'approved' status: creates a new draft version (version_number + 1)
        preserving the previously approved version as immutable!
        """
        # 1. Update title if provided
        if data.resume_title:
            resume.resume_title = data.resume_title

        # 2. Update manifest if provided
        if data.editable_manifest:
            # Validate schema integrity
            try:
                manifest_obj = ResumeContentManifest.model_validate(data.editable_manifest)
            except Exception as exc:
                raise ValueError(f"Invalid resume manifest structure: {exc}")

            # Enforce candidate privacy and prohibited terms
            candidate = session.execute(
                select(CandidateProfile).filter_by(id=resume.profile_id)
            ).scalar_one_or_none()
            prohibited = None
            if candidate and candidate.config_rules:
                prohibited = candidate.config_rules.get("prohibited_terms")

            # Check headline and summary for prohibited terms
            validate_no_prohibited_terms(manifest_obj.headline, prohibited, "Headline")
            validate_no_prohibited_terms(manifest_obj.summary, prohibited, "Summary")
            for proj in manifest_obj.projects:
                validate_no_prohibited_terms(proj.title, prohibited, f"Project {proj.title}")
                for b in proj.bullets:
                    validate_no_prohibited_terms(b, prohibited, f"Project {proj.title} bullet")

            new_manifest_dict = manifest_obj.model_dump()

            if resume.status == "approved":
                # Version increment: Preserve previously approved version immutable!
                new_version_num = resume.current_version + 1
                resume.current_version = new_version_num
                resume.status = "draft"
                resume.editable_manifest = new_manifest_dict

                # Create new draft version snapshot
                new_version = DBResumeVersion(
                    id=uuid.uuid4(),
                    resume_id=resume.id,
                    version_number=new_version_num,
                    manifest_snapshot=new_manifest_dict,
                    ats_analysis={},
                )
                session.add(new_version)
            else:
                # Draft in place: update editable manifest and sync current version snapshot
                resume.editable_manifest = new_manifest_dict
                current_ver_obj = session.execute(
                    select(DBResumeVersion).filter_by(
                        resume_id=resume.id,
                        version_number=resume.current_version,
                    )
                ).scalar_one_or_none()
                if current_ver_obj:
                    current_ver_obj.manifest_snapshot = new_manifest_dict

        session.commit()
        session.refresh(resume)
        return resume

    @staticmethod
    def approve_resume(
        session: Session,
        resume: DBResume,
    ) -> ResumeApprovalResponse:
        """Approve resume content, locking current version for export."""
        # 1. Verify manifest validity before approval
        try:
            ResumeContentManifest.model_validate(resume.editable_manifest)
        except Exception as exc:
            raise ValueError(f"Cannot approve invalid resume manifest: {exc}")

        # 2. Transition status to approved
        resume.status = "approved"

        # 3. Ensure current version snapshot matches manifest
        version_obj = session.execute(
            select(DBResumeVersion).filter_by(
                resume_id=resume.id,
                version_number=resume.current_version,
            )
        ).scalar_one_or_none()
        if version_obj:
            version_obj.manifest_snapshot = resume.editable_manifest
        else:
            version_obj = DBResumeVersion(
                id=uuid.uuid4(),
                resume_id=resume.id,
                version_number=resume.current_version,
                manifest_snapshot=resume.editable_manifest,
                ats_analysis={},
            )
            session.add(version_obj)

        session.commit()
        session.refresh(resume)

        return ResumeApprovalResponse(
            id=resume.id,
            status="approved",
            approved_version=resume.current_version,
            message=f"Resume '{resume.resume_title}' (v{resume.current_version}) approved for final export.",
        )

    @staticmethod
    def list_versions(
        session: Session,
        resume_id: uuid.UUID,
    ) -> List[DBResumeVersion]:
        """List all historical version snapshots for a resume."""
        stmt = (
            select(DBResumeVersion)
            .filter_by(resume_id=resume_id)
            .order_by(DBResumeVersion.version_number)
        )
        return session.execute(stmt).scalars().all()

    @staticmethod
    def get_version(
        session: Session,
        resume_id: uuid.UUID,
        version_number: int,
    ) -> Optional[DBResumeVersion]:
        """Retrieve a specific immutable resume version snapshot."""
        stmt = select(DBResumeVersion).filter_by(
            resume_id=resume_id,
            version_number=version_number,
        )
        return session.execute(stmt).scalar_one_or_none()
