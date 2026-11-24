"""Resume generation service orchestrating candidate data, JD matching, and AI content creation."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.candidate import CandidateProfile
from backend.app.models.resume import JobDescription as DBJobDescription, Resume as DBResume, ResumeVersion as DBResumeVersion
from backend.app.schemas.resume import ResumeGenerateRequest
from backend.app.services.profile_converter import db_candidate_to_engine_profile
from backend.app.services.profile_service import ProfileService
from src.resume_builder.ai.provider_manager import ProviderManager
from src.resume_builder.content.generator import build_resume_manifest
from src.resume_builder.content.manifest import ResumeContentManifest
from src.resume_builder.jd_analysis.analyzer import JDAnalyzer
from src.resume_builder.project_selection.selector import select_projects_for_jd


class ResumeGenerationService:
    """Orchestrates structured resume generation from PostgreSQL candidate data and JD requirements."""

    @staticmethod
    def generate_draft(
        session: Session,
        request: ResumeGenerateRequest,
    ) -> DBResume:
        """Execute full draft resume generation workflow."""
        # 1. Resolve and validate candidate profile
        candidate = ProfileService.get_profile_by_id_or_slug(session, request.profile_id)
        if not candidate:
            raise ValueError(f"Candidate profile '{request.profile_id}' not found.")
        if (candidate.config_rules or {}).get("is_archived", False):
            raise ValueError(f"Candidate profile '{candidate.slug}' is archived. Restore before generating resumes.")

        # 2. Resolve and validate job description
        jd = session.execute(
            select(DBJobDescription).filter_by(id=request.job_description_id)
        ).scalar_one_or_none()
        if not jd:
            raise ValueError(f"Job Description '{request.job_description_id}' not found.")

        # Guard against cross-profile mismatch if JD is bound to another candidate
        if jd.profile_id and jd.profile_id != candidate.id:
            raise ValueError("Target Job Description belongs to a different candidate profile.")

        # If JD is unattached, associate it with this candidate
        if not jd.profile_id:
            jd.profile_id = candidate.id
            session.flush()

        # 3. Convert DB candidate to resume engine models
        master_profile, all_projects, profile_config = db_candidate_to_engine_profile(candidate)

        # 4. Analyze JD and build requirement matrix
        analyzer = JDAnalyzer(profile=master_profile, projects=all_projects)
        engine_jd = analyzer.analyze(
            raw_text=jd.raw_text,
            user_company=jd.company_name,
            user_role=jd.job_title,
        )
        req_matrix = analyzer.evaluate_match(engine_jd)

        # 5. Project selection (custom override or intelligent ranking)
        target_projects = []
        if request.selected_project_ids:
            # User specified projects explicitly
            id_map = {p.id.lower(): p for p in all_projects}
            for pid in request.selected_project_ids[:4]:
                if pid.lower() in id_map:
                    target_projects.append(id_map[pid.lower()])
            # If Sujal profile, guarantee Bearing Fault is included
            if profile_config.project_selection.has_fixed_project:
                fixed_id = profile_config.project_selection.fixed_project.id
                has_fixed = any(p.id.lower() == fixed_id.lower() for p in target_projects)
                if not has_fixed and fixed_id.lower() in id_map:
                    target_projects = [id_map[fixed_id.lower()]] + target_projects[:3]
        else:
            # Algorithmic ranking with 45/25/20/10 weights & fixed safeguard
            selected, _, _ = select_projects_for_jd(
                all_projects=all_projects,
                jd=engine_jd,
                target_count=4,
                weights=profile_config.project_selection.weights,
                selection_config=profile_config.project_selection,
            )
            target_projects = selected

        # 6. Run AI Content Generator with fallback cascade
        manager = ProviderManager()
        tailored_ai, provider_name, model_used = manager.generate(
            profile=master_profile,
            selected_projects=target_projects,
            jd=engine_jd,
            req_matrix=req_matrix,
            requested_provider=request.provider_override,
            offline=(request.provider_override == "offline"),
        )

        # 7. Assemble validated ResumeContentManifest
        manifest: ResumeContentManifest = build_resume_manifest(
            profile=master_profile,
            selected_projects=target_projects,
            tailored_ai=tailored_ai,
            jd=engine_jd,
            model_used=model_used,
            profile_config=profile_config,
        )

        # Apply optional custom skills selection
        if request.selected_skills:
            manifest.ordered_skills["Custom Selected Skills"] = request.selected_skills

        manifest_dict = manifest.model_dump()

        # 8. Title resolution
        title = request.resume_title
        if not title:
            company_str = engine_jd.company_name or "Target"
            role_str = engine_jd.job_title or "Software Engineer"
            title = f"{candidate.display_name} - {company_str} {role_str} Resume"

        # 9. Persist Resume record
        resume_id = uuid.uuid4()
        resume = DBResume(
            id=resume_id,
            profile_id=candidate.id,
            job_description_id=jd.id,
            resume_title=title,
            status="draft",
            current_version=1,
            editable_manifest=manifest_dict,
        )
        session.add(resume)
        session.flush()

        # 10. Persist initial ResumeVersion
        version = DBResumeVersion(
            id=uuid.uuid4(),
            resume_id=resume.id,
            version_number=1,
            manifest_snapshot=manifest_dict,
            ats_analysis={},
        )
        session.add(version)
        session.commit()
        session.refresh(resume)

        return resume
