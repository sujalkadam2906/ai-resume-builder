"""ATS validation rules and standard definitions."""

from typing import List, Set

STANDARD_HEADINGS: List[str] = [
    "PROFESSIONAL SUMMARY",
    "TECHNICAL SKILLS",
    "PROJECTS",
    "LEADERSHIP",
    "EDUCATION",
    "CERTIFICATIONS",
]

ACTION_VERBS: Set[str] = {
    "built", "developed", "designed", "implemented", "engineered", "created",
    "trained", "tuned", "cleaned", "analyzed", "wrote", "coordinated", "won",
    "authored", "co-authored", "deployed", "integrated", "managed", "optimized",
    "configured", "automated", "tested", "refactored", "spearheaded", "executed",
}

DISCLAIMER: str = (
    "LOCAL ATS READINESS ESTIMATE — NOT AN OFFICIAL VENDOR SCORE.\n"
    "This local diagnostic evaluates structural ATS readability, document extractability,\n"
    "and keyword alignment against the provided Job Description. Actual employer ATS platforms\n"
    "(Workday, Taleo, Greenhouse, Lever, etc.) use proprietary indexing algorithms."
)
