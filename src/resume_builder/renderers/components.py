"""Modular Layout Components for ReportLab Document Rendering with Times New Roman and Centered Header."""

from typing import Any, Dict, List, Optional
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ..content.manifest import ManifestProject, ResumeContentManifest
from ..profile.models import AchievementItem, EducationItem, LeadershipItem, ProfessionalDevelopmentItem
from ..utils.text_cleaner import escape_xml
from .design_system import (
    COLOR_FOREST_GREEN,
    COLOR_HYPERLINK,
    COLOR_LIGHT_DIVIDER,
    COLOR_MAIN_GRAPHITE,
    COLOR_MAIN_TEXT,
    COLOR_MUTED_BLUE,
    COLOR_PALE_MINT,
    COLOR_PRIMARY_NAVY,
    COLOR_PRIMARY_TEAL,
    COLOR_PROJECT_TECH,
    COLOR_SECONDARY_SAGE,
    COLOR_SECONDARY_TEXT,
    COLOR_SECTION_DIVIDER,
    COLOR_SEPARATOR,
    COLOR_SOFT_BLUE_GREY,
    COLOR_WARM_COPPER,
    FONT_BODY,
    FONT_BULLET,
    FONT_CANDIDATE_NAME,
    FONT_CONTACT,
    FONT_PROJECT_TECH,
    FONT_PROJECT_TITLE,
    FONT_SECTION_HEADING,
    FONT_SERIF_BOLD,
    FONT_SERIF_BOLD_ITALIC,
    FONT_SERIF_ITALIC,
    FONT_SERIF_REGULAR,
    FONT_TARGET_TITLE,
    FONT_TECH_SUBTITLE,
    HEX_BODY_TEXT,
    HEX_DEEP_SLATE_NAVY,
    HEX_FOREST_GREEN,
    HEX_HYPERLINK,
    HEX_LIGHT_DIVIDER,
    HEX_MAIN_GRAPHITE,
    HEX_MUTED_BLUE,
    HEX_PALE_MINT,
    HEX_PRIMARY_NAVY,
    HEX_PRIMARY_TEAL,
    HEX_SECONDARY_TEXT,
    HEX_SOFT_BLUE_GREY,
    HEX_WARM_COPPER,
    LEADING_BODY,
    LEADING_BULLET,
    LEADING_CANDIDATE_NAME,
    LEADING_CONTACT,
    LEADING_PROJECT_TECH,
    LEADING_PROJECT_TITLE,
    LEADING_SECTION_HEADING,
    LEADING_TARGET_TITLE,
    LEADING_TECH_SUBTITLE,
    SECTION_DIVIDER_WIDTH_PT,
    USABLE_WIDTH_PT,
)


