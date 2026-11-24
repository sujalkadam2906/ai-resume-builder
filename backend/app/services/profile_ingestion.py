"""Profile JSON/YAML ingestion, validation, and dry-run service.

Maps filesystem candidate profiles (registry.json, master_profile.json, projects.json,
profile_config.yaml) into the relational SQLAlchemy 2.0 schema with strict data preservation,
transaction integrity, duplicate detection, and non-destructive dry-run capabilities.
"""

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import yaml

from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.config import PROJECT_ROOT
from backend.app.models.candidate import (
    CandidateProfile,
    Education,
    Experience,
    Skill,
    Project,
    Certification,
    Achievement,
    ProfessionalDevelopment,
)

logger = logging.getLogger(__name__)

PROFILES_DEFAULT_DIR = PROJECT_ROOT / "profiles"


@dataclass
class ValidationIssue:
    """Detailed validation issue or non-relational field warning."""
    level: str  # "error", "warning", "info"
    profile_id: str
    source_file: str
    field_name: str
    message: str


@dataclass
class ParsedProfileBundle:
    """In-memory validated entity bundle ready for relational insertion or dry-run inspection."""
    profile_id: str
    candidate_profile_data: Dict[str, Any]
    educations: List[Dict[str, Any]] = field(default_factory=list)
    experiences: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[Dict[str, Any]] = field(default_factory=list)
    projects: List[Dict[str, Any]] = field(default_factory=list)
    certifications: List[Dict[str, Any]] = field(default_factory=list)
    achievements: List[Dict[str, Any]] = field(default_factory=list)
    professional_developments: List[Dict[str, Any]] = field(default_factory=list)
    unmapped_fields: List[str] = field(default_factory=list)


@dataclass
class ProfileDryRunSummary:
    """Per-profile validation and projected table counts."""
    profile_id: str
    candidate_name: str
    is_valid: bool
    expected_records: Dict[str, int]
    unmapped_fields: List[str]
    warnings: List[str]
    errors: List[str]
    duplicate_status: str  # "new", "exists_in_database", "uninitialized"


