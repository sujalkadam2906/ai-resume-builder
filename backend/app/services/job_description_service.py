"""Job Description lifecycle, persistence, and AI/deterministic analysis service."""

import math
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models.candidate import CandidateProfile
from backend.app.models.resume import JobDescription as DBJobDescription
from backend.app.schemas.resume import (
    JobDescriptionAnalysisResponse,
    JobDescriptionCreate,
    JobDescriptionUpdate,
)
from backend.app.services.profile_converter import db_candidate_to_engine_profile
from backend.app.services.profile_service import ProfileService
from src.resume_builder.jd_analysis.analyzer import JDAnalyzer
from src.resume_builder.jd_analysis.models import JobDescription as EngineJD


class JobDescriptionService:
    """Service handling job description CRUD and structured requirement extraction."""

    @staticmethod
    def create_job_description(
        session: Session,
        data: JobDescriptionCreate,
        user_id: Optional[uuid.UUID] = None,
    ) -> DBJobDescription:
        """Create and persist a new target job description scoped to user_id."""
        resolved_profile_id = None
        if data.profile_id:
            profile = ProfileService.get_profile_by_id_or_slug(session, data.profile_id, user_id=user_id)
            if not profile:
                raise ValueError(f"Candidate profile '{data.profile_id}' not found.")
            resolved_profile_id = profile.id

        jd_id = uuid.uuid4()
        req_matrix: Dict[str, Any] = {}
        if data.source_url:
            req_matrix["source_url"] = data.source_url

        jd = DBJobDescription(
            id=jd_id,
            user_id=user_id,
            profile_id=resolved_profile_id,
            job_title=data.job_title,
            company_name=data.company_name,
            raw_text=data.raw_text,
            extracted_skills=[],
            requirement_matrix=req_matrix,
            match_percentage=None,
        )
        session.add(jd)
        session.commit()
        session.refresh(jd)
        return jd

    @staticmethod
    def get_job_description(
        session: Session,
        jd_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[DBJobDescription]:
        """Fetch job description by UUID and optional user ownership."""
        stmt = select(DBJobDescription).filter_by(id=jd_id)
        if user_id is not None:
            from backend.app.config import settings
            dev_user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "dev-local-user")
            if not settings.is_production and user_id == dev_user_uuid:
                stmt = stmt.filter((DBJobDescription.user_id == user_id) | (DBJobDescription.user_id.is_(None)))
            else:
                stmt = stmt.filter(DBJobDescription.user_id == user_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_job_descriptions(
        session: Session,
        profile_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[DBJobDescription], int]:
        """List job descriptions scoped to user_id with optional profile filter and pagination."""
        stmt = select(DBJobDescription).order_by(desc(DBJobDescription.created_at))

        if user_id is not None:
            from backend.app.config import settings
            dev_user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "dev-local-user")
            if not settings.is_production and user_id == dev_user_uuid:
                stmt = stmt.filter((DBJobDescription.user_id == user_id) | (DBJobDescription.user_id.is_(None)))
            else:
                stmt = stmt.filter(DBJobDescription.user_id == user_id)

        if profile_id:
            profile = ProfileService.get_profile_by_id_or_slug(session, profile_id, user_id=user_id)
            if profile:
                stmt = stmt.filter(DBJobDescription.profile_id == profile.id)
            else:
                return [], 0

        all_items = session.execute(stmt).scalars().all()
        total_count = len(all_items)
        paginated = all_items[(page - 1) * size : page * size]
        return paginated, total_count

    @staticmethod
    def update_job_description(
        session: Session,
        jd: DBJobDescription,
        data: JobDescriptionUpdate,
    ) -> DBJobDescription:
        """Partially update an existing job description."""
        update_data = data.model_dump(exclude_unset=True)
        if "source_url" in update_data:
            url = update_data.pop("source_url")
            matrix = dict(jd.requirement_matrix or {})
            if url:
                matrix["source_url"] = url
            else:
                matrix.pop("source_url", None)
            jd.requirement_matrix = matrix

        for key, value in update_data.items():
            if hasattr(jd, key):
                setattr(jd, key, value)

        session.commit()
        session.refresh(jd)
        return jd

    @staticmethod
    def delete_job_description(session: Session, jd: DBJobDescription) -> bool:
        """Delete a job description and cascade to child records."""
        session.delete(jd)
        session.commit()
        return True

    @staticmethod
    def analyze_job_description(
        session: Session,
        jd: DBJobDescription,
        candidate_profile: Optional[CandidateProfile] = None,
    ) -> JobDescriptionAnalysisResponse:
        """Analyze job description extracting skills, responsibilities, and technical stack.
        
        Persists extracted_skills, requirement_matrix, and match_percentage.
        Never silently assumes uncertain AI extraction is verified fact.
        """
        # 1. Resolve candidate profile for matching context
        target_profile = candidate_profile
        if not target_profile and jd.profile_id:
            target_profile = session.execute(
                select(CandidateProfile).filter_by(id=jd.profile_id)
            ).scalar_one_or_none()

        master_profile = None
        projects = []
        if target_profile:
            master_profile, projects, _ = db_candidate_to_engine_profile(target_profile)

        # 2. Run deterministic JD Analyzer
        analyzer = JDAnalyzer(profile=master_profile, projects=projects)
        engine_jd = analyzer.analyze(
            raw_text=jd.raw_text,
            user_company=jd.company_name,
            user_role=jd.job_title,
        )

        # 3. Infer company and role if missing
        if not jd.company_name and engine_jd.company_name:
            jd.company_name = engine_jd.company_name
        if not jd.job_title and engine_jd.job_title:
            jd.job_title = engine_jd.job_title

        # 4. Extract tech stack categories
        tech_stack = {
            "languages": engine_jd.programming_languages,
            "frameworks_and_libraries": engine_jd.frameworks_and_libraries,
            "databases": engine_jd.databases,
            "tools": engine_jd.tools,
        }

        # 5. Evaluate match if candidate profile is linked
        match_percentage = None
        matched_skills_list = []
        missing_skills_list = []
        if master_profile:
            req_matrix = analyzer.evaluate_match(engine_jd)
            total_req = len(engine_jd.required_skills)
            unsupported = len(req_matrix.get_unsupported_skills())
            matched_count = max(0, total_req - unsupported)
            match_percentage = round((matched_count / total_req * 100.0), 1) if total_req > 0 else 100.0

            all_cand_skills = set(s.lower() for s in master_profile.technical_skills.get_all_skills_flat())
            for sk in engine_jd.required_skills:
                if sk.lower() in all_cand_skills:
                    matched_skills_list.append(sk)
                else:
                    missing_skills_list.append(sk)

        # 6. Build stored requirement_matrix
        existing_matrix = dict(jd.requirement_matrix or {})
        existing_matrix.update({
            "required_skills": engine_jd.required_skills,
            "preferred_skills": engine_jd.preferred_skills,
            "technical_stack": tech_stack,
            "responsibilities": engine_jd.responsibilities,
            "important_keywords": engine_jd.domain_keywords,
            "matched_skills": matched_skills_list,
            "missing_skills": missing_skills_list,
            "is_ai_extracted": False,
        })

        jd.extracted_skills = list(dict.fromkeys(engine_jd.required_skills + engine_jd.preferred_skills))
        jd.requirement_matrix = existing_matrix
        jd.match_percentage = match_percentage

        session.commit()
        session.refresh(jd)

        return JobDescriptionAnalysisResponse(
            id=jd.id,
            job_title=jd.job_title,
            company_name=jd.company_name,
            required_skills=engine_jd.required_skills,
            preferred_skills=engine_jd.preferred_skills,
            technical_stack=tech_stack,
            responsibilities=engine_jd.responsibilities,
            important_keywords=engine_jd.domain_keywords,
            match_percentage=match_percentage,
            is_ai_extracted=False,
            confidence_note="Analysis extracted deterministically from job description text. Verify before treating as definitive fact.",
        )

    @staticmethod
    def get_analysis(jd: DBJobDescription) -> JobDescriptionAnalysisResponse:
        """Retrieve previously saved analysis results."""
        matrix = jd.requirement_matrix or {}
        return JobDescriptionAnalysisResponse(
            id=jd.id,
            job_title=jd.job_title,
            company_name=jd.company_name,
            required_skills=matrix.get("required_skills", []),
            preferred_skills=matrix.get("preferred_skills", []),
            technical_stack=matrix.get("technical_stack", {}),
            responsibilities=matrix.get("responsibilities", []),
            experience_requirements=matrix.get("experience_requirements"),
            education_requirements=matrix.get("education_requirements"),
            domain=matrix.get("domain"),
            important_keywords=matrix.get("important_keywords", jd.extracted_skills or []),
            match_percentage=jd.match_percentage,
            is_ai_extracted=matrix.get("is_ai_extracted", False),
            confidence_note="Stored requirement analysis for human review. Verify before using as confirmed requirements.",
        )