class ComponentStyles:
    """Singleton styles repository ensuring typography consistency with Times New Roman serif."""

    def __init__(self):
        styles = getSampleStyleSheet()

        # Centered Header Styles (PART 14)
        self.name_style = ParagraphStyle(
            "HeaderName",
            parent=styles["Normal"],
            fontName=FONT_SERIF_BOLD,
            fontSize=FONT_CANDIDATE_NAME,
            leading=LEADING_CANDIDATE_NAME,
            textColor=COLOR_PRIMARY_NAVY,
            alignment=1,  # Strict rule: Centered
            spaceAfter=1.5,
        )

        self.headline_style = ParagraphStyle(
            "HeaderHeadline",
            parent=styles["Normal"],
            fontName=FONT_SERIF_BOLD,
            fontSize=FONT_TARGET_TITLE,
            leading=LEADING_TARGET_TITLE,
            textColor=COLOR_MUTED_BLUE,
            alignment=1,  # Centered
            spaceAfter=2.0,
        )

        self.contact_style = ParagraphStyle(
            "HeaderContact",
            parent=styles["Normal"],
            fontName=FONT_SERIF_REGULAR,
            fontSize=FONT_CONTACT,
            leading=LEADING_CONTACT,
            textColor=COLOR_SECONDARY_TEXT,
            alignment=1,  # Centered
            spaceAfter=1.5,
        )

        self.links_style = ParagraphStyle(
            "HeaderLinks",
            parent=styles["Normal"],
            fontName=FONT_SERIF_REGULAR,
            fontSize=FONT_CONTACT,
            leading=LEADING_CONTACT,
            textColor=COLOR_SECONDARY_TEXT,
            alignment=1,  # Centered
            spaceAfter=3.0,
        )

        # Section Headings
        self.section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName=FONT_SERIF_BOLD,
            fontSize=FONT_SECTION_HEADING,
            leading=LEADING_SECTION_HEADING,
            textColor=COLOR_PRIMARY_TEAL,
            spaceBefore=0.0,
            spaceAfter=0.0,
        )

        # Body & Metadata (Left-aligned)
        self.body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName=FONT_SERIF_REGULAR,
            fontSize=FONT_BODY,
            leading=LEADING_BODY,
            textColor=COLOR_MAIN_TEXT,
            alignment=0,  # Left-aligned
            spaceAfter=0.5,
        )

        self.project_title_style = ParagraphStyle(
            "ProjectTitle",
            parent=styles["Normal"],
            fontName=FONT_SERIF_BOLD,
            fontSize=FONT_PROJECT_TITLE,
            leading=LEADING_PROJECT_TITLE,
            textColor=COLOR_PRIMARY_NAVY,
            spaceBefore=1.5,
            spaceAfter=0.0,
        )

        self.project_tech_style = ParagraphStyle(
            "ProjectTech",
            parent=styles["Normal"],
            fontName=FONT_SERIF_REGULAR,
            fontSize=FONT_PROJECT_TECH,
            leading=LEADING_PROJECT_TECH,
            textColor=COLOR_PROJECT_TECH,
            spaceAfter=0.5,
        )

        # Hanging Indent Bullet Style
        self.bullet_style = ParagraphStyle(
            "Bullet",
            parent=styles["Normal"],
            fontName=FONT_SERIF_REGULAR,
            fontSize=FONT_BULLET,
            leading=LEADING_BULLET,
            textColor=COLOR_MAIN_TEXT,
            leftIndent=11,
            firstLineIndent=-8,
            spaceAfter=0.5,
        )


def build_resume_header(manifest: ResumeContentManifest, styles: ComponentStyles) -> List[Any]:
    """
    Renders the elegant CENTERED professional header following Part 14:
    SUJAL KADAM (Times-Bold 20 pt, Navy)
    Entry-Level Software Engineer | Full Stack Developer | ML Research Paper Publisher (Times-Bold 10.5 pt, Muted Blue)
    Phone | Email | Location (8.8 pt)
    LinkedIn | GitHub | Portfolio (8.8 pt, clickable)
    Thin Light Divider Rule
    """
    flowables = []
    p_info = manifest.personal_info
    links = manifest.links

    # 1. Candidate Name (Centered)
    flowables.append(Paragraph(escape_xml(p_info.display_name), styles.name_style))

    # 2. Permanent Professional Identity Headline (Strictly constant across all JDs)
    flowables.append(Paragraph(escape_xml(manifest.headline), styles.headline_style))

    # 3. Contact Information Row
    contact_text = (
        f"{escape_xml(p_info.phone)}   |   "
        f'<a href="mailto:{p_info.email}" color="{HEX_HYPERLINK}"><u>{escape_xml(p_info.email)}</u></a>   |   '
        f"{escape_xml(p_info.location)}"
    )
    flowables.append(Paragraph(contact_text, styles.contact_style))

    # 4. Professional Links Row (Visible clean URL & Clickable, Hyperlink Blue #267BF1, underlined)
    links_text = (
        f'<a href="{links.linkedin.url}" color="{HEX_HYPERLINK}"><u>{escape_xml(links.linkedin.display)}</u></a>   |   '
        f'<a href="{links.github.url}" color="{HEX_HYPERLINK}"><u>{escape_xml(links.github.display)}</u></a>   |   '
        f'<a href="{links.portfolio.url}" color="{HEX_HYPERLINK}"><u>{escape_xml(links.portfolio.display)}</u></a>'
    )
    flowables.append(Paragraph(links_text, styles.links_style))

    # 5. Thin Divider Line beneath header
    flowables.append(HRFlowable(
        width="100%",
        thickness=0.6,
        color=COLOR_LIGHT_DIVIDER,
        spaceBefore=1,
        spaceAfter=3,
    ))

    return flowables


