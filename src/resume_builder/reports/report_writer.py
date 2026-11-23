"""Writes and organizes complete output application packages safely without overwriting."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..ats.scorer import ATSReport
from ..config import OUTPUT_DIR
from ..content.manifest import ResumeContentManifest
from ..jd_analysis.models import JobDescription, RequirementMatrix
from ..profile.models import ProjectItem
from ..renderers.docx_renderer import render_docx
from ..renderers.pdf_renderer import render_pdf_guaranteed_one_page
from ..utils.file_ops import atomic_write_json, atomic_write_text, sanitize_filename
from .summary_generator import generate_change_summary


def prepare_output_directory(
    company: str,
    role: str,
    base_output_dir: Path = OUTPUT_DIR,
    profile_id: Optional[str] = None,
) -> Path:
    """
    Creates a dedicated, timestamped folder under output/{profile_id}/2026/Company_Role_Date/.
    If an existing application exists, creates a unique versioned folder using the next version number.
    """
    year = str(datetime.now().year)
    date_str = datetime.now().strftime("%Y%m%d")

    clean_company = sanitize_filename(company, max_length=30)
    clean_role = sanitize_filename(role, max_length=30)

    folder_name = f"{clean_company}_{clean_role}_{date_str}"

    # Route output to profile-specific subdirectory if profile_id provided
    if profile_id and not base_output_dir.name == profile_id:
        target_base = base_output_dir / profile_id
    else:
        target_base = base_output_dir

    year_dir = target_base / year

    existing_dirs = list(year_dir.glob(f"{folder_name}*")) if year_dir.exists() else []
    if not existing_dirs:
        target_dir = year_dir / folder_name
    else:
        max_v = 1
        for d in existing_dirs:
            d_name = d.name
            if d_name == folder_name:
                max_v = max(max_v, 1)
            elif "_v" in d_name:
                try:
                    v_num = int(d_name.rsplit("_v", 1)[1])
                    max_v = max(max_v, v_num)
                except ValueError:
                    pass
        target_dir = year_dir / f"{folder_name}_v{max_v + 1}"

    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def write_complete_application(
    manifest: ResumeContentManifest,
    jd: JobDescription,
    req_matrix: RequirementMatrix,
    selected_projects: List[ProjectItem],
    scored_pool: List[Tuple[ProjectItem, float]],
    base_output_dir: Path = OUTPUT_DIR,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates all application artifacts into a dedicated folder:
    - PDF Resume (exactly 1 page guaranteed)
    - DOCX Resume
    - ATS_Report.txt and ATS_Report.json
    - Resume_Manifest.json
    - Extracted_Text.txt
    - Source_JD.txt
    - Change_Summary.md
    """
    out_dir = prepare_output_directory(jd.company_name, jd.job_title, base_output_dir, profile_id=profile_id)

    company_clean = sanitize_filename(jd.company_name, max_length=25)
    role_clean = sanitize_filename(jd.job_title, max_length=25)

    cand_name = manifest.personal_info.display_name or manifest.personal_info.full_name
    cand_slug = sanitize_filename(cand_name.title().replace(" ", "_"), max_length=25)

    pdf_filename = f"{cand_slug}_{company_clean}_{role_clean}_Resume.pdf"
    docx_filename = f"{cand_slug}_{company_clean}_{role_clean}_Resume.docx"

    pdf_path = out_dir / pdf_filename
    docx_path = out_dir / docx_filename

    # 1. Render PDF guaranteed 1 page
    pdf_res = render_pdf_guaranteed_one_page(manifest, pdf_path)
    page_count = int(pdf_res)
    utilization_pct = pdf_res.vertical_utilization_pct
    preview_png_path = pdf_res.preview_png

    # 2. Render DOCX
    render_docx(manifest, docx_path)

    # 3. Calculate local ATS readiness score from the ACTUAL PDF
    from ..ats.scorer import calculate_ats_readiness
    from ..profile.manager import ProfileManager
    p_cfg = None
    if profile_id:
        try:
            p_cfg = ProfileManager(profile_id=profile_id).load_profile_config()
        except Exception:
            p_cfg = None
    ats_report = calculate_ats_readiness(pdf_path, jd, req_matrix, profile_config=p_cfg)

    # 4. Save ATS Reports (txt and json)
    ats_txt_path = out_dir / "ATS_Report.txt"
    ats_json_path = out_dir / "ATS_Report.json"
    atomic_write_text(ats_txt_path, ats_report.format_console_text())
    atomic_write_json(ats_json_path, ats_report.to_dict())

    # 5. Save Resume Manifest JSON
    manifest_path = out_dir / "Resume_Manifest.json"
    atomic_write_json(manifest_path, manifest.model_dump(mode="json"))

    # 6. Save Extracted Text from PDF
    from ..ats.validator import inspect_generated_pdf
    inspection = inspect_generated_pdf(pdf_path)
    extracted_text_path = out_dir / "Extracted_Text.txt"
    atomic_write_text(extracted_text_path, inspection.extracted_text)

    # 7. Save Source JD
    source_jd_path = out_dir / "Source_JD.txt"
    atomic_write_text(source_jd_path, jd.raw_text)

    # 8. Save Change Summary MD
    change_summary = generate_change_summary(
        manifest, jd, req_matrix, ats_report, selected_projects, scored_pool
    )
    change_summary_path = out_dir / "Change_Summary.md"
    atomic_write_text(change_summary_path, change_summary)

    return {
        "output_directory": str(out_dir),
        "pdf_path": str(pdf_path),
        "docx_path": str(docx_path),
        "preview_png": str(preview_png_path),
        "ats_report_txt": str(ats_txt_path),
        "ats_report_json": str(ats_json_path),
        "manifest_path": str(manifest_path),
        "extracted_text_path": str(extracted_text_path),
        "source_jd_path": str(source_jd_path),
        "change_summary_path": str(change_summary_path),
        "ats_report": ats_report,
        "page_count": page_count,
        "vertical_utilization_pct": utilization_pct,
    }
