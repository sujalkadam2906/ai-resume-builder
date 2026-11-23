"""Safe, idempotent migration utility for migrating legacy single-profile data to multi-profile architecture."""

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

from ..config import (
    BACKUPS_DIR,
    MASTER_PROFILE_FILE,
    PROJECT_ROOT,
    PROJECTS_FILE,
    PROFILES_DIR,
)


def compute_file_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file for integrity verification."""
    if not filepath.exists():
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def ensure_profile_structure(profile_dir: Path) -> None:
    """Ensures standard subdirectories exist for a profile."""
    for sub in ["source_resumes", "backups", "audit"]:
        (profile_dir / sub).mkdir(parents=True, exist_ok=True)


def migrate_sujal_profile(target_profile_id: str = "sujal") -> Dict[str, Any]:
    """
    Migrates legacy data/master_profile.json and data/projects.json into profiles/sujal/.
    Performs cryptographic hash comparisons and produces a verifiable audit record.
    Idempotent: safe to run multiple times without duplicating or corrupting data.
    """
    profile_dir = PROFILES_DIR / target_profile_id
    ensure_profile_structure(profile_dir)

    target_profile_file = profile_dir / "master_profile.json"
    target_projects_file = profile_dir / "projects.json"
    target_config_file = profile_dir / "profile_config.yaml"
    audit_file = profile_dir / "audit" / "migration_audit.json"

    # 1. Verify and migrate master profile
    orig_profile_hash = compute_file_sha256(MASTER_PROFILE_FILE)
    if MASTER_PROFILE_FILE.exists():
        shutil.copy2(MASTER_PROFILE_FILE, target_profile_file)
        new_profile_hash = compute_file_sha256(target_profile_file)
        if orig_profile_hash != new_profile_hash:
            raise ValueError(
                f"Hash mismatch during master_profile migration! Original: {orig_profile_hash}, Migrated: {new_profile_hash}"
            )

    # 2. Verify and migrate projects database
    orig_projects_hash = compute_file_sha256(PROJECTS_FILE)
    if PROJECTS_FILE.exists():
        shutil.copy2(PROJECTS_FILE, target_projects_file)
        new_projects_hash = compute_file_sha256(target_projects_file)
        if orig_projects_hash != new_projects_hash:
            raise ValueError(
                f"Hash mismatch during projects migration! Original: {orig_projects_hash}, Migrated: {new_projects_hash}"
            )

    # 3. Copy legacy backups if any
    if BACKUPS_DIR.exists():
        for backup_item in BACKUPS_DIR.glob("*.json"):
            dest_backup = profile_dir / "backups" / backup_item.name
            if not dest_backup.exists():
                shutil.copy2(backup_item, dest_backup)

    # 4. Copy source resumes
    current_resumes_dir = PROJECT_ROOT / "Current Resumes"
    if current_resumes_dir.exists():
        for resume_file in current_resumes_dir.glob("*.pdf"):
            dest_resume = profile_dir / "source_resumes" / resume_file.name
            if not dest_resume.exists():
                shutil.copy2(resume_file, dest_resume)

    # 5. Create Sujal's isolated profile_config.yaml
    sujal_config = {
        "profile_id": target_profile_id,
        "display_name": "Sujal Sunil Kadam",
        "is_synthetic": False,
        "headline_rule": {
            "mode": "permanent",
            "permanent_headline": "Entry-Level Software Engineer | Full Stack Developer | ML Research Paper Publisher",
        },
        "summary_rule": {
            "mode": "permanent",
            "permanent_summary": (
                "Developed full-stack projects using Java/Spring Boot and React/TypeScript, "
                "alongside PostgreSQL analytics and Python-based machine learning and Gemini-powered automation. "
                "Coordinated campus placement operations for 1,500+ students across 20+ recruitment drives. "
                "B.Tech graduate (2026, CGPA: 8.23/10); immediate joiner and open to relocation."
            ),
        },
        "prohibited_terms": [
            "mechanical engineering",
            "mechanical engineer",
            "department of mechanical engineering",
        ],
        "project_selection": {
            "target_count": 4,
            "has_fixed_project": True,
            "fixed_project": {
                "id": "bearing_fault_diagnosis",
                "title": "Bearing Fault Diagnosis Using Machine Learning",
                "position": 2,
            },
            "weights": {
                "required_skills_coverage": 0.45,
                "responsibilities_alignment": 0.25,
                "tech_stack_similarity": 0.20,
                "domain_relevance": 0.10,
            },
        },
        "sections_order": [
            "header",
            "summary",
            "technical_skills",
            "projects",
            "professional_development",
            "education",
            "leadership_and_achievements",
            "certifications",
        ],
        "theme": "editorial_teal_copper",
    }

    with open(target_config_file, "w", encoding="utf-8") as f:
        yaml.dump(sujal_config, f, sort_keys=False, default_flow_style=False)

    # 6. Update or create registry.json
    registry_file = PROFILES_DIR / "registry.json"
    registry_data: Dict[str, Any] = {"profiles": {}}
    if registry_file.exists():
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry_data = json.load(f)
        except Exception:
            registry_data = {"profiles": {}}

    if target_profile_id not in registry_data.get("profiles", {}):
        registry_data.setdefault("profiles", {})[target_profile_id] = {
            "profile_id": target_profile_id,
            "candidate_display_name": "Sujal Sunil Kadam",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source_status": "verified_source",
            "is_active": True,
            "schema_version": "2.0.0",
        }
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, indent=2)

    # 7. Write audit record
    audit_record = {
        "migration_timestamp": datetime.now().isoformat(),
        "profile_id": target_profile_id,
        "status": "verified_success",
        "master_profile": {
            "source_path": str(MASTER_PROFILE_FILE),
            "target_path": str(target_profile_file),
            "sha256": orig_profile_hash,
            "verified": True,
        },
        "projects_database": {
            "source_path": str(PROJECTS_FILE),
            "target_path": str(target_projects_file),
            "sha256": orig_projects_hash,
            "verified": True,
        },
        "configuration": {
            "path": str(target_config_file),
            "has_fixed_project": True,
            "fixed_project_id": "bearing_fault_diagnosis",
        },
    }

    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(audit_record, f, indent=2)

    return audit_record
