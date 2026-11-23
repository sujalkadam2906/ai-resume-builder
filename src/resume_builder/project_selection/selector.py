"""Intelligent project selection supporting profile-specific rules and dynamic ranking."""

from typing import Dict, List, Optional, Tuple
from ..config import config
from ..jd_analysis.models import JobDescription
from ..profile.models import ProjectItem, ProjectSelectionConfig
from .scorer import compute_project_score


def select_projects_for_jd(
    all_projects: List[ProjectItem],
    jd: JobDescription,
    target_count: int = 4,
    fixed_project_id: str = "bearing_fault_diagnosis",
    fixed_position: int = 2,
    weights: Optional[Dict[str, float]] = None,
    selection_config: Optional[ProjectSelectionConfig] = None,
) -> Tuple[List[ProjectItem], List[Tuple[ProjectItem, float]], Optional[str]]:
    """
    Selects the best projects for the target JD.
    If selection_config specifies has_fixed_project == False:
      Performs 100% dynamic ranking across all projects.
    If selection_config specifies has_fixed_project == True (or default Sujal rule):
      Strictly enforces the fixed project at fixed_position (e.g. Bearing Fault Detection at #2)
      and dynamically ranks remaining slots.
    """
    if selection_config is not None:
        target_count = selection_config.target_count or target_count
        weights = selection_config.weights or weights or config.project_weights
        has_fixed = selection_config.has_fixed_project
        if has_fixed and selection_config.fixed_project:
            fixed_project_id = selection_config.fixed_project.id
            fixed_position = selection_config.fixed_project.position
    else:
        weights = weights or config.project_weights
        has_fixed = True

    if not all_projects:
        return [], [], "No projects available in database."

    # Pure dynamic selection if no fixed project rule
    if not has_fixed:
        scored: List[Tuple[ProjectItem, float]] = []
        for p in all_projects:
            score = compute_project_score(p, jd, weights)
            scored.append((p, score))
        scored.sort(key=lambda x: x[1], reverse=True)

        selected = [item[0] for item in scored[:target_count]]
        shortage = None
        if len(selected) < target_count:
            shortage = f"Notice: Only {len(selected)} verified projects available. Target was {target_count}."
        return selected, scored, shortage

    # Fixed project selection mode
    fixed_project: Optional[ProjectItem] = None
    candidate_pool: List[ProjectItem] = []

    for p in all_projects:
        # Match case-insensitively or by id
        if p.id.lower() == fixed_project_id.lower() or ("bearing" in fixed_project_id.lower() and "bearing" in p.title.lower()):
            fixed_project = p
        else:
            candidate_pool.append(p)

    if not fixed_project:
        raise ValueError(
            f"Mandatory fixed project '{fixed_project_id}' was not found in verified projects database!"
        )

    # Score candidate pool projects
    scored_candidates: List[Tuple[ProjectItem, float]] = []
    for p in candidate_pool:
        score = compute_project_score(p, jd, weights)
        scored_candidates.append((p, score))

    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    shortage_warning = None
    needed_dynamic = target_count - 1
    if len(scored_candidates) < needed_dynamic:
        shortage_warning = (
            f"Notice: Only {len(scored_candidates)} dynamic verified projects available. "
            f"Target was {needed_dynamic}. Selecting all available without fabricating."
        )

    selected_projects: List[ProjectItem] = []
    if scored_candidates and fixed_position > 1:
        # Fill slots before fixed_position
        for item in scored_candidates[:fixed_position - 1]:
            selected_projects.append(item[0])

    # Insert fixed project
    selected_projects.append(fixed_project)

    # Fill remaining slots after fixed_position
    start_idx = fixed_position - 1
    remaining_needed = target_count - len(selected_projects)
    for item in scored_candidates[start_idx : start_idx + remaining_needed]:
        selected_projects.append(item[0])

    # Final sanity check: ensure no duplicates
    unique_ids = set()
    deduped_selection = []
    for p in selected_projects:
        if p.id not in unique_ids:
            unique_ids.add(p.id)
            deduped_selection.append(p)

    return deduped_selection, scored_candidates, shortage_warning
