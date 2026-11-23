"""Multi-profile and project database manager with safe backup operations and strict isolation."""

from datetime import datetime
import json
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Optional
import yaml

from ..config import (
    BACKUPS_DIR,
    DEFAULT_PROFILE_ID,
    MASTER_PROFILE_FILE,
    PROFILES_DIR,
    PROJECTS_FILE,
    get_profile_dir,
)
from ..extraction import extract_resume, find_resume_files, validate_discovered_files
from ..utils import atomic_write_json, create_backup
from .migration import migrate_sujal_profile
from .models import MasterProfile, ProfileConfig, ProfileRegistry, ProfileRegistryEntry, ProjectItem
from .reconciler import reconcile_resumes


class ProfileManager:
    """
    Manages reading, writing, backups, listing, and validation of verified candidate data
    with strict multi-profile isolation and directory traversal protection.
    """

    def __init__(
        self,
        profile_id: Optional[str] = None,
        profile_path: Optional[Path] = None,
        projects_path: Optional[Path] = None,
        backups_dir: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ):
        if profile_id:
            self.profile_id = profile_id
            self.profile_dir = get_profile_dir(profile_id)
            # Ensure sujal profile auto-migrates if necessary
            if profile_id == DEFAULT_PROFILE_ID and not (self.profile_dir / "master_profile.json").exists():
                migrate_sujal_profile(DEFAULT_PROFILE_ID)

            self.profile_path = profile_path or (self.profile_dir / "master_profile.json")
            self.projects_path = projects_path or (self.profile_dir / "projects.json")
            self.config_path = config_path or (self.profile_dir / "profile_config.yaml")
            self.backups_dir = backups_dir or (self.profile_dir / "backups")
        elif profile_path or projects_path:
            # Legacy direct path mode for backwards compatibility
            self.profile_id = DEFAULT_PROFILE_ID
            self.profile_path = profile_path or MASTER_PROFILE_FILE
            self.projects_path = projects_path or PROJECTS_FILE
            self.profile_dir = self.profile_path.parent
            self.config_path = config_path or (self.profile_dir / "profile_config.yaml")
            self.backups_dir = backups_dir or BACKUPS_DIR
        else:
            # Default to default profile ("sujal")
            self.profile_id = DEFAULT_PROFILE_ID
            self.profile_dir = get_profile_dir(self.profile_id)
            if not (self.profile_dir / "master_profile.json").exists():
                migrate_sujal_profile(DEFAULT_PROFILE_ID)
            self.profile_path = self.profile_dir / "master_profile.json"
            self.projects_path = self.profile_dir / "projects.json"
            self.config_path = self.profile_dir / "profile_config.yaml"
            self.backups_dir = self.profile_dir / "backups"

        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def load_profile(self) -> MasterProfile:
        """Load the master candidate profile from disk."""
        if not self.profile_path.exists():
            # If default profile, check legacy path as fallback
            if self.profile_id == DEFAULT_PROFILE_ID and MASTER_PROFILE_FILE.exists():
                migrate_sujal_profile(DEFAULT_PROFILE_ID)
            else:
                raise FileNotFoundError(
                    f"Master profile not found at {self.profile_path}. "
                    f"Profile '{self.profile_id}' may not have been initialized."
                )
        with open(self.profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return MasterProfile(**data)

    def load_projects(self) -> List[ProjectItem]:
        """Load all verified projects from the projects database."""
        if not self.projects_path.exists():
            if self.profile_id == DEFAULT_PROFILE_ID and PROJECTS_FILE.exists():
                migrate_sujal_profile(DEFAULT_PROFILE_ID)
            else:
                raise FileNotFoundError(
                    f"Projects database not found at {self.projects_path}. "
                    f"Profile '{self.profile_id}' may not have been initialized."
                )
        with open(self.projects_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [ProjectItem(**item) for item in data]

    def load_profile_config(self) -> ProfileConfig:
        """Load profile configuration YAML."""
        if not self.config_path.exists():
            # Fallback default configuration
            return ProfileConfig(
                profile_id=self.profile_id,
                display_name=self.profile_id.capitalize(),
            )
        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return ProfileConfig(**raw)

    def save_profile(self, profile: MasterProfile) -> None:
        """Save master profile with an automated backup."""
        if self.profile_path.exists():
            create_backup(self.profile_path, self.backups_dir)
        atomic_write_json(self.profile_path, profile.model_dump(mode="json"))

    def save_projects(self, projects: List[ProjectItem]) -> None:
        """Save projects database with an automated backup."""
        if self.projects_path.exists():
            create_backup(self.projects_path, self.backups_dir)
        atomic_write_json(
            self.projects_path, [p.model_dump(mode="json") for p in projects]
        )

    def save_profile_config(self, cfg: ProfileConfig) -> None:
        """Save profile configuration to YAML."""
        if self.config_path.exists():
            create_backup(self.config_path, self.backups_dir)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg.model_dump(mode="json"), f, sort_keys=False, default_flow_style=False)

    def refresh_from_source(self, search_dir: Path) -> Dict[str, Any]:
        """
        Discovers original resume files, extracts them, reconciles conflicts,
        and saves updated master profile and projects.
        """
        found = find_resume_files(search_dir)
        r1_path, r2_path = validate_discovered_files(found)

        r1_data = extract_resume(r1_path)
        r2_data = extract_resume(r2_path)

        profile, projects, conflicts = reconcile_resumes(r1_data, r2_data)

        self.save_profile(profile)
        self.save_projects(projects)

        return {
            "r1": str(r1_path),
            "r2": str(r2_path),
            "projects_count": len(projects),
            "conflicts": conflicts,
        }

    def list_projects_summary(self) -> List[Dict[str, Any]]:
        """Return a structured summary of all verified projects for this profile."""
        projects = self.load_projects()
        summary = []
        for p in projects:
            summary.append({
                "id": p.id,
                "title": p.title,
                "subtitle": p.subtitle,
                "is_fixed": p.is_fixed_project,
                "fixed_pos": p.fixed_position,
                "categories": p.categories,
                "skills_count": len(p.skills),
                "bullets_count": len(p.bullets),
                "verification_status": p.verification_status,
            })
        return summary

    def validate_profile(self) -> Dict[str, Any]:
        """
        Validates profile completeness, schema compliance, prohibited terms,
        and fixed project integrity.
        """
        errors = []
        warnings = []

        try:
            profile = self.load_profile()
        except Exception as e:
            return {
                "profile_id": self.profile_id,
                "valid": False,
                "errors": [f"Failed to load master profile: {e}"],
                "warnings": [],
                "projects_count": 0,
                "skills_count": 0,
            }

        try:
            projects = self.load_projects()
        except Exception as e:
            return {
                "profile_id": self.profile_id,
                "valid": False,
                "errors": [f"Failed to load projects database: {e}"],
                "warnings": [],
                "projects_count": 0,
                "skills_count": 0,
            }

        cfg = self.load_profile_config()

        # 1. Check Personal Info
        if not profile.personal_info.full_name:
            errors.append("Personal info full_name is missing.")
        if not profile.personal_info.email:
            errors.append("Personal info email is missing.")

        # 2. Check Prohibited Terms
        prohibited = [t.lower() for t in cfg.prohibited_terms]
        if prohibited:
            dumped_profile = json.dumps(profile.model_dump(mode="json")).lower()
            for term in prohibited:
                if term in dumped_profile:
                    errors.append(f"Prohibited term '{term}' detected in master profile.")

        # 3. Check Fixed Project Rule
        if cfg.project_selection.has_fixed_project and cfg.project_selection.fixed_project:
            fx_id = cfg.project_selection.fixed_project.id.lower()
            fx_title = cfg.project_selection.fixed_project.title.lower()
            matching = [p for p in projects if p.id.lower() == fx_id or fx_title in p.title.lower()]
            if not matching:
                errors.append(
                    f"Fixed project rule requires '{cfg.project_selection.fixed_project.id}' "
                    f"but it was not found among {len(projects)} verified projects."
                )

        # 4. Check Projects Count
        if len(projects) < cfg.project_selection.target_count:
            warnings.append(
                f"Verified projects count ({len(projects)}) is less than target ({cfg.project_selection.target_count})."
            )

        # Count skills
        skills_count = sum(len(items) for items in profile.technical_skills.model_dump().values() if isinstance(items, list))

        return {
            "profile_id": self.profile_id,
            "candidate_name": profile.personal_info.full_name,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "projects_count": len(projects),
            "skills_count": skills_count,
            "is_synthetic": cfg.is_synthetic,
        }

    # =========================================================================
    # Multi-Profile Class & Static Management Methods
    # =========================================================================

    @classmethod
    def list_all_profiles(cls) -> List[Dict[str, Any]]:
        """Returns metadata for all registered candidate profiles."""
        registry_file = PROFILES_DIR / "registry.json"
        registered_profiles: Dict[str, Any] = {}

        if registry_file.exists():
            try:
                with open(registry_file, "r", encoding="utf-8") as f:
                    reg_data = json.load(f)
                    registered_profiles = reg_data.get("profiles", {})
            except Exception:
                registered_profiles = {}

        # Also inspect directories under profiles/
        results = []
        if PROFILES_DIR.exists():
            for p_dir in sorted(PROFILES_DIR.iterdir()):
                if p_dir.is_dir() and not p_dir.name.startswith("."):
                    pid = p_dir.name
                    meta = registered_profiles.get(pid, {})
                    prof_file = p_dir / "master_profile.json"
                    has_profile = prof_file.exists()
                    cand_name = meta.get("candidate_display_name", "")
                    if not cand_name and has_profile:
                        try:
                            with open(prof_file, "r", encoding="utf-8") as f:
                                d = json.load(f)
                                cand_name = d.get("personal_info", {}).get("full_name", pid)
                        except Exception:
                            cand_name = pid

                    results.append({
                        "profile_id": pid,
                        "candidate_name": cand_name or pid,
                        "created_at": meta.get("created_at", "N/A"),
                        "source_status": meta.get("source_status", "verified" if has_profile else "uninitialized"),
                        "is_active": meta.get("is_active", True),
                        "has_profile": has_profile,
                        "has_projects": (p_dir / "projects.json").exists(),
                        "has_config": (p_dir / "profile_config.yaml").exists(),
                    })
        return results

    @classmethod
    def get_profile_info(cls, profile_id: str) -> Dict[str, Any]:
        """Returns deep profile information and statistics."""
        mgr = cls(profile_id=profile_id)
        val = mgr.validate_profile()
        cfg = mgr.load_profile_config()
        try:
            prof = mgr.load_profile()
            projects = mgr.load_projects()
            headline = (
                cfg.headline_rule.permanent_headline
                if cfg.headline_rule.mode == "permanent" and cfg.headline_rule.permanent_headline
                else (prof.headlines[0] if prof.headlines else "Dynamic")
            )
            return {
                "profile_id": profile_id,
                "candidate_name": prof.personal_info.full_name,
                "display_name": prof.personal_info.display_name,
                "email": prof.personal_info.email,
                "phone": prof.personal_info.phone,
                "headline_mode": cfg.headline_rule.mode,
                "headline": headline,
                "summary_mode": cfg.summary_rule.mode,
                "fixed_project": (
                    cfg.project_selection.fixed_project.model_dump()
                    if cfg.project_selection.has_fixed_project and cfg.project_selection.fixed_project
                    else None
                ),
                "prohibited_terms": cfg.prohibited_terms,
                "projects_count": len(projects),
                "skills_count": val["skills_count"],
                "valid": val["valid"],
                "errors": val["errors"],
                "warnings": val["warnings"],
                "is_synthetic": cfg.is_synthetic,
            }
        except Exception as e:
            return {
                "profile_id": profile_id,
                "candidate_name": "Unknown",
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "projects_count": 0,
                "skills_count": 0,
            }

    @classmethod
    def create_new_profile(
        cls,
        profile_id: str,
        candidate_name: str,
        source_dir: Optional[Path] = None,
        is_synthetic: bool = False,
    ) -> Dict[str, Any]:
        """Scaffolds a new profile directory and registers it."""
        profile_dir = get_profile_dir(profile_id)
        if profile_dir.exists() and (profile_dir / "master_profile.json").exists():
            raise FileExistsError(f"Profile '{profile_id}' already exists at {profile_dir}!")

        for sub in ["source_resumes", "backups", "audit"]:
            (profile_dir / sub).mkdir(parents=True, exist_ok=True)

        # Copy source resumes if provided
        copied_sources = []
        if source_dir and source_dir.exists():
            for src_file in source_dir.glob("*.pdf"):
                dest = profile_dir / "source_resumes" / src_file.name
                shutil.copy2(src_file, dest)
                copied_sources.append(dest.name)

        # Create basic profile_config.yaml
        cfg = ProfileConfig(
            profile_id=profile_id,
            display_name=candidate_name,
            is_synthetic=is_synthetic,
            headline_rule={"mode": "dynamic", "permanent_headline": None},
            summary_rule={"mode": "dynamic", "permanent_summary": None},
            prohibited_terms=[],
            project_selection={
                "target_count": 4,
                "has_fixed_project": False,
                "fixed_project": None,
            },
        )
        with open(profile_dir / "profile_config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(cfg.model_dump(mode="json"), f, sort_keys=False, default_flow_style=False)

        # Update registry.json
        registry_file = PROFILES_DIR / "registry.json"
        reg_data = {"profiles": {}}
        if registry_file.exists():
            try:
                with open(registry_file, "r", encoding="utf-8") as f:
                    reg_data = json.load(f)
            except Exception:
                reg_data = {"profiles": {}}

        reg_data.setdefault("profiles", {})[profile_id] = {
            "profile_id": profile_id,
            "candidate_display_name": candidate_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source_status": "source_uploaded" if copied_sources else "scaffolded",
            "is_active": True,
            "schema_version": "2.0.0",
        }
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(reg_data, f, indent=2)

        return {
            "profile_id": profile_id,
            "profile_dir": str(profile_dir),
            "candidate_name": candidate_name,
            "copied_sources": copied_sources,
        }