@dataclass
class DryRunReport:
    """Global dry-run audit report."""
    profiles_discovered: List[str]
    valid_profiles: List[str]
    invalid_profiles: List[str]
    total_expected_records: Dict[str, int]
    profile_summaries: Dict[str, ProfileDryRunSummary]
    errors: List[str]
    dry_run_mode: bool = True
    written_to_database: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize report for API or CLI consumption."""
        return {
            "dry_run_mode": self.dry_run_mode,
            "written_to_database": self.written_to_database,
            "profiles_discovered": self.profiles_discovered,
            "valid_profiles": self.valid_profiles,
            "invalid_profiles": self.invalid_profiles,
            "total_expected_records": self.total_expected_records,
            "profile_summaries": {
                pid: {
                    "profile_id": s.profile_id,
                    "candidate_name": s.candidate_name,
                    "is_valid": s.is_valid,
                    "expected_records": s.expected_records,
                    "unmapped_fields": s.unmapped_fields,
                    "warnings": s.warnings,
                    "errors": s.errors,
                    "duplicate_status": s.duplicate_status,
                }
                for pid, s in self.profile_summaries.items()
            },
            "errors": self.errors,
        }


class ProfileIngestionService:
    """Modular ingestion service with validation, dry-run auditing, and transactional loading."""

    def __init__(
        self,
        profiles_dir: Optional[Path] = None,
        db_session: Optional[Session] = None,
    ):
        self.profiles_dir = Path(profiles_dir or PROFILES_DEFAULT_DIR)
        self.db_session = db_session

    def discover_profiles(self) -> List[str]:
        """Discover initialized candidate profile slugs from registry.json and filesystem directories."""
        discovered: Set[str] = set()

        if not self.profiles_dir.exists():
            return []

        # 1. Read registry.json catalog if available
        registry_path = self.profiles_dir / "registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    reg_data = json.load(f)
                    for pid, meta in reg_data.get("profiles", {}).items():
                        profile_dir = self.profiles_dir / pid
                        # Only discover profiles with initialized files
                        if (profile_dir / "master_profile.json").exists():
                            discovered.add(pid)
            except Exception as e:
                logger.warning("Error reading registry.json: %s", e)

        # 2. Filesystem sweep for any directory containing master_profile.json
        for sub_dir in self.profiles_dir.iterdir():
            if sub_dir.is_dir() and not sub_dir.name.startswith((".", "_", "backups", "audit")):
                if (sub_dir / "master_profile.json").exists():
                    discovered.add(sub_dir.name)

        return sorted(list(discovered))

    def validate_and_parse_profile(
        self,
        profile_id: str,
    ) -> Tuple[Optional[ParsedProfileBundle], List[ValidationIssue]]:
        """Parse JSON/YAML files for a candidate profile, perform validations, and map to relational entities."""
        issues: List[ValidationIssue] = []
        profile_dir = self.profiles_dir / profile_id

        if not profile_dir.exists() or not profile_dir.is_dir():
            issues.append(
                ValidationIssue(
                    level="error",
                    profile_id=profile_id,
                    source_file="",
                    field_name="",
                    message=f"Profile directory not found: {profile_dir}",
                )
            )
            return None, issues

        master_file = profile_dir / "master_profile.json"
        projects_file = profile_dir / "projects.json"
        config_file = profile_dir / "profile_config.yaml"

        if not master_file.exists():
            issues.append(
                ValidationIssue(
                    level="error",
                    profile_id=profile_id,
                    source_file="master_profile.json",
                    field_name="master_profile.json",
                    message="Missing mandatory master_profile.json",
                )
            )
            return None, issues

        # ----------------------------------------------------------------------
        # 1. Parse master_profile.json
        # ----------------------------------------------------------------------
        try:
            with open(master_file, "r", encoding="utf-8") as f:
                master_raw = json.load(f)
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    level="error",
                    profile_id=profile_id,
                    source_file="master_profile.json",
                    field_name="json_syntax",
                    message=f"JSON syntax error in master_profile.json: {exc}",
                )
            )
            return None, issues

        # ----------------------------------------------------------------------
        # 2. Parse profile_config.yaml (if present)
        # ----------------------------------------------------------------------
        config_raw: Dict[str, Any] = {}
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_raw = yaml.safe_load(f) or {}
            except Exception as exc:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        profile_id=profile_id,
                        source_file="profile_config.yaml",
                        field_name="yaml_syntax",
                        message=f"Error parsing profile_config.yaml: {exc}; using fallback config",
                    )
                )

        # ----------------------------------------------------------------------
        # 3. Parse projects.json (if present)
        # ----------------------------------------------------------------------
        projects_raw: List[Dict[str, Any]] = []
        if projects_file.exists():
            try:
                with open(projects_file, "r", encoding="utf-8") as f:
                    projects_raw = json.load(f)
                if not isinstance(projects_raw, list):
                    issues.append(
                        ValidationIssue(
                            level="error",
                            profile_id=profile_id,
                            source_file="projects.json",
                            field_name="root",
                            message="projects.json must contain a JSON array of projects",
                        )
                    )
                    return None, issues
            except Exception as exc:
                issues.append(
                    ValidationIssue(
                        level="error",
                        profile_id=profile_id,
                        source_file="projects.json",
                        field_name="json_syntax",
                        message=f"JSON syntax error in projects.json: {exc}",
                    )
                )
                return None, issues

        # ----------------------------------------------------------------------
        # 4. Map & Validate candidate_profiles Entity
        # ----------------------------------------------------------------------
        personal_info = master_raw.get("personal_info", {})
        if not personal_info or not personal_info.get("full_name"):
            issues.append(
                ValidationIssue(
                    level="error",
                    profile_id=profile_id,
                    source_file="master_profile.json",
                    field_name="personal_info.full_name",
                    message="Missing mandatory personal_info.full_name",
                )
            )
            return None, issues

        full_name = str(personal_info.get("full_name", "")).strip()
        display_name = str(personal_info.get("display_name", "")).strip() or full_name
        email = personal_info.get("email")
        phone = personal_info.get("phone")
        location = personal_info.get("location")
        open_to_relocate = bool(personal_info.get("open_to_relocate", True))
        immediate_joiner = bool(personal_info.get("immediate_joiner", True))

        # Determine active headline & summary
        headline_rule = config_raw.get("headline_rule", {})
        summary_rule = config_raw.get("summary_rule", {})

        headlines_data = master_raw.get("headlines", {})
        summaries_data = master_raw.get("summaries", {})

        professional_headline = (
            headline_rule.get("permanent_headline")
            if headline_rule.get("mode") == "permanent" and headline_rule.get("permanent_headline")
            else None
        )
        if not professional_headline and isinstance(headlines_data, dict):
            professional_headline = headlines_data.get("primary") or headlines_data.get("general")
        elif not professional_headline and isinstance(headlines_data, list) and headlines_data:
            professional_headline = headlines_data[0]

        professional_summary = (
            summary_rule.get("permanent_summary")
            if summary_rule.get("mode") == "permanent" and summary_rule.get("permanent_summary")
            else None
        )
        if not professional_summary and isinstance(summaries_data, dict):
            professional_summary = (
                summaries_data.get("permanent")
                or summaries_data.get("general")
                or summaries_data.get("master")
            )
        elif not professional_summary and isinstance(summaries_data, list) and summaries_data:
            professional_summary = summaries_data[0]

        # Gather custom configuration rules & non-relational fields
        config_rules: Dict[str, Any] = {
            "headline_rule": headline_rule,
            "summary_rule": summary_rule,
            "prohibited_terms": config_raw.get("prohibited_terms", []),
            "project_selection": config_raw.get("project_selection", {}),
            "sections_order": config_raw.get("sections_order", []),
            "theme": config_raw.get("theme", "editorial_teal_copper"),
            "source_entity_ids": {
                "experiences": {},
                "achievements": {},
                "professional_developments": {},
            },
        }

        # Track and preserve special/non-relational master profile fields
        unmapped_fields: List[str] = []
        known_master_keys = {
            "personal_info",
            "links",
            "headlines",
            "summaries",
            "education",
            "technical_skills",
            "leadership_and_experience",
            "professional_development",
            "achievements",
            "certifications",
            "research_publications",
            "reconciliation_metadata",
            "_notice",
        }
        for k, v in master_raw.items():
            if k not in known_master_keys:
                unmapped_fields.append(f"master_profile.{k}")
                config_rules.setdefault("extra_fields", {})[k] = v
                issues.append(
                    ValidationIssue(
                        level="info",
                        profile_id=profile_id,
                        source_file="master_profile.json",
                        field_name=k,
                        message=f"Preserving non-relational top-level field '{k}' in config_rules['extra_fields']",
                    )
                )

        if "research_publications" in master_raw:
            config_rules["research_publications"] = master_raw["research_publications"]
        if "reconciliation_metadata" in master_raw:
            config_rules["reconciliation_metadata"] = master_raw["reconciliation_metadata"]
        if "_notice" in master_raw:
            config_rules["_notice"] = master_raw["_notice"]

        # Read registry metadata if exists
        registry_path = self.profiles_dir / "registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    reg = json.load(f)
                    if profile_id in reg.get("profiles", {}):
                        config_rules["registry_entry"] = reg["profiles"][profile_id]
            except Exception:
                pass

        candidate_profile_record = {
            "id": uuid.uuid4(),
            "slug": profile_id,
            "full_name": full_name,
            "display_name": display_name,
            "email": email,
            "phone": phone,
            "location": location,
            "open_to_relocate": open_to_relocate,
            "immediate_joiner": immediate_joiner,
            "professional_headline": professional_headline,
            "professional_summary": professional_summary,
            "headlines": headlines_data if isinstance(headlines_data, dict) else {"items": headlines_data},
            "summaries": summaries_data if isinstance(summaries_data, dict) else {"items": summaries_data},
            "links": master_raw.get("links", {}),
            "config_rules": config_rules,
            "is_synthetic": bool(config_raw.get("is_synthetic", False)),
        }

        bundle = ParsedProfileBundle(
            profile_id=profile_id,
            candidate_profile_data=candidate_profile_record,
            unmapped_fields=unmapped_fields,
        )

        profile_uuid = candidate_profile_record["id"]

        # ----------------------------------------------------------------------
        # 5. Map Education Records
        # ----------------------------------------------------------------------
        for idx, edu in enumerate(master_raw.get("education", [])):
            if not isinstance(edu, dict):
                continue
            bundle.educations.append({
                "id": uuid.uuid4(),
                "profile_id": profile_uuid,
                "degree": str(edu.get("degree", "Degree")).strip(),
                "institution": str(edu.get("institution", "Institution")).strip(),
                "duration": edu.get("duration"),
                "start_year": edu.get("start_year"),
                "end_year": edu.get("end_year"),
                "cgpa": edu.get("cgpa"),
                "score": edu.get("score"),
                "scale": edu.get("scale"),
                "source": edu.get("source", "verified_both"),
                "display_order": idx,
            })

        # ----------------------------------------------------------------------
        # 6. Map Experience Records
        # ----------------------------------------------------------------------
        for idx, exp in enumerate(master_raw.get("leadership_and_experience", [])):
            if not isinstance(exp, dict):
                continue
            exp_uuid = uuid.uuid4()
            if "id" in exp:
                config_rules["source_entity_ids"]["experiences"][str(exp_uuid)] = exp["id"]

            bundle.experiences.append({
                "id": exp_uuid,
                "profile_id": profile_uuid,
                "role": str(exp.get("role", "Role")).strip(),
                "organization": str(exp.get("organization", "Organization")).strip(),
                "duration": exp.get("duration"),
                "metrics": exp.get("metrics"),
                "description": exp.get("description"),
                "bullets": exp.get("bullets", []) if isinstance(exp.get("bullets"), list) else [],
                "source": exp.get("source", "verified_both"),
                "display_order": idx,
            })

        # ----------------------------------------------------------------------
        # 7. Map Technical Skills
        # ----------------------------------------------------------------------
        skills_dict = master_raw.get("technical_skills", {})
        if isinstance(skills_dict, dict):
            for cat, skill_list in skills_dict.items():
                if isinstance(skill_list, list):
                    for idx, s_name in enumerate(skill_list):
                        if isinstance(s_name, str) and s_name.strip():
                            bundle.skills.append({
                                "id": uuid.uuid4(),
                                "profile_id": profile_uuid,
                                "category": cat,
                                "skill_name": s_name.strip(),
                                "display_order": idx,
                            })

        # ----------------------------------------------------------------------
        # 8. Map Projects
        # ----------------------------------------------------------------------
        known_proj_keys = {
            "id", "title", "subtitle", "is_fixed_project", "fixed_position",
            "categories", "skills", "links", "bullets", "metrics",
            "evidence_source", "verification_status", "notice"
        }
        for idx, p in enumerate(projects_raw):
            if not isinstance(p, dict):
                continue
            p_slug = p.get("id") or f"project_{idx + 1}"
            
            # Check for unknown project keys
            for pk in p.keys():
                if pk not in known_proj_keys:
                    bundle.unmapped_fields.append(f"projects[{p_slug}].{pk}")

            bundle.projects.append({
                "id": uuid.uuid4(),
                "profile_id": profile_uuid,
                "slug": p_slug,
                "title": str(p.get("title", "Project")).strip(),
                "subtitle": p.get("subtitle"),
                "notice": p.get("notice"),
                "is_fixed_project": bool(p.get("is_fixed_project", False)),
                "fixed_position": p.get("fixed_position"),
                "display_order": idx,
                "categories": p.get("categories", []) if isinstance(p.get("categories"), list) else [],
                "skills": p.get("skills", []) if isinstance(p.get("skills"), list) else [],
                "links": p.get("links", []) if isinstance(p.get("links"), list) else [],
                "bullets": p.get("bullets", []) if isinstance(p.get("bullets"), list) else [],
                "metrics": p.get("metrics", []) if isinstance(p.get("metrics"), list) else [],
                "evidence_source": p.get("evidence_source"),
                "verification_status": p.get("verification_status", "verified"),
            })

        # ----------------------------------------------------------------------
        # 9. Map Certifications
        # ----------------------------------------------------------------------
        for idx, cert in enumerate(master_raw.get("certifications", [])):
            cert_name = cert if isinstance(cert, str) else cert.get("name", "") if isinstance(cert, dict) else str(cert)
            bundle.certifications.append({
                "id": uuid.uuid4(),
                "profile_id": profile_uuid,
                "name": cert_name.strip(),
                "issuer": None,
                "issue_date": None,
                "display_order": idx,
            })

        # ----------------------------------------------------------------------
        # 10. Map Achievements
        # ----------------------------------------------------------------------
        for idx, ach in enumerate(master_raw.get("achievements", [])):
            if not isinstance(ach, dict):
                continue
            ach_uuid = uuid.uuid4()
            if "id" in ach:
                config_rules["source_entity_ids"]["achievements"][str(ach_uuid)] = ach["id"]

            bundle.achievements.append({
                "id": ach_uuid,
                "profile_id": profile_uuid,
                "title": str(ach.get("title", "Achievement")).strip(),
                "description": ach.get("description"),
                "bullets": ach.get("bullets", []) if isinstance(ach.get("bullets"), list) else [],
                "source": ach.get("source", "verified_both"),
                "display_order": idx,
            })

        # ----------------------------------------------------------------------
        # 11. Map Professional Development
        # ----------------------------------------------------------------------
        for idx, pd in enumerate(master_raw.get("professional_development", [])):
            if not isinstance(pd, dict):
                continue
            pd_uuid = uuid.uuid4()
            if "id" in pd:
                config_rules["source_entity_ids"]["professional_developments"][str(pd_uuid)] = pd["id"]

            bundle.professional_developments.append({
                "id": pd_uuid,
                "profile_id": profile_uuid,
                "title": str(pd.get("title", "Course / Workshop")).strip(),
                "organization": str(pd.get("organization", "Platform")).strip(),
                "date": pd.get("date"),
                "bullets": pd.get("bullets", []) if isinstance(pd.get("bullets"), list) else [],
                "source": pd.get("source"),
                "conflict_note": pd.get("conflict_note"),
                "display_order": idx,
            })

        return bundle, issues

    def dry_run(
        self,
        target_profile_ids: Optional[List[str]] = None,
        check_database_duplicates: bool = True,
    ) -> DryRunReport:
        """Execute a non-destructive audit and dry-run validation.
        
        Guarantees that NO modifications, inserts, or updates are written to the database.
        """
        discovered = target_profile_ids or self.discover_profiles()
        valid_profiles: List[str] = []
        invalid_profiles: List[str] = []
        total_records: Dict[str, int] = {
            "candidate_profiles": 0,
            "educations": 0,
            "experiences": 0,
            "skills": 0,
            "projects": 0,
            "certifications": 0,
            "achievements": 0,
            "professional_developments": 0,
        }
        summaries: Dict[str, ProfileDryRunSummary] = {}
        global_errors: List[str] = []

        # Optional read-only duplicate inspection against existing DB records
        existing_slugs: Set[str] = set()
        if check_database_duplicates and self.db_session is not None:
            try:
                res = self.db_session.execute(select(CandidateProfile.slug)).scalars().all()
                existing_slugs = set(res)
            except Exception as e:
                logger.warning("Could not query existing DB slugs for duplicate check: %s", e)

        for pid in discovered:
            bundle, issues = self.validate_and_parse_profile(pid)
            errors = [i.message for i in issues if i.level == "error"]
            warnings = [i.message for i in issues if i.level == "warning"]

            if bundle is None or errors:
                invalid_profiles.append(pid)
                summaries[pid] = ProfileDryRunSummary(
                    profile_id=pid,
                    candidate_name="Invalid / Incomplete",
                    is_valid=False,
                    expected_records={},
                    unmapped_fields=[],
                    warnings=warnings,
                    errors=errors,
                    duplicate_status="uninitialized",
                )
                continue

            valid_profiles.append(pid)
            dup_status = "exists_in_database" if pid in existing_slugs else "new"

            rec_counts = {
                "candidate_profiles": 1,
                "educations": len(bundle.educations),
                "experiences": len(bundle.experiences),
                "skills": len(bundle.skills),
                "projects": len(bundle.projects),
                "certifications": len(bundle.certifications),
                "achievements": len(bundle.achievements),
                "professional_developments": len(bundle.professional_developments),
            }

            for table_name, count in rec_counts.items():
                total_records[table_name] += count

            summaries[pid] = ProfileDryRunSummary(
                profile_id=pid,
                candidate_name=bundle.candidate_profile_data["full_name"],
                is_valid=True,
                expected_records=rec_counts,
                unmapped_fields=bundle.unmapped_fields,
                warnings=warnings,
                errors=[],
                duplicate_status=dup_status,
            )

        return DryRunReport(
            profiles_discovered=discovered,
            valid_profiles=valid_profiles,
            invalid_profiles=invalid_profiles,
            total_expected_records=total_records,
            profile_summaries=summaries,
            errors=global_errors,
            dry_run_mode=True,
            written_to_database=False,
        )

    def import_profile(
        self,
        bundle: ParsedProfileBundle,
        session: Session,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Transactional, idempotent import of a parsed bundle into a database session.
        
        Designed for stage 2B execution and unit-tested in isolated SQLite fixtures.
        """
        slug = bundle.profile_id
        existing = session.execute(
            select(CandidateProfile).filter_by(slug=slug)
        ).scalar_one_or_none()

        if existing is not None:
            if not overwrite:
                return {
                    "status": "skipped",
                    "reason": "duplicate_profile",
                    "profile_id": slug,
                    "db_id": str(existing.id),
                }
            # Cascade delete existing profile records before re-inserting
            session.delete(existing)
            session.flush()

        # Insert CandidateProfile
        profile_row = CandidateProfile(**bundle.candidate_profile_data)
        session.add(profile_row)
        session.flush()

        # Insert child records linked to profile_row.id
        pid = profile_row.id
        for edu in bundle.educations:
            edu_data = {**edu, "profile_id": pid}
            session.add(Education(**edu_data))

        for exp in bundle.experiences:
            exp_data = {**exp, "profile_id": pid}
            session.add(Experience(**exp_data))

        for sk in bundle.skills:
            sk_data = {**sk, "profile_id": pid}
            session.add(Skill(**sk_data))

        for prj in bundle.projects:
            prj_data = {**prj, "profile_id": pid}
            session.add(Project(**prj_data))

        for cert in bundle.certifications:
            cert_data = {**cert, "profile_id": pid}
            session.add(Certification(**cert_data))

        for ach in bundle.achievements:
            ach_data = {**ach, "profile_id": pid}
            session.add(Achievement(**ach_data))

        for pd in bundle.professional_developments:
            pd_data = {**pd, "profile_id": pid}
            session.add(ProfessionalDevelopment(**pd_data))

        session.flush()

        return {
            "status": "imported",
            "profile_id": slug,
            "db_id": str(profile_row.id),
            "records_created": {
                "educations": len(bundle.educations),
                "experiences": len(bundle.experiences),
                "skills": len(bundle.skills),
                "projects": len(bundle.projects),
                "certifications": len(bundle.certifications),
                "achievements": len(bundle.achievements),
                "professional_developments": len(bundle.professional_developments),
            },
        }

    def import_all(
        self,
        session: Session,
        target_profile_ids: Optional[List[str]] = None,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Atomically import all targeted candidate profiles in a single database transaction.
        
        If any candidate profile fails validation or insertion, rolls back the entire transaction.
        """
        pids = target_profile_ids or self.discover_profiles()
        results: Dict[str, Any] = {}

        # Validate all bundles first before writing anything
        bundles: List[ParsedProfileBundle] = []
        for pid in pids:
            bundle, issues = self.validate_and_parse_profile(pid)
            errors = [i.message for i in issues if i.level == "error"]
            if not bundle or errors:
                raise ValueError(f"Profile '{pid}' failed validation with errors: {errors}")
            bundles.append(bundle)

        # Single atomic transaction for all profiles
        try:
            with session.begin_nested() if session.in_transaction() else session.begin():
                for b in bundles:
                    res = self.import_profile(b, session, overwrite=overwrite)
                    results[b.profile_id] = res
        except Exception as exc:
            logger.error("Atomic profile import failed, rolled back: %s", exc)
            raise

        return results
