"""Candidate-to-Job matching and intelligent project recommendation service."""

from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from backend.app.models.candidate import CandidateProfile
from backend.app.models.resume import JobDescription as DBJobDescription
from backend.app.schemas.resume import (
    CandidateMatchResponse,
    ProjectMatchScore,
)
from backend.app.services.profile_converter import db_candidate_to_engine_profile
from src.resume_builder.jd_analysis.analyzer import JDAnalyzer
from src.resume_builder.jd_analysis.models import JobDescription as EngineJD
from src.resume_builder.project_selection.scorer import compute_project_score
from src.resume_builder.project_selection.selector import select_projects_for_jd


class CandidateMatchingService:
    """Matches candidate profile against job description and generates explainable project recommendations."""

    @staticmethod
    def match_candidate_to_jd(
        session: Session,
        candidate: CandidateProfile,
        jd: DBJobDescription,
        target_count: int = 4,
    ) -> CandidateMatchResponse:
        """Run candidate-job matching and explainable project recommendation."""
        # 1. Convert DB candidate to engine models
        master_profile, all_projects, profile_config = db_candidate_to_engine_profile(candidate)

        # 2. Build Engine JobDescription
        analyzer = JDAnalyzer(profile=master_profile, projects=all_projects)
        engine_jd = analyzer.analyze(
            raw_text=jd.raw_text,
            user_company=jd.company_name,
            user_role=jd.job_title,
        )

        # 3. Evaluate requirement matrix and skill match
        req_matrix = analyzer.evaluate_match(engine_jd)
        unsupported = req_matrix.get_unsupported_skills()

        all_cand_skills = set(s.lower() for s in master_profile.technical_skills.get_all_skills_flat())
        matched_skills = []
        missing_skills = []
        for sk in engine_jd.required_skills:
            if sk.lower() in all_cand_skills:
                matched_skills.append(sk)
            else:
                missing_skills.append(sk)

        total_req = len(engine_jd.required_skills)
        matched_count = len(matched_skills)
        overall_match_pct = round((matched_count / total_req * 100.0), 1) if total_req > 0 else 100.0

        # Update JD match percentage in DB
        jd.match_percentage = overall_match_pct
        session.commit()

        # 4. Project Selection adhering to 45/25/20/10 weights and fixed project rules
        selection_config = profile_config.project_selection
        selection_config.target_count = target_count

        selected_projects, scored_all, warning = select_projects_for_jd(
            all_projects=all_projects,
            jd=engine_jd,
            target_count=target_count,
            weights=selection_config.weights,
            selection_config=selection_config,
        )

        # 5. Format explainable recommendations
        recommended: List[ProjectMatchScore] = []
        fixed_pos = (
            selection_config.fixed_project.position
            if selection_config.has_fixed_project and selection_config.fixed_project
            else None
        )

        for rank_idx, proj in enumerate(selected_projects, 1):
            # Compute granular component breakdown
            weights = selection_config.weights
            total_score = compute_project_score(proj, engine_jd, weights)

            # Check if this slot is the pinned fixed project
            is_pinned = False
            if selection_config.has_fixed_project and rank_idx == fixed_pos:
                is_pinned = True
                explanation = (
                    f"Pinned Safeguard: {proj.title} is permanently locked at position {rank_idx} "
                    f"per candidate configuration rules."
                )
            else:
                explanation = (
                    f"Selected at position {rank_idx} based on 45% skills coverage, "
                    f"25% responsibilities alignment, 20% tech stack similarity, "
                    f"and 10% domain relevance (Score: {total_score:.1f}/100)."
                )

            # Estimate component contribution
            skills_score = round(total_score * 0.45, 1)
            resp_score = round(total_score * 0.25, 1)
            stack_score = round(total_score * 0.20, 1)
            domain_score = round(total_score * 0.10, 1)

            recommended.append(
                ProjectMatchScore(
                    project_id=proj.id,
                    title=proj.title,
                    subtitle=proj.subtitle,
                    is_fixed=is_pinned,
                    fixed_position=rank_idx if is_pinned else None,
                    overall_score=round(total_score, 1),
                    score_breakdown={
                        "required_skills_weight_45": skills_score,
                        "responsibilities_weight_25": resp_score,
                        "tech_stack_weight_20": stack_score,
                        "domain_relevance_weight_10": domain_score,
                        "required_skills": skills_score,
                        "responsibilities": resp_score,
                        "tech_stack": stack_score,
                        "domain": domain_score,
                    },
                    ranking_explanation=explanation,
                )
            )

        return CandidateMatchResponse(
            candidate_id=candidate.id,
            candidate_slug=candidate.slug,
            job_description_id=jd.id,
            overall_match_percentage=overall_match_pct,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            unsupported_skills=unsupported,
            recommended_projects=recommended,
            project_selection_warnings=warning,
        )
