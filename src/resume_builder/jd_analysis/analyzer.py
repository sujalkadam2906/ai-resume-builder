"""Job Description analysis pipeline."""

import re
from typing import Dict, List, Optional, Set
from ..profile.models import MasterProfile, ProjectItem
from .keywords import (
    KNOWN_DATABASES,
    KNOWN_FRAMEWORKS,
    KNOWN_LANGUAGES,
    KNOWN_TOOLS,
    canonicalize_skill,
    extract_keywords_from_text,
)
from .models import JobDescription, RequirementMatrix
from .requirement_matrix import build_requirement_matrix


class JDAnalyzer:
    """Parses and analyzes job descriptions deterministically with optional AI enhancement."""

    def __init__(self, profile: MasterProfile, projects: List[ProjectItem]):
        self.profile = profile
        self.projects = projects

    def extract_metadata(self, text: str, user_company: Optional[str] = None, user_role: Optional[str] = None) -> Dict[str, str]:
        """Extract or fallback company name and job role from text."""
        company = user_company or "Target Company"
        role = user_role or "Software Engineer"

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Try to infer company name if not supplied
        if not user_company:
            for line in lines[:8]:
                m = re.search(r"(?:company|organization|client|at)\s*[:\-]?\s*([A-Za-z0-9\s&]+)", line, re.IGNORECASE)
                if m:
                    cand = m.group(1).strip()
                    if 2 < len(cand) < 40 and not any(k in cand.lower() for k in ["description", "overview", "looking", "job"]):
                        company = cand
                        break

        # Try to infer role if not supplied
        if not user_role:
            for line in lines[:8]:
                m = re.search(r"(?:job title|role|position|opening)\s*[:\-]?\s*([A-Za-z0-9\s/]+)", line, re.IGNORECASE)
                if m:
                    cand = m.group(1).strip()
                    if 3 < len(cand) < 50:
                        role = cand
                        break
                elif any(title in line.lower() for title in ["software engineer", "developer", "backend", "frontend", "full stack", "data engineer", "swe"]):
                    role = line.strip(" :-#*")
                    break

        return {"company": company, "role": role}

    def analyze(
        self,
        raw_text: str,
        user_company: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> JobDescription:
        """Analyze job description and build structured JobDescription model."""
        meta = self.extract_metadata(raw_text, user_company, user_role)
        all_keywords = extract_keywords_from_text(raw_text)

        # Also extract bullet items under Required / Requirements
        explicit_requirements = []
        in_required_section = False
        for line in raw_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            if re.search(r"^(?:required|requirements|must have|qualifications)\s*:", line_str, re.IGNORECASE):
                in_required_section = True
                continue
            if re.search(r"^(?:preferred|nice to have|plus|bonus|responsibilities)\s*:", line_str, re.IGNORECASE):
                in_required_section = False
                continue
            if in_required_section and line_str.startswith(("-", "*", "•")):
                item_text = line_str.lstrip("-*• ").strip()
                if item_text and len(item_text) < 60:
                    explicit_requirements.append(item_text)

        languages = [s for s in all_keywords if s in KNOWN_LANGUAGES]
        frameworks = [s for s in all_keywords if s in KNOWN_FRAMEWORKS]
        databases = [s for s in all_keywords if s in KNOWN_DATABASES]
        tools = [s for s in all_keywords if s in KNOWN_TOOLS]

        # Extract lines that look like responsibilities
        responsibilities = []
        for line in raw_text.split("\n"):
            line_str = line.strip(" •-*#")
            if len(line_str) > 20 and any(
                line_str.lower().startswith(v)
                for v in [
                    "build", "develop", "design", "maintain", "collaborate",
                    "implement", "create", "write", "participate", "work with",
                    "responsible for", "support"
                ]
            ):
                responsibilities.append(line_str)

        if not responsibilities:
            responsibilities = [
                "Develop high-quality, maintainable, and testable code",
                "Design and implement REST APIs and persistence layers",
                "Collaborate with cross-functional teams to deliver software features",
            ]

        # Merge extracted keywords and explicit requirements
        combined_reqs = list(all_keywords)
        for er in explicit_requirements:
            canonical_er = canonicalize_skill(er)
            if canonical_er not in combined_reqs:
                combined_reqs.append(canonical_er)

        required_skills = combined_reqs
        preferred_skills = []

        preferred_match = re.search(r"(?:preferred|nice to have|plus|bonus|optional)[\s\w]*:?(.*)", raw_text, re.IGNORECASE | re.DOTALL)
        if preferred_match:
            pref_text = preferred_match.group(1)[:500]
            pref_keywords = extract_keywords_from_text(pref_text)
            for pk in pref_keywords:
                if pk in required_skills:
                    required_skills.remove(pk)
                preferred_skills.append(pk)

        return JobDescription(
            raw_text=raw_text,
            company_name=meta["company"],
            job_title=meta["role"],
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            programming_languages=languages,
            frameworks_and_libraries=frameworks,
            databases=databases,
            tools=tools,
            responsibilities=responsibilities[:6],
            domain_keywords=list(all_keywords),
        )

    def evaluate_match(self, jd: JobDescription) -> RequirementMatrix:
        """Build the full requirement matrix comparing candidate to JD."""
        return build_requirement_matrix(
            profile=self.profile,
            projects=self.projects,
            required_skills=jd.required_skills,
            preferred_skills=jd.preferred_skills,
            responsibilities=jd.responsibilities,
        )
