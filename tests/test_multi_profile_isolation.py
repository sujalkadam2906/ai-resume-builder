"""Comprehensive Multi-Profile Isolation, Security, and Regression Test Suite."""

import copy
import hashlib
import json
from pathlib import Path
import pytest

from resume_builder.config import PROFILES_DIR, PROJECT_ROOT, get_profile_dir
from resume_builder.content.generator import build_resume_manifest
from resume_builder.jd_analysis.models import JobDescription
from resume_builder.profile.manager import ProfileManager
from resume_builder.profile.migration import compute_file_sha256, migrate_sujal_profile
from resume_builder.profile.models import MasterProfile, ProfileConfig, ProjectItem
from resume_builder.project_selection.selector import select_projects_for_jd
from resume_builder.reports.report_writer import prepare_output_directory


# 1. Registry Integrity
def test_registry_integrity():
    registry_file = PROFILES_DIR / "registry.json"
    assert registry_file.exists(), "Registry file must exist under profiles/"
    with open(registry_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "profiles" in data
    profiles = data["profiles"]
    assert "sujal" in profiles
    assert "demo_candidate" in profiles
    assert profiles["sujal"]["candidate_display_name"] == "Sujal Sunil Kadam"
    assert "Aarav Sharma" in profiles["demo_candidate"]["candidate_display_name"]


# 2. Sujal Directory Structure
def test_profile_directory_structure_sujal():
    sujal_dir = PROFILES_DIR / "sujal"
    assert sujal_dir.is_dir()
    assert (sujal_dir / "master_profile.json").is_file()
    assert (sujal_dir / "projects.json").is_file()
    assert (sujal_dir / "profile_config.yaml").is_file()
    assert (sujal_dir / "source_resumes").is_dir()
    assert (sujal_dir / "backups").is_dir()
    assert (sujal_dir / "audit").is_dir()


# 3. Demo Candidate Directory Structure
def test_profile_directory_structure_demo():
    demo_dir = PROFILES_DIR / "demo_candidate"
    assert demo_dir.is_dir()
    assert (demo_dir / "master_profile.json").is_file()
    assert (demo_dir / "projects.json").is_file()
    assert (demo_dir / "profile_config.yaml").is_file()
    assert (demo_dir / "source_resumes").is_dir()
    assert (demo_dir / "backups").is_dir()
    assert (demo_dir / "audit").is_dir()


# 4. Profile Isolation: Sujal contains no Demo data
def test_profile_isolation_sujal_no_demo_leak():
    sujal_dir = PROFILES_DIR / "sujal"
    for fname in ["master_profile.json", "projects.json", "profile_config.yaml"]:
        text = (sujal_dir / fname).read_text(encoding="utf-8").lower()
        assert "aarav" not in text
        assert "aaravsharma" not in text
        assert "formforge" not in text
        assert "cloudcanvas" not in text
        assert "cryptopulse" not in text


# 5. Profile Isolation: Demo contains no Sujal data
def test_profile_isolation_demo_no_sujal_leak():
    demo_dir = PROFILES_DIR / "demo_candidate"
    sujal_dir = PROFILES_DIR / "sujal"
    sujal_phone = ""
    sujal_email = ""
    if (sujal_dir / "master_profile.json").exists():
        import json
        with open(sujal_dir / "master_profile.json", "r", encoding="utf-8") as f:
            s_data = json.load(f)
            sujal_phone = s_data.get("personal_info", {}).get("phone", "")
            sujal_email = s_data.get("personal_info", {}).get("email", "")
    for fname in ["master_profile.json", "projects.json", "profile_config.yaml"]:
        text = (demo_dir / fname).read_text(encoding="utf-8").lower()
        assert "sujal" not in text
        assert "kadam" not in text
        assert "bearing fault" not in text
        if sujal_phone:
            assert sujal_phone.replace(" ", "") not in text.replace(" ", "")
        if sujal_email:
            assert sujal_email not in text
        assert "kolhapur" not in text


# 6. Security: Path Traversal Protection
def test_profile_path_traversal_protection():
    traversal_attempts = [
        "../something",
        "..\\something",
        "sujal/../demo_candidate",
        "../../etc/passwd",
        "/etc/passwd",
        "C:\\Windows\\System32",
    ]
    for attempt in traversal_attempts:
        with pytest.raises(ValueError, match="Invalid profile ID|traversal"):
            get_profile_dir(attempt)


# 7. Security: Invalid Profile ID Characters Rejection
def test_invalid_profile_id_rejection():
    invalid_ids = ["sujal kadam", "sujal@kadam", "profile$1", "test*", ""]
    for bad_id in invalid_ids:
        with pytest.raises(ValueError):
            get_profile_dir(bad_id)


# 8. Unknown Profile Raises FileNotFoundError
def test_unknown_profile_not_found():
    pm = ProfileManager(profile_id="non_existent_candidate_xyz")
    with pytest.raises(FileNotFoundError):
        pm.load_profile()


# 9. Migration Idempotency
def test_migration_idempotency():
    res1 = migrate_sujal_profile("sujal")
    sujal_dir = PROFILES_DIR / "sujal"
    hash_p1 = compute_file_sha256(sujal_dir / "master_profile.json")
    hash_pr1 = compute_file_sha256(sujal_dir / "projects.json")

    res2 = migrate_sujal_profile("sujal")
    hash_p2 = compute_file_sha256(sujal_dir / "master_profile.json")
    hash_pr2 = compute_file_sha256(sujal_dir / "projects.json")

    assert res2["status"] == "verified_success"
    assert hash_p1 == hash_p2
    assert hash_pr1 == hash_pr2


# 10. SHA-256 Hash Matching with Legacy Data
def test_migration_sha256_hash_match():
    legacy_profile = PROJECT_ROOT / "data" / "master_profile.json"
    migrated_profile = PROFILES_DIR / "sujal" / "master_profile.json"
    if legacy_profile.exists() and migrated_profile.exists():
        assert compute_file_sha256(legacy_profile) == compute_file_sha256(migrated_profile)


# 11. Demo Candidate Synthetic Flag
def test_demo_fixture_synthetic_flag():
    pm = ProfileManager(profile_id="demo_candidate")
    cfg = pm.load_profile_config()
    assert cfg.is_synthetic is True


# 12. Sujal Candidate Non-Synthetic Flag
def test_sujal_fixture_not_synthetic():
    pm = ProfileManager(profile_id="sujal")
    cfg = pm.load_profile_config()
    assert cfg.is_synthetic is False


# 13. Sujal Fixed Project Rule: Bearing Fault at #2
def test_sujal_fixed_project_rule_bearing_fault():
    pm = ProfileManager(profile_id="sujal")
    cfg = pm.load_profile_config()
    assert cfg.project_selection.has_fixed_project is True
    assert cfg.project_selection.fixed_project is not None
    assert cfg.project_selection.fixed_project.id == "bearing_fault_diagnosis"
    assert cfg.project_selection.fixed_project.position == 2


# 14. Demo Candidate Fixed Project Rule: Dynamic
def test_demo_fixed_project_rule_dynamic():
    pm = ProfileManager(profile_id="demo_candidate")
    cfg = pm.load_profile_config()
    assert cfg.project_selection.has_fixed_project is False


# 15. Project Selector Respects Sujal Fixed Rule
def test_selector_respects_sujal_fixed_rule():
    pm = ProfileManager(profile_id="sujal")
    projects = pm.load_projects()
    cfg = pm.load_profile_config()

    jd = JobDescription(
        raw_text="Seeking Senior Java Backend Engineer with Spring Boot and AWS",
        company_name="Enterprise Java",
        job_title="Java Backend Engineer",
        required_skills=["Java", "Spring Boot", "AWS"],
    )

    selected, scored, shortage = select_projects_for_jd(
        all_projects=projects,
        jd=jd,
        selection_config=cfg.project_selection,
    )

    assert len(selected) == 4
    assert selected[1].id == "bearing_fault_diagnosis"
    assert "bearing" in selected[1].title.lower()


# 16. Project Selector Respects Demo Dynamic Ranking (No Bearing Fault)
def test_selector_respects_demo_dynamic_ranking():
    pm = ProfileManager(profile_id="demo_candidate")
    projects = pm.load_projects()
    cfg = pm.load_profile_config()

    jd = JobDescription(
        raw_text="Frontend Developer needed with React 18, TypeScript, and Tailwind",
        company_name="WebDesign Studio",
        job_title="Frontend Developer",
        required_skills=["React 18", "TypeScript", "Tailwind CSS"],
    )

    selected, scored, shortage = select_projects_for_jd(
        all_projects=projects,
        jd=jd,
        selection_config=cfg.project_selection,
    )

    assert len(selected) == 4
    # Demo projects must be purely frontend, bearing fault should NOT appear
    for p in selected:
        assert "bearing" not in p.id.lower()
        assert "bearing" not in p.title.lower()


# 17. Generator Respects Sujal Permanent Headline
def test_generator_respects_profile_headline_sujal():
    from resume_builder.ai.structured_schemas import TailoredResumeContent
    pm = ProfileManager(profile_id="sujal")
    profile = pm.load_profile()
    projects = pm.load_projects()
    cfg = pm.load_profile_config()

    dummy_ai = TailoredResumeContent(
        professional_headline="Injected Temporary Role",
        professional_summary="Temporary summary",
    )
    jd = JobDescription(raw_text="Java Role", company_name="Corp", job_title="Engineer")

    manifest = build_resume_manifest(
        profile=profile,
        selected_projects=projects[:4],
        tailored_ai=dummy_ai,
        jd=jd,
        model_used="offline",
        profile_config=cfg,
    )

    assert manifest.headline == cfg.headline_rule.permanent_headline
    assert "Full Stack Developer" in manifest.headline


# 18. Generator Respects Demo Headline Rule
def test_generator_respects_profile_headline_demo():
    from resume_builder.ai.structured_schemas import TailoredResumeContent
    pm = ProfileManager(profile_id="demo_candidate")
    profile = pm.load_profile()
    projects = pm.load_projects()
    cfg = pm.load_profile_config()

    dummy_ai = TailoredResumeContent(
        professional_headline="Injected Temporary Role",
        professional_summary="Temporary summary",
    )
    jd = JobDescription(raw_text="Frontend Role", company_name="WebCorp", job_title="Developer")

    manifest = build_resume_manifest(
        profile=profile,
        selected_projects=projects[:4],
        tailored_ai=dummy_ai,
        jd=jd,
        model_used="offline",
        profile_config=cfg,
    )

    assert manifest.headline == cfg.headline_rule.permanent_headline
    assert "Junior Frontend Developer" in manifest.headline
    assert "Sujal" not in manifest.headline


# 19. Generator Prohibited Terms: Sujal Excludes Mechanical Engineering
def test_generator_prohibited_terms_sujal():
    from resume_builder.ai.structured_schemas import TailoredResumeContent
    pm = ProfileManager(profile_id="sujal")
    profile = pm.load_profile()
    projects = pm.load_projects()
    cfg = pm.load_profile_config()

    dummy_ai = TailoredResumeContent()
    jd = JobDescription(raw_text="General JD", company_name="Corp", job_title="Dev")

    manifest = build_resume_manifest(
        profile=profile,
        selected_projects=projects[:4],
        tailored_ai=dummy_ai,
        jd=jd,
        model_used="offline",
        profile_config=cfg,
    )

    manifest_json = manifest.model_dump_json().lower()
    assert "mechanical engineering" not in manifest_json
    assert "mechanical engineer" not in manifest_json


# 20. Generator Prohibited Terms: Demo Retains Degree Cleanly
def test_generator_prohibited_terms_demo():
    from resume_builder.ai.structured_schemas import TailoredResumeContent
    pm = ProfileManager(profile_id="demo_candidate")
    profile = pm.load_profile()
    projects = pm.load_projects()
    cfg = pm.load_profile_config()

    dummy_ai = TailoredResumeContent()
    jd = JobDescription(raw_text="Frontend JD", company_name="WebLab", job_title="Dev")

    manifest = build_resume_manifest(
        profile=profile,
        selected_projects=projects[:4],
        tailored_ai=dummy_ai,
        jd=jd,
        model_used="offline",
        profile_config=cfg,
    )

    # Aarav's degree (Computer Science) must be present
    assert len(manifest.education) >= 1
    assert "Computer Science" in manifest.education[0].degree


# 21. Marker Injection: Zero Cross-Profile Data Leakage
def test_marker_injection_zero_cross_leakage():
    from resume_builder.ai.structured_schemas import TailoredResumeContent
    pm_demo = ProfileManager(profile_id="demo_candidate")
    pm_sujal = ProfileManager(profile_id="sujal")

    sujal_prof = pm_sujal.load_profile()
    sujal_projs = pm_sujal.load_projects()
    sujal_cfg = pm_sujal.load_profile_config()

    # Secret UUID marker injected ONLY into demo profile
    secret_marker = "SECRET_MARKER_UUID_9876543210_XYZ"
    demo_prof = pm_demo.load_profile()
    demo_prof.personal_info.full_name = f"Aarav Sharma {secret_marker}"

    jd = JobDescription(raw_text="Engineering Role", company_name="SafeCorp", job_title="SE")
    sujal_manifest = build_resume_manifest(
        profile=sujal_prof,
        selected_projects=sujal_projs[:4],
        tailored_ai=TailoredResumeContent(),
        jd=jd,
        model_used="offline",
        profile_config=sujal_cfg,
    )

    sujal_dump = sujal_manifest.model_dump_json()
    assert secret_marker not in sujal_dump, "CRITICAL ERROR: Cross-profile marker leaked into Sujal's manifest!"


# 22. Report Writer Directory Routing
def test_report_writer_routes_to_profile_output():
    out_demo = prepare_output_directory(
        company="TestCompany",
        role="FrontendEngineer",
        profile_id="demo_candidate",
    )
    assert "demo_candidate" in str(out_demo), f"Output directory must be partitioned by profile: {out_demo}"

    out_sujal = prepare_output_directory(
        company="TestCompany",
        role="JavaBackendEngineer",
        profile_id="sujal",
    )
    assert "sujal" in str(out_sujal), f"Output directory must be partitioned by profile: {out_sujal}"


# 23. Profile Listing
def test_cli_list_profiles():
    profiles = ProfileManager.list_all_profiles()
    assert len(profiles) >= 2
    ids = [p["profile_id"] for p in profiles]
    assert "sujal" in ids
    assert "demo_candidate" in ids


# 24. Create Profile
def test_cli_create_profile(tmp_path):
    import shutil
    test_id = "test_candidate_fixture"
    test_dir = PROFILES_DIR / test_id
    registry_file = PROFILES_DIR / "registry.json"
    original_registry = registry_file.read_text(encoding="utf-8") if registry_file.exists() else None

    try:
        # Ensure clean state
        if test_dir.exists():
            shutil.rmtree(test_dir)

        created = ProfileManager.create_new_profile(
            profile_id=test_id,
            candidate_name="Test Candidate Fixture",
        )
        assert created["profile_id"] == test_id
        assert test_dir.is_dir()
        assert (test_dir / "profile_config.yaml").is_file()

        # Check in list
        listed = ProfileManager.list_all_profiles()
        assert any(p["profile_id"] == test_id for p in listed)
    finally:
        # Clean up created test profile
        if test_dir.exists():
            shutil.rmtree(test_dir)
        if original_registry is not None:
            registry_file.write_text(original_registry, encoding="utf-8")
        elif registry_file.exists():
            registry_file.unlink()
