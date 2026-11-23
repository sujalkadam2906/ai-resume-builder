"""Project selection package exports."""

from .scorer import compute_project_score
from .selector import select_projects_for_jd

__all__ = ["compute_project_score", "select_projects_for_jd"]
