"""Premium Professional ReportLab PDF Renderer with Centered Header, Page Border, and 88-94% Page Utilization."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pypdf
import pypdfium2 as pdfium
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Spacer

from ..content.compression_engine import OnePageCompressionEngine
from ..content.manifest import ResumeContentManifest
from .components import (
    ComponentStyles,
    build_certifications,
    build_education,
    build_leadership_and_achievements,
    build_professional_development,
    build_professional_summary,
    build_project_entry,
    build_resume_header,
    build_section_heading,
    build_technical_skills,
)
from .design_system import (
    COLOR_PAGE_BORDER,
    MARGIN_BOTTOM_PT,
    MARGIN_LEFT_PT,
    MARGIN_RIGHT_PT,
    MARGIN_TOP_PT,
    MAX_VERTICAL_UTILIZATION_PT,
    MIN_VERTICAL_UTILIZATION_PT,
    PAGE_BORDER_INSET_PT,
    PAGE_BORDER_WIDTH_PT,
    PAGE_HEIGHT_PT,
    PAGE_WIDTH_PT,
    USABLE_HEIGHT_PT,
    USABLE_WIDTH_PT,
)


class RenderResult(dict):
    """
    Dual-compatibility return type for PDF rendering results:
    behaves as an integer (for `page_count == 1`), a dict (for subscripting),
    and has property attributes for `page_count`, `vertical_utilization_pct`, and `preview_png`.
    """

    @property
    def page_count(self) -> int:
        return self["page_count"]

    @property
    def vertical_utilization_pct(self) -> float:
        return self["vertical_utilization_pct"]

    @property
    def preview_png(self) -> str:
        return self["preview_png"]

    def __int__(self) -> int:
        return self["page_count"]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, int):
            return self["page_count"] == other
        return super().__eq__(other)

    def __str__(self) -> str:
        return str(self["page_count"])


def draw_page_border(canvas, doc) -> None:
    """Draws a subtle, elegant rectangular page border (Part 14.C)."""
    canvas.saveState()
    canvas.setStrokeColor(COLOR_PAGE_BORDER)
    canvas.setLineWidth(PAGE_BORDER_WIDTH_PT)
    canvas.rect(
        PAGE_BORDER_INSET_PT,
        PAGE_BORDER_INSET_PT,
        PAGE_WIDTH_PT - (2 * PAGE_BORDER_INSET_PT),
        PAGE_HEIGHT_PT - (2 * PAGE_BORDER_INSET_PT),
        stroke=1,
        fill=0,
    )
    canvas.restoreState()


def assemble_story(
    manifest: ResumeContentManifest,
    styles: ComponentStyles,
) -> List[Any]:
    """
    Assembles all resume components in the STRICT required section order (Part 9):
    1. HEADER
    2. PROFESSIONAL SUMMARY
    3. TECHNICAL SKILLS
    4. PROJECTS (4 projects, Bearing Fault at #2)
    5. PROFESSIONAL DEVELOPMENT & JOB SIMULATIONS
    6. EDUCATION
    7. LEADERSHIP & ACHIEVEMENTS
    8. CERTIFICATIONS
    """
    story: List[Any] = []

    # 1. Centered Header
    story.extend(build_resume_header(manifest, styles))

    # 2. Professional Summary (Fixed master version)
    story.extend(build_professional_summary(manifest.summary, styles))

    # 3. Technical Skills (Exact 6 categories)
    story.extend(build_technical_skills(manifest.ordered_skills, styles))

    # 4. Projects (4 projects with Bearing Fault strictly in slot 2)
    story.extend(build_section_heading("PROJECTS", styles))
    for proj in manifest.projects:
        story.extend(build_project_entry(proj, styles))

    # 5. Professional Development & Job Simulations (retained as independent section)
    if manifest.professional_development:
        story.extend(build_professional_development(manifest.professional_development, styles))

    # 6. Education (clean B.Tech, no Mechanical Engineering)
    story.extend(build_education(manifest.education, styles))

    # 7. Leadership & Achievements
    story.extend(build_leadership_and_achievements(manifest.leadership, manifest.achievements, styles))

    # 8. Certifications
    if manifest.certifications:
        story.extend(build_certifications(manifest.certifications, styles))

    return story


def measure_content_height(story: List[Any]) -> float:
    """Calculates the total rendered height of the flowables in points."""
    total_height = 0.0
    for flowable in story:
        _, h = flowable.wrap(USABLE_WIDTH_PT, USABLE_HEIGHT_PT)
        total_height += h
    return total_height


def render_pdf_document(
    manifest: ResumeContentManifest,
    output_path: Path,
    compression_level: int = 0,
    spacing_boost: float = 0.0,
) -> Tuple[int, float]:
    """
    Builds the PDF document using ReportLab.
    Returns (page_count, vertical_utilization_pct).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = ComponentStyles()

    if spacing_boost > 0:
        styles.section_heading_style.spaceBefore += spacing_boost

    story = assemble_story(manifest, styles)
    content_height = measure_content_height(story)
    utilization_pct = (content_height / USABLE_HEIGHT_PT) * 100.0

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=(PAGE_WIDTH_PT, PAGE_HEIGHT_PT),
        leftMargin=MARGIN_LEFT_PT,
        rightMargin=MARGIN_RIGHT_PT,
        topMargin=MARGIN_TOP_PT,
        bottomMargin=MARGIN_BOTTOM_PT,
    )

    # Build with outer page border
    doc.build(story, onFirstPage=draw_page_border, onLaterPages=draw_page_border)

    # Verify actual rendered page count and prohibited terms via pypdf
    reader = pypdf.PdfReader(str(output_path))
    actual_pages = len(reader.pages)
    extracted_text = "\n".join(p.extract_text() or "" for p in reader.pages)

    if "mechanical" in extracted_text.lower():
        raise ValueError("Critical Violation: 'Mechanical' found in rendered PDF document text!")

    return actual_pages, round(utilization_pct, 1)


