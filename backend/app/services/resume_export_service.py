"""Resume PDF and DOCX document export service with approval validation and storage management."""

import hashlib
from pathlib import Path
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.candidate import CandidateProfile
from backend.app.models.resume import FileAsset, Resume as DBResume, ResumeVersion as DBResumeVersion
from src.resume_builder.content.manifest import ResumeContentManifest
from src.resume_builder.renderers.docx_renderer import render_docx
from src.resume_builder.renderers.pdf_renderer import render_pdf_guaranteed_one_page


class ResumeExportService:
    """Exports approved resumes to guaranteed one-page PDF and Times New Roman DOCX."""

    @staticmethod
    def _get_export_dir(candidate_slug: str) -> Path:
        """Resolve and ensure export directory exists under configured storage with traversal protection."""
        import re
        safe_slug = re.sub(r"[^a-zA-Z0-9_\-]", "", candidate_slug)
        if not safe_slug:
            safe_slug = "default"
        base_dir = (settings.storage_path / "resumes" / safe_slug).resolve()
        storage_root = settings.storage_path.resolve()
        if not str(base_dir).startswith(str(storage_root)):
            raise ValueError(f"Path traversal detected in candidate slug '{candidate_slug}'.")
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        """Compute SHA256 checksum of generated file."""
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        return sha.hexdigest()

    @staticmethod
    def export_pdf(
        session: Session,
        resume: DBResume,
        enforce_approved: bool = True,
    ) -> Path:
        """Render and export approved resume to ReportLab A4 PDF."""
        # 1. Enforce approval safeguard
        if enforce_approved and resume.status != "approved":
            raise ValueError(
                f"Cannot export unapproved resume '{resume.resume_title}'. "
                "Only explicitly approved resumes can be exported to final formats."
            )

        # 2. Reconstitute manifest
        manifest = ResumeContentManifest.model_validate(resume.editable_manifest)

        # 3. Resolve candidate slug
        candidate = session.execute(
            select(CandidateProfile).filter_by(id=resume.profile_id)
        ).scalar_one_or_none()
        slug = candidate.slug if candidate else "default"

        # 4. Resolve output destination
        export_dir = ResumeExportService._get_export_dir(slug)
        filename = f"{slug}_resume_v{resume.current_version}.pdf"
        output_path = export_dir / filename

        # 5. Render PDF with guaranteed one-page engine
        render_result = render_pdf_guaranteed_one_page(manifest, output_path)

        # 6. Validate generated file
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("PDF generation failed: output file is empty or missing.")

        file_size = output_path.stat().st_size
        checksum = ResumeExportService._compute_sha256(output_path)
        storage_rel_key = f"resumes/{slug}/{filename}"

        # 7. Update ResumeVersion record
        version_obj = session.execute(
            select(DBResumeVersion).filter_by(
                resume_id=resume.id,
                version_number=resume.current_version,
            )
        ).scalar_one_or_none()
        if version_obj:
            version_obj.pdf_storage_key = storage_rel_key
            if "preview_png" in render_result and render_result["preview_png"]:
                version_obj.preview_storage_key = render_result["preview_png"]

        # 8. Record FileAsset in database
        asset = session.execute(
            select(FileAsset).filter_by(storage_key=storage_rel_key)
        ).scalar_one_or_none()
        if not asset:
            asset = FileAsset(
                id=uuid.uuid4(),
                user_id=resume.user_id,
                profile_id=resume.profile_id,
                file_name=filename,
                storage_key=storage_rel_key,
                mime_type="application/pdf",
                file_size_bytes=file_size,
                checksum_sha256=checksum,
            )
            session.add(asset)
        else:
            asset.file_size_bytes = file_size
            asset.checksum_sha256 = checksum

        session.commit()
        return output_path

    @staticmethod
    def export_docx(
        session: Session,
        resume: DBResume,
        enforce_approved: bool = True,
    ) -> Path:
        """Render and export approved resume to python-docx DOCX."""
        # 1. Enforce approval safeguard
        if enforce_approved and resume.status != "approved":
            raise ValueError(
                f"Cannot export unapproved resume '{resume.resume_title}'. "
                "Only explicitly approved resumes can be exported to final formats."
            )

        # 2. Reconstitute manifest
        manifest = ResumeContentManifest.model_validate(resume.editable_manifest)

        # 3. Resolve candidate slug
        candidate = session.execute(
            select(CandidateProfile).filter_by(id=resume.profile_id)
        ).scalar_one_or_none()
        slug = candidate.slug if candidate else "default"

        # 4. Resolve output destination
        export_dir = ResumeExportService._get_export_dir(slug)
        filename = f"{slug}_resume_v{resume.current_version}.docx"
        output_path = export_dir / filename

        # 5. Render DOCX matching design system
        render_docx(manifest, output_path)

        # 6. Validate generated file
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("DOCX generation failed: output file is empty or missing.")

        file_size = output_path.stat().st_size
        checksum = ResumeExportService._compute_sha256(output_path)
        storage_rel_key = f"resumes/{slug}/{filename}"

        # 7. Update ResumeVersion record
        version_obj = session.execute(
            select(DBResumeVersion).filter_by(
                resume_id=resume.id,
                version_number=resume.current_version,
            )
        ).scalar_one_or_none()
        if version_obj:
            version_obj.docx_storage_key = storage_rel_key

        # 8. Record FileAsset in database
        asset = session.execute(
            select(FileAsset).filter_by(storage_key=storage_rel_key)
        ).scalar_one_or_none()
        if not asset:
            asset = FileAsset(
                id=uuid.uuid4(),
                user_id=resume.user_id,
                profile_id=resume.profile_id,
                file_name=filename,
                storage_key=storage_rel_key,
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                file_size_bytes=file_size,
                checksum_sha256=checksum,
            )
            session.add(asset)
        else:
            asset.file_size_bytes = file_size
            asset.checksum_sha256 = checksum

        session.commit()
        return output_path
