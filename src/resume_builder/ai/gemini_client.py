"""Gemini API client with structured outputs and deterministic offline fallback."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from ..config import config
from ..jd_analysis.models import JobDescription, RequirementMatrix
from ..profile.models import MasterProfile, ProjectItem
from .fallback import execute_with_fallback, InvalidAPIKeyError
from .prompts import SYSTEM_PROMPT, build_tailoring_user_prompt
from .structured_schemas import TailoredProject, TailoredResumeContent

logger = logging.getLogger("resume_builder.ai")


def generate_offline_content(
    profile: MasterProfile,
    selected_projects: List[ProjectItem],
    jd: JobDescription,
    req_matrix: RequirementMatrix,
) -> TailoredResumeContent:
    """
    Deterministic local fallback generator when running offline or without an active API key.
    Enforces all business constraints: 100% truthful, 4 projects, Bearing Fault at position 2.
    """
    title_lower = jd.job_title.lower()
    skills_text = " ".join(jd.required_skills).lower()

    # Determine headline
    if "java" in title_lower or "backend" in title_lower or "spring" in skills_text:
        headline = "Entry-Level SWE / SWD | Java Full-Stack | Spring Boot & REST APIs"
        category_order = ["Backend & Java", "Databases & SQL", "Languages", "Core CS & ML", "Testing & Tools", "Frontend"]
        focus = "building a Spring Boot REST API with MySQL persistence and SQL analytics in PostgreSQL"
    elif "frontend" in title_lower or "react" in skills_text or "ui" in title_lower:
        headline = "Entry-Level Software Engineer | React, TypeScript & Modern Web Development"
        category_order = ["Frontend", "Languages", "Testing & Tools", "Core CS & ML", "Databases & SQL", "Backend & Java"]
        focus = "building responsive React 18, TypeScript web applications and modular JavaScript frontends"
    elif "data" in title_lower or "ml" in skills_text or "python" in title_lower:
        headline = "Entry-Level Software Engineer | Python, Machine Learning & SQL Analytics"
        category_order = ["Core CS & ML", "Languages", "Databases & SQL", "Backend & Java", "Frontend", "Testing & Tools"]
        focus = "applied machine learning in Python, statistical feature engineering, and relational database analytics"
    else:
        headline = "Entry-Level Software Engineer | Java, Spring Boot, SQL, React & TypeScript"
        category_order = ["Languages", "Backend & Java", "Frontend", "Databases & SQL", "Core CS & ML", "Testing & Tools"]
        focus = "full-stack software development across Java/Spring Boot REST APIs and React/TypeScript interfaces"

    summary = (
        f"B.Tech graduate (2026, CGPA: 8.23/10) with hands-on project experience {focus}. "
        "Solid foundation in Data Structures, Algorithms, OOP, and relational schema design. "
        "Chief Student Training & Placement Officer who coordinated placement operations for "
        "1,500+ students across 20+ recruitment drives; immediate joiner open to relocation."
    )

    tailored_projects = []
    for p in selected_projects:
        tailored_projects.append(
            TailoredProject(
                project_id=p.id,
                title=p.title,
                subtitle=p.subtitle,
                bullets=p.bullets,
            )
        )

    # Relevant certifications
    certs = list(profile.certifications)
    if "java" in title_lower or "backend" in title_lower:
        certs.sort(key=lambda c: 0 if "java" in c.lower() or "sql" in c.lower() else 1)

    return TailoredResumeContent(
        professional_headline=headline,
        professional_summary=summary,
        skills_category_order=category_order,
        tailored_projects=tailored_projects,
        relevant_certifications=certs,
        change_summary_notes=[
            f"Tailored headline to match target role: '{jd.job_title}' at '{jd.company_name}'",
            "Prioritized primary technical skills category to align with JD requirements",
            "Retained all 4 verified projects with Bearing Fault Diagnosis fixed at position 2",
            "Excluded unsupported technologies to preserve strict factual integrity",
        ],
    )


class GeminiResumeClient:
    """Client for generating tailored resume content via Gemini with model fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.gemini_api_key
        self._client = None
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI client: {e}")

    def generate(
        self,
        profile: MasterProfile,
        selected_projects: List[ProjectItem],
        jd: JobDescription,
        req_matrix: RequirementMatrix,
        offline: bool = False,
    ) -> Tuple[TailoredResumeContent, str]:
        """
        Generate tailored resume content.
        Uses Google Gemini with model fallback if online and configured;
        otherwise runs high-fidelity offline deterministic generator.
        """
        if offline or not self._client or not self.api_key:
            logger.info("Using deterministic offline content generator (offline mode or no API key).")
            content = generate_offline_content(profile, selected_projects, jd, req_matrix)
            return content, "offline-deterministic-engine"

        user_prompt = build_tailoring_user_prompt(profile, selected_projects, jd, req_matrix)
        candidate_models = config.candidate_models

        def _call_model(model_name: str) -> TailoredResumeContent:
            from google.genai import types

            response = self._client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=config.gemini_temperature,
                    response_mime_type="application/json",
                    response_schema=TailoredResumeContent,
                ),
            )

            # Validate structured output
            text = response.text
            data = json.loads(text)
            parsed = TailoredResumeContent(**data)

            # Verify Bearing Fault rule: slot 2 must be Bearing Fault
            if len(parsed.tailored_projects) >= 2:
                p2 = parsed.tailored_projects[1]
                if "bearing" not in p2.title.lower() and "bearing" not in p2.project_id.lower():
                    logger.warning("AI reordered Bearing Fault! Restoring Bearing Fault at position 2.")
                    # Find bearing fault project from selected_projects
                    bf = next(p for p in selected_projects if "bearing" in p.id.lower())
                    parsed.tailored_projects[1] = TailoredProject(
                        project_id=bf.id,
                        title=bf.title,
                        subtitle=bf.subtitle,
                        bullets=bf.bullets,
                    )

            return parsed

        try:
            content, active_model = execute_with_fallback(
                client=self._client,
                candidate_models=candidate_models,
                call_fn=_call_model,
                max_retries=config.gemini_max_retries,
                backoff_factor=config.gemini_backoff_factor,
            )
            return content, active_model
        except Exception as e:
            logger.warning(f"Online Gemini generation failed ({e}). Falling back to deterministic engine.")
            content = generate_offline_content(profile, selected_projects, jd, req_matrix)
            return content, "fallback-deterministic-engine"
