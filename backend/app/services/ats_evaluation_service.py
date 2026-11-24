"""ATS scoring service wrapping deterministic 100-point evaluator with 30/50/20 breakdown."""

from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models.candidate import CandidateProfile
from backend.app.models.resume import ATSEvaluation as DBATSEvaluation, JobDescription as DBJobDescription, Resume as DBResume, ResumeVersion as DBResumeVersion
from backend.app.schemas.resume import ATSEvaluationResponse
from backend.app.services.profile_converter import db_candidate_to_engine_profile
from backend.app.services.resume_export_service import ResumeExportService
from src.resume_builder.ats.scorer import calculate_ats_readiness
from src.resume_builder.jd_analysis.analyzer import JDAnalyzer


class ATSEvaluationService:
    """Evaluates rendered resumes against target JD with format, relevance, and quality scoring."""

    @staticmethod
    def evaluate_resume(
        session: Session,
        resume: DBResume,
    ) -> ATSEvaluationResponse:
        """Run deterministic ATS evaluation on resume and persist breakdown."""
        # 1. Render/resolve PDF for evaluation (allows evaluation on drafts or approved versions)
        pdf_path = ResumeExportService.export_pdf(session, resume, enforce_approved=False)

        # 2. Resolve candidate and profile configuration
        candidate = session.execute(
            select(CandidateProfile).filter_by(id=resume.profile_id)
        ).scalar_one_or_none()
        master_profile, projects, profile_config = (
            db_candidate_to_engine_profile(candidate) if candidate else (None, [], None)
        )

        # 3. Resolve JD and requirement matrix
        jd_record = None
        if resume.job_description_id:
            jd_record = session.execute(
                select(DBJobDescription).filter_by(id=resume.job_description_id)
            ).scalar_one_or_none()

        raw_jd_text = (
            jd_record.raw_text
            if jd_record
            else "Software Engineer position requiring Python, REST APIs, databases, and version control."
        )
        company_str = jd_record.company_name if jd_record else "Target Company"
        role_str = jd_record.job_title if jd_record else "Software Engineer"

        analyzer = JDAnalyzer(profile=master_profile, projects=projects)
        engine_jd = analyzer.analyze(raw_text=raw_jd_text, user_company=company_str, user_role=role_str)
        req_matrix = analyzer.evaluate_match(engine_jd)

        # 4. Run local ATS Readiness Estimator
        report = calculate_ats_readiness(
            pdf_path=pdf_path,
            jd=engine_jd,
            req_matrix=req_matrix,
            profile_config=profile_config,
        )

        # 5. Build and persist ATSEvaluation record
        eval_id = uuid.uuid4()
        evaluation = DBATSEvaluation(
            id=eval_id,
            resume_id=resume.id,
            overall_score=report.overall_score,
            format_score=report.format_score,
            relevance_score=report.relevance_score,
            quality_score=report.quality_score,
            matched_keywords=report.matched_must_have + report.preferred_matched,
            missing_keywords=report.missing_must_have,
            critical_issues=report.critical_issues,
            warnings=report.warnings,
            suggestions=report.suggestions,
        )
        session.add(evaluation)

        # 6. Update current version's ats_score & analysis
        version_obj = session.execute(
            select(DBResumeVersion).filter_by(
                resume_id=resume.id,
                version_number=resume.current_version,
            )
        ).scalar_one_or_none()
        if version_obj:
            version_obj.ats_score = report.overall_score
            version_obj.ats_analysis = report.to_dict()

        session.commit()
        session.refresh(evaluation)

        return ATSEvaluationResponse(
            id=evaluation.id,
            resume_id=resume.id,
            overall_score=evaluation.overall_score,
            format_score=evaluation.format_score,
            relevance_score=evaluation.relevance_score,
            quality_score=evaluation.quality_score,
            score_breakdown={
                "ats_format_compatibility": {"score": evaluation.format_score, "max": 30},
                "jd_relevance": {"score": evaluation.relevance_score, "max": 50},
                "content_quality": {"score": evaluation.quality_score, "max": 20},
            },
            matched_keywords=evaluation.matched_keywords,
            missing_keywords=evaluation.missing_keywords,
            critical_issues=evaluation.critical_issues,
            warnings=evaluation.warnings,
            suggestions=evaluation.suggestions,
            disclaimer=report.disclaimer,
            created_at=evaluation.created_at,
        )

    @staticmethod
    def list_evaluations(
        session: Session,
        resume_id: uuid.UUID,
    ) -> List[DBATSEvaluation]:
        """Fetch historical ATS evaluations for a resume ordered by most recent first."""
        stmt = (
            select(DBATSEvaluation)
            .filter_by(resume_id=resume_id)
            .order_by(desc(DBATSEvaluation.created_at))
        )
        return session.execute(stmt).scalars().all()