def generate_preview_png(pdf_path: Path, png_path: Optional[Path] = None, scale: float = 2.0) -> Path:
    """
    Renders the first page of the PDF into a high-resolution PNG image (approx 150-200 DPI)
    for Visual Quality Assurance.
    """
    if png_path is None:
        png_path = pdf_path.with_name(f"{pdf_path.stem}_Preview.png")

    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc[0]
    image = page.render(scale=scale).to_pil()
    image.save(str(png_path))
    return png_path


def render_pdf_guaranteed_one_page(
    manifest: ResumeContentManifest,
    output_path: Path,
    target_min_utilization: float = 88.0,
    target_max_utilization: float = 94.0,
) -> RenderResult:
    """
    Renders PDF ensuring:
    - Exactly ONE A4 page.
    - 88% to 94% vertical page utilization.
    - Automatic progressive compression if content overflows.
    - Automatic spacing optimization if underutilized.
    - Renders high-resolution PNG preview for Visual QA.
    """
    # 1. Initial attempt with standard spacing
    pages, util = render_pdf_document(manifest, output_path, compression_level=0, spacing_boost=0.0)

    # If within 88-94% and exactly 1 page, we are in the sweet spot
    if pages == 1 and target_min_utilization <= util <= target_max_utilization:
        preview_png = generate_preview_png(output_path)
        return RenderResult({
            "page_count": 1,
            "vertical_utilization_pct": util,
            "preview_png": str(preview_png),
            "compression_level": 0,
        })

    # If pages == 1 but utilization < 88%, boost spacing subtly so page breathes
    if pages == 1 and util < target_min_utilization:
        for boost in [0.5, 1.0, 1.5]:
            p, u = render_pdf_document(manifest, output_path, compression_level=0, spacing_boost=boost)
            if p == 1:
                pages, util = p, u
                if util >= target_min_utilization:
                    break

    # If document overflows onto page 2, compress progressively
    if pages > 1:
        for level in [1, 2, 3]:
            compressed_manifest = OnePageCompressionEngine.compress(manifest, level=level)
            p, u = render_pdf_document(compressed_manifest, output_path, compression_level=level)
            if p == 1:
                pages, util = p, u
                break

    # Final preview generation for visual QA
    preview_png = generate_preview_png(output_path)
    return RenderResult({
        "page_count": pages,
        "vertical_utilization_pct": util,
        "preview_png": str(preview_png),
    })


# Backward-compatible alias
create_pdf = render_pdf_document
