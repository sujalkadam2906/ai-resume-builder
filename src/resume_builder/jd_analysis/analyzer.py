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

        # Multi-section parser for Responsibilities, Requirements, and Preferred
        responsibilities = []
        explicit_requirements = []
        explicit_preferred = []

        re_resp_header = re.compile(
            r"^(?:[#*_\s]*)(?:responsibilities|key responsibilities|what you(?:'ll| will) do|what you will be doing|duties|your role|the role|scope of work|what you'll bring|core duties)(?:[#*_\s:]*)$",
            re.IGNORECASE,
        )
        re_req_header = re.compile(
            r"^(?:[#*_\s]*)(?:requirements|qualifications|what we(?:'re| are) looking for|what you(?:'ll| will) need|must[- ]haves?|basic qualifications|minimum qualifications|key qualifications|technical requirements)(?:[#*_\s:]*)$",
            re.IGNORECASE,
        )
        re_pref_header = re.compile(
            r"^(?:[#*_\s]*)(?:preferred qualifications?|nice to have|bonus points|preferred skills?|additional qualifications|bonus)(?:[#*_\s:]*)$",
            re.IGNORECASE,
        )
        re_other_header = re.compile(
            r"^(?:[#*_\s]*)(?:about us|company overview|benefits|what we offer|perks|compensation|about the team|equal opportunity)(?:[#*_\s:]*)$",
            re.IGNORECASE,
        )

        current_section = "unknown"
        for line in raw_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            # Header transitions
            if re_resp_header.match(line_str) or any(
                line_str.lower().startswith(p)
                for p in ["responsibilities:", "what you'll do:", "what you will do:", "key responsibilities:"]
            ):
                current_section = "responsibilities"
                continue
            elif re_req_header.match(line_str) or any(
                line_str.lower().startswith(p)
                for p in ["requirements:", "qualifications:", "must have:", "minimum qualifications:", "what we're looking for:"]
            ):
                current_section = "requirements"
                continue
            elif re_pref_header.match(line_str) or any(
                line_str.lower().startswith(p)
                for p in ["preferred:", "nice to have:", "preferred qualifications:", "bonus:"]
            ):
                current_section = "preferred"
                continue
            elif re_other_header.match(line_str):
                current_section = "other"
                continue

            cleaned_bullet = re.sub(r"^[\s•\-\*\u2022\u25cf\u25cb\d+\.\)]+\s*", "", line_str).strip()

            if current_section == "responsibilities":
                if len(cleaned_bullet) >= 12:
                    responsibilities.append(cleaned_bullet)
            elif current_section == "requirements":
                if len(cleaned_bullet) >= 3:
                    explicit_requirements.append(cleaned_bullet)
            elif current_section == "preferred":
                if len(cleaned_bullet) >= 3:
                    explicit_preferred.append(cleaned_bullet)

        # Fallback for unsectioned JDs: Verb-based detection across the whole text
        if not responsibilities:
            action_verbs = [
                "build", "develop", "design", "maintain", "collaborate", "implement",
                "create", "write", "participate", "work with", "responsible for", "support",
                "lead", "architect", "scale", "optimize", "manage", "ensure", "drive",
                "deliver", "spearhead", "deploy", "automate", "test", "integrate",
                "troubleshoot", "review", "coordinate", "oversee", "evaluate", "own"
            ]
            for line in raw_text.splitlines():
                line_str = re.sub(r"^[\s•\-\*\u2022\u25cf\u25cb\d+\.\)]+\s*", "", line.strip()).strip()
                if len(line_str) > 15:
                    first_words = line_str.lower().split()[:2]
                    first_str = " ".join(first_words)
                    if any(line_str.lower().startswith(v) for v in action_verbs) or "you will" in first_str or "responsible for" in first_str:
                        responsibilities.append(line_str)

        # If still empty, use actual non-empty sentences from the JD instead of static defaults
        if not responsibilities:
            candidate_lines = [
                re.sub(r"^[\s•\-\*\u2022\u25cf\u25cb\d+\.\)]+\s*", "", l.strip()).strip()
                for l in raw_text.splitlines()
                if len(l.strip()) > 20 and not any(k in l.lower() for k in ["company", "job title", "location", "about us", "salary"])
            ]
            if candidate_lines:
                responsibilities = candidate_lines[:5]
            else:
                responsibilities = [
                    "Develop high-quality, maintainable, and testable code",
                    "Design and implement REST APIs and persistence layers",
                    "Collaborate with cross-functional teams to deliver software features",
                ]

        languages = [s for s in all_keywords if s in KNOWN_LANGUAGES]
        frameworks = [s for s in all_keywords if s in KNOWN_FRAMEWORKS]
        databases = [s for s in all_keywords if s in KNOWN_DATABASES]
        tools = [s for s in all_keywords if s in KNOWN_TOOLS]

        # Merge extracted keywords and explicit requirements
        combined_reqs = list(all_keywords)
        for er in explicit_requirements:
            for kw in extract_keywords_from_text(er):
                if kw not in combined_reqs:
                    combined_reqs.append(kw)
            canonical_er = canonicalize_skill(er)
            if canonical_er and canonical_er not in combined_reqs and len(canonical_er) < 35:
                combined_reqs.append(canonical_er)

        required_skills = combined_reqs
        preferred_skills = []

        # Preferred keywords from section or regex
        for ep in explicit_preferred:
            for kw in extract_keywords_from_text(ep):
                if kw not in preferred_skills:
                    preferred_skills.append(kw)

        if not preferred_skills:
            preferred_match = re.search(r"(?:preferred|nice to have|plus|bonus|optional)[\s\w]*:?(.*)", raw_text, re.IGNORECASE | re.DOTALL)
            if preferred_match:
                pref_text = preferred_match.group(1)[:500]
                pref_keywords = extract_keywords_from_text(pref_text)
                for pk in pref_keywords:
                    if pk not in preferred_skills:
                        preferred_skills.append(pk)

        # Separate preferred from required
        for pk in preferred_skills:
            if pk in required_skills:
                required_skills.remove(pk)

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