def build_section_heading(title: str, styles: ComponentStyles) -> List[Any]:
    """
    Builds a bold uppercase serif section heading with light mint background shading (#E9F0ED),
    a 2.5 pt copper left accent bar (#C47A42), and a 1.3 pt copper divider line directly below.
    """
    heading_p = Paragraph(title.upper(), styles.section_heading_style)
    table = Table([[heading_p]], colWidths=[USABLE_WIDTH_PT])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_PALE_MINT),
        ('LINEBEFORE', (0, 0), (0, 0), 2.5, COLOR_WARM_COPPER),
        ('TOPPADDING', (0, 0), (-1, -1), 0.8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4.0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4.0),
    ]))
    return [
        table,
        HRFlowable(
            width="100%",
            thickness=SECTION_DIVIDER_WIDTH_PT,
            color=COLOR_SECTION_DIVIDER,
            spaceBefore=0.2,
            spaceAfter=0.8,
        ),
    ]


def build_professional_summary(summary_text: str, styles: ComponentStyles) -> List[Any]:
    """Renders the concise 35-50 word professional master summary (left-aligned)."""
    flowables = build_section_heading("PROFESSIONAL SUMMARY", styles)
    flowables.append(Paragraph(escape_xml(summary_text), styles.body_style))
    return flowables


def build_technical_skills(ordered_skills: Dict[str, List[str]], styles: ComponentStyles) -> List[Any]:
    """Renders categorized technical skills across the exact 6 categories in fixed order."""
    flowables = build_section_heading("TECHNICAL SKILLS", styles)
    skill_style = ParagraphStyle(
        "SkillItem",
        parent=styles.body_style,
        fontName=FONT_SERIF_REGULAR,
        fontSize=9.0,
        leading=10.5,
        spaceAfter=0.5,
    )
    for cat_name, skill_items in ordered_skills.items():
        if skill_items:
            line_html = (
                f'<font color="{HEX_DEEP_SLATE_NAVY}"><b>{escape_xml(cat_name)}:</b></font> '
                f'{escape_xml(", ".join(skill_items))}'
            )
            flowables.append(Paragraph(line_html, skill_style))
    return flowables


def build_project_entry(project: ManifestProject, styles: ComponentStyles) -> List[Any]:
    """
    Renders a project entry with:
    - Bold title in Navy with clean GitHub / Paper link
    - Subtitle in Muted Blue Italic
    - 2 concise, evidence-backed bullets with hanging indents
    """
    flowables = []

    # Title line with clickable link (Hyperlink Blue #267BF1, underlined)
    links_html = []
    for l in project.links:
        links_html.append(f'<a href="{l["url"]}" color="{HEX_HYPERLINK}"><u>[{escape_xml(l["label"])}]</u></a>')
    links_str = "  ".join(links_html)

    title_html = f'<font color="{HEX_DEEP_SLATE_NAVY}"><b>{escape_xml(project.title)}</b></font>'
    if links_str:
        title_html += f"   {links_str}"
    flowables.append(Paragraph(title_html, styles.project_title_style))

    # Tech stack subtitle in italic
    if project.subtitle:
        tech_cleaned = project.subtitle.replace(",", " · ")
        flowables.append(Paragraph(escape_xml(tech_cleaned), styles.project_tech_style))

    # Bullets (maximum 2 concise bullets)
    for b in project.bullets[:2]:
        flowables.append(Paragraph(f"•   {escape_xml(b)}", styles.bullet_style))

    return flowables


def build_professional_development(
    development: List[ProfessionalDevelopmentItem],
    styles: ComponentStyles,
) -> List[Any]:
    """Renders the distinct Professional Development & Job Simulations section."""
    if not development:
        return []

    flowables = build_section_heading("PROFESSIONAL DEVELOPMENT & JOB SIMULATIONS", styles)
    for pd in development:
        title_html = (
            f'<font color="{HEX_DEEP_SLATE_NAVY}"><b>{escape_xml(pd.title)}</b></font>   '
            f'<font color="{HEX_SECONDARY_TEXT}">— {escape_xml(pd.date)}</font>'
        )
        flowables.append(Paragraph(title_html, styles.project_title_style))
        for b in pd.bullets[:2]:  # 2 concise bullets covering IAM and presentations
            flowables.append(Paragraph(f"•   {escape_xml(b)}", styles.bullet_style))

    return flowables


def build_education(education: List[EducationItem], styles: ComponentStyles) -> List[Any]:
    """
    Renders the Education section strictly omitting any branch or Mechanical Engineering reference.
    Format:
    B.Tech | KIT's College of Engineering (Autonomous), Kolhapur
    2022–2026 | CGPA: 8.23/10
    """
    flowables = build_section_heading("EDUCATION", styles)
    for edu in education:
        # Strictly ensure no Mechanical Engineering
        degree_clean = edu.degree.replace("in Mechanical Engineering", "").replace("Mechanical Engineering", "").strip()
        if not degree_clean:
            degree_clean = "B.Tech"

        cgpa_str = edu.cgpa if "/" in edu.cgpa else f"{edu.cgpa}/10"

        edu_html = (
            f'<font color="{HEX_DEEP_SLATE_NAVY}"><b>{escape_xml(degree_clean)}</b></font>   |   '
            f'{escape_xml(edu.institution)}   '
            f'<font color="{HEX_SECONDARY_TEXT}">({escape_xml(edu.duration)})</font>   |   '
            f'<b>CGPA: {escape_xml(cgpa_str)}</b>'
        )
        flowables.append(Paragraph(edu_html, styles.body_style))
    return flowables


def build_leadership_and_achievements(
    leadership: List[LeadershipItem],
    achievements: List[AchievementItem],
    styles: ComponentStyles,
) -> List[Any]:
    """Renders the Leadership & Achievements section."""
    flowables = build_section_heading("LEADERSHIP & ACHIEVEMENTS", styles)

    # Chief Student TPO
    for lead in leadership:
        lead_html = (
            f'•   <font color="{HEX_DEEP_SLATE_NAVY}"><b>{escape_xml(lead.role)}</b></font> '
            f'— {escape_xml(lead.organization)}: {escape_xml(lead.description)}'
        )
        flowables.append(Paragraph(lead_html, styles.bullet_style))

    # Best Mega-Project Award & Research Co-Author
    target_phrase = "EPJ Web of Conferences (2026)"
    doi_url = "https://doi.org/10.1051/epjconf/202635501004"
    for ach in achievements:
        desc = escape_xml(ach.description)
        if target_phrase in desc:
            desc = desc.replace(
                target_phrase,
                f'<a href="{doi_url}" color="{HEX_HYPERLINK}"><u>{target_phrase}</u></a>',
            )
        ach_html = (
            f'•   <font color="{HEX_DEEP_SLATE_NAVY}"><b>{escape_xml(ach.title)}:</b></font> '
            f'{desc}'
        )
        flowables.append(Paragraph(ach_html, styles.bullet_style))

    return flowables


def build_certifications(certifications: List[str], styles: ComponentStyles) -> List[Any]:
    """Renders the Certifications section in clean compact format containing all verified credentials."""
    flowables = build_section_heading("CERTIFICATIONS", styles)
    certs_text = "   ·   ".join(escape_xml(c) for c in certifications)
    flowables.append(Paragraph(certs_text, styles.body_style))
    return flowables
