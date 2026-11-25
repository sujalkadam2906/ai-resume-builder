"""Deterministic python-docx Resume Renderer matching Times New Roman PDF layout, page border, and design system."""

from pathlib import Path
from typing import Any, Optional
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from ..content.manifest import ResumeContentManifest
from ..utils.text_cleaner import normalize_url
from .design_system import (
    HEX_BODY_TEXT,
    HEX_DEEP_SLATE_NAVY,
    HEX_LIGHT_DIVIDER,
    HEX_MUTED_BLUE,
    HEX_SECONDARY_TEXT,
    HEX_SOFT_BLUE_GREY,
)

# Editorial Deep Teal & Warm Copper Palette
COLOR_PRIMARY_TEAL = RGBColor(0x17, 0x4A, 0x45)    # Deep Teal #174A45
COLOR_WARM_COPPER = RGBColor(0xC4, 0x7A, 0x42)     # Copper #C47A42
COLOR_MAIN_GRAPHITE = RGBColor(0x26, 0x32, 0x38)   # Graphite #263238
COLOR_SECONDARY_TEXT = RGBColor(0x47, 0x5B, 0x55)  # Secondary #475B55
COLOR_PROJECT_TECH = RGBColor(0x47, 0x5B, 0x55)    # Project Tech Stack #475B55
COLOR_DIVIDER = RGBColor(0xD4, 0xDF, 0xD9)         # Light divider #D4DFD9
COLOR_HYPERLINK = RGBColor(0x26, 0x7B, 0xF1)       # Clickable Hyperlink Blue #267BF1

# Backward-compatible aliases
COLOR_FOREST_GREEN = COLOR_PRIMARY_TEAL
COLOR_SECONDARY_SAGE = COLOR_WARM_COPPER
COLOR_LIGHT_SAGE_GREY = COLOR_DIVIDER
COLOR_BODY_CHARCOAL = COLOR_MAIN_GRAPHITE
COLOR_NAVY = COLOR_PRIMARY_TEAL
COLOR_MUTED = COLOR_WARM_COPPER
COLOR_BODY = COLOR_MAIN_GRAPHITE
COLOR_GRAY = COLOR_SECONDARY_TEXT
COLOR_BORDER = COLOR_PRIMARY_TEAL


def add_hyperlink(paragraph, text: str, url: str, color_rgb: RGBColor = COLOR_HYPERLINK, underline: bool = True):
    """Add a clickable hyperlink to a python-docx paragraph (Hyperlink Blue #267BF1, underlined)."""
    norm_url = normalize_url(url)
    if not norm_url:
        run = paragraph.add_run(text)
        run.font.name = "Times New Roman"
        if color_rgb:
            run.font.color.rgb = color_rgb
        if underline:
            run.font.underline = True
        return run

    part = paragraph.part
    r_id = part.relate_to(norm_url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rPr.append(rFonts)

    if color_rgb:
        c = OxmlElement("w:color")
        c.set(qn("w:val"), f"{color_rgb[0]:02X}{color_rgb[1]:02X}{color_rgb[2]:02X}")
        rPr.append(c)

    if underline:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)

    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def style_section_heading_borders(paragraph, fill_hex: str = "E9F0ED", left_hex: str = "C47A42", bottom_hex: str = "C47A42"):
    """Adds a Pale Mint background shading, a 2 pt copper left accent bar, and a 1.3 pt copper bottom border."""
    pPr = paragraph._p.get_or_add_pPr()

    # Borders: left (sz=16 is 2.0 pt), bottom (sz=10 is 1.25-1.3 pt)
    pBdr = OxmlElement("w:pBdr")

    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "16")
    left.set(qn("w:space"), "4")
    left.set(qn("w:color"), left_hex)
    pBdr.append(left)

    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "10")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), bottom_hex)
    pBdr.append(bottom)

    pPr.append(pBdr)

    # Background Shading: Pale Mint
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    pPr.append(shd)


def set_paragraph_bottom_border(paragraph, color_hex: str = "C47A42", sz: str = "10"):
    """Adds a bottom border rule under a heading paragraph."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), sz)
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_docx_page_border(section, color_hex: str = "174A45", sz: str = "12"):
    """Adds a prominent rectangular outer page border to the DOCX section (Deep Teal #174A45, 1.5 pt)."""
    sectPr = section._sectPr
    pgBorders = OxmlElement("w:pgBorders")
    pgBorders.set(qn("w:offsetFrom"), "page")
    for b_name in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{b_name}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), sz)
        b.set(qn("w:space"), "22")
        b.set(qn("w:color"), color_hex)
        pgBorders.append(b)
    sectPr.append(pgBorders)


def render_docx(manifest: ResumeContentManifest, output_path: Path) -> Path:
    """
    Renders the resume to DOCX format:
    - Times New Roman typography throughout
    - Single-column A4 portrait layout with page border
    - Centered header with permanent headline
    - Strict Section Order: Summary -> Skills -> Projects -> Prof Dev -> Education -> Leadership -> Certs
    - Mechanical Engineering strictly excluded
    - Real clickable hyperlinks
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = docx.Document()

    # Configure A4 page dimensions and margins
    section = doc.sections[0]
    section.top_margin = Inches(0.44)
    section.bottom_margin = Inches(0.44)
    section.left_margin = Inches(0.55)
    section.right_margin = Inches(0.55)
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)

    # Add outer page border (Deep Teal #174A45, 1.5 pt)
    add_docx_page_border(section, color_hex="174A45", sz="12")

    p_info = manifest.personal_info
    links = manifest.links

    # ==========================================================================
    # 1. CENTERED HEADER (Part 14.E)
    # ==========================================================================
    # Candidate Name (20 pt Navy Bold)
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_before = Pt(0)
    p_name.paragraph_format.space_after = Pt(1)
    r_name = p_name.add_run(p_info.display_name)
    r_name.font.name = "Times New Roman"
    r_name.font.size = Pt(20)
    r_name.font.bold = True
    r_name.font.color.rgb = COLOR_NAVY

    # Permanent Professional Identity Headline (10.5 pt Muted Blue Bold)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    r_title = p_title.add_run(manifest.headline)
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(10.5)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_MUTED

    # Contact Details Line (8.8 pt)
    p_con = doc.add_paragraph()
    p_con.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_con.paragraph_format.space_before = Pt(0)
    p_con.paragraph_format.space_after = Pt(1)
    r_phone = p_con.add_run(f"{p_info.phone}   |   ")
    r_phone.font.name = "Times New Roman"
    r_phone.font.size = Pt(8.8)
    r_phone.font.color.rgb = COLOR_GRAY

    add_hyperlink(p_con, p_info.email, f"mailto:{p_info.email}", color_rgb=COLOR_HYPERLINK)

    r_loc = p_con.add_run(f"   |   {p_info.location}")
    r_loc.font.name = "Times New Roman"
    r_loc.font.size = Pt(8.8)
    r_loc.font.color.rgb = COLOR_GRAY

    # Professional Links Line (8.8 pt with real hyperlinks)
    p_links = doc.add_paragraph()
    p_links.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_links.paragraph_format.space_before = Pt(0)
    p_links.paragraph_format.space_after = Pt(3)

    def _get_link_field(item: Any, field: str, default: str = "") -> str:
        if isinstance(item, dict):
            return item.get(field, default) or default
        return getattr(item, field, default) or default

    li_item = getattr(links, "linkedin", None) if hasattr(links, "linkedin") else (links.get("linkedin") if isinstance(links, dict) else None)
    gh_item = getattr(links, "github", None) if hasattr(links, "github") else (links.get("github") if isinstance(links, dict) else None)
    pf_item = getattr(links, "portfolio", None) if hasattr(links, "portfolio") else (links.get("portfolio") if isinstance(links, dict) else None)

    li_url = normalize_url(_get_link_field(li_item, "url"), default_domain="linkedin.com/in", fallback=_get_link_field(li_item, "display"))
    li_disp = _get_link_field(li_item, "display", "linkedin.com/in/profile")

    gh_url = normalize_url(_get_link_field(gh_item, "url"), default_domain="github.com", fallback=_get_link_field(gh_item, "display"))
    gh_disp = _get_link_field(gh_item, "display", "github.com/profile")

    pf_url = normalize_url(_get_link_field(pf_item, "url"), fallback=_get_link_field(pf_item, "display"))
    pf_disp = _get_link_field(pf_item, "display", "portfolio.dev")

    add_hyperlink(p_links, li_disp, li_url, color_rgb=COLOR_HYPERLINK)
    r_sep1 = p_links.add_run("   |   ")
    r_sep1.font.name = "Times New Roman"
    r_sep1.font.size = Pt(8.8)
    r_sep1.font.color.rgb = COLOR_GRAY

    add_hyperlink(p_links, gh_disp, gh_url, color_rgb=COLOR_HYPERLINK)
    r_sep2 = p_links.add_run("   |   ")
    r_sep2.font.name = "Times New Roman"
    r_sep2.font.size = Pt(8.8)
    r_sep2.font.color.rgb = COLOR_GRAY

    add_hyperlink(p_links, pf_disp, pf_url, color_rgb=COLOR_HYPERLINK)

    # Accent bottom rule under header (Light Divider #D4DFD9)
    set_paragraph_bottom_border(p_links, color_hex="D4DFD9", sz="4")

    # Helper function for adding standard section headings with Pale Mint fill & Copper left/bottom borders
    def add_section_heading(title: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(title.upper())
        r.font.name = "Times New Roman"
        r.font.size = Pt(10.5)
        r.font.bold = True
        r.font.color.rgb = COLOR_NAVY
        style_section_heading_borders(p, fill_hex="E9F0ED", left_hex="C47A42", bottom_hex="C47A42")
        return p

    # ==========================================================================
    # 2. PROFESSIONAL SUMMARY (Left-aligned, 2-4 lines)
    # ==========================================================================
    add_section_heading("PROFESSIONAL SUMMARY")
    p_sum = doc.add_paragraph()
    p_sum.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_sum.paragraph_format.space_before = Pt(1)
    p_sum.paragraph_format.space_after = Pt(2)
    r_sum = p_sum.add_run(manifest.summary)
    r_sum.font.name = "Times New Roman"
    r_sum.font.size = Pt(9.6)
    r_sum.font.color.rgb = COLOR_BODY

    # ==========================================================================
    # 3. TECHNICAL SKILLS (Exact 6 categories in fixed order)
    # ==========================================================================
    add_section_heading("TECHNICAL SKILLS")
    for cat_name, skill_items in manifest.ordered_skills.items():
        if skill_items:
            p_sk = doc.add_paragraph()
            p_sk.paragraph_format.space_before = Pt(0)
            p_sk.paragraph_format.space_after = Pt(1)
            r_c = p_sk.add_run(f"{cat_name}: ")
            r_c.font.name = "Times New Roman"
            r_c.font.size = Pt(9.0)
            r_c.font.bold = True
            r_c.font.color.rgb = COLOR_NAVY

            r_s = p_sk.add_run(", ".join(skill_items))
            r_s.font.name = "Times New Roman"
            r_s.font.size = Pt(9.0)
            r_s.font.color.rgb = COLOR_BODY

    # ==========================================================================
    # 4. PROJECTS (4 projects, Bearing Fault strictly at position 2)
    # ==========================================================================
    add_section_heading("PROJECTS")
    for proj in manifest.projects:
        p_pj = doc.add_paragraph()
        p_pj.paragraph_format.space_before = Pt(2)
        p_pj.paragraph_format.space_after = Pt(0)

        # Title
        r_pt = p_pj.add_run(proj.title)
        r_pt.font.name = "Times New Roman"
        r_pt.font.size = Pt(10.0)
        r_pt.font.bold = True
        r_pt.font.color.rgb = COLOR_NAVY

        # Hyperlinks (Live Demo | GitHub)
        valid_links = []
        for l in (proj.links or []):
            l_url = l.get("url") if isinstance(l, dict) else getattr(l, "url", "")
            l_label = l.get("label") if isinstance(l, dict) else getattr(l, "label", "")
            norm_url = normalize_url(l_url)
            if norm_url:
                clean_lbl = (l_label or "").strip("[] ").strip()
                low = clean_lbl.lower()
                if low in ("demo", "live", "live demo", "website", "app"):
                    clean_lbl = "Live Demo"
                elif low in ("github", "code", "repo", "repository"):
                    clean_lbl = "GitHub"
                elif not clean_lbl:
                    clean_lbl = "Link"
                valid_links.append((clean_lbl, norm_url))

        if valid_links:
            p_pj.add_run("   ")
            for idx, (lbl, url) in enumerate(valid_links):
                if idx > 0:
                    r_sep = p_pj.add_run(" | ")
                    r_sep.font.name = "Times New Roman"
                    r_sep.font.size = Pt(9.5)
                    r_sep.font.color.rgb = COLOR_BODY
                add_hyperlink(p_pj, lbl, url, color_rgb=COLOR_HYPERLINK, underline=True)

        # Subtitle / tech stack
        if proj.subtitle:
            p_st = doc.add_paragraph()
            p_st.paragraph_format.space_before = Pt(0)
            p_st.paragraph_format.space_after = Pt(0)
            r_ps = p_st.add_run(proj.subtitle.replace(",", " · "))
            r_ps.font.name = "Times New Roman"
            r_ps.font.size = Pt(9.2)
            r_ps.font.italic = False
            r_ps.font.color.rgb = COLOR_PROJECT_TECH

        # Bullets (maximum 2 concise bullets)
        for b in proj.bullets[:2]:
            p_b = doc.add_paragraph(style="List Bullet")
            p_b.paragraph_format.space_before = Pt(0)
            p_b.paragraph_format.space_after = Pt(0.5)
            r_b = p_b.add_run(b)
            r_b.font.name = "Times New Roman"
            r_b.font.size = Pt(9.6)
            r_b.font.color.rgb = COLOR_BODY

    # ==========================================================================
    # 5. PROFESSIONAL DEVELOPMENT & JOB SIMULATIONS (Part 9 & 10)
    # ==========================================================================
    if manifest.professional_development:
        add_section_heading("PROFESSIONAL DEVELOPMENT & JOB SIMULATIONS")
        for pd in manifest.professional_development:
            p_pd = doc.add_paragraph()
            p_pd.paragraph_format.space_before = Pt(1.5)
            p_pd.paragraph_format.space_after = Pt(0)
            r_pdt = p_pd.add_run(pd.title)
            r_pdt.font.name = "Times New Roman"
            r_pdt.font.size = Pt(9.8)
            r_pdt.font.bold = True
            r_pdt.font.color.rgb = COLOR_NAVY

            r_pdd = p_pd.add_run(f" — {pd.date}")
            r_pdd.font.name = "Times New Roman"
            r_pdd.font.size = Pt(8.8)
            r_pdd.font.italic = True
            r_pdd.font.color.rgb = COLOR_GRAY

            for b in pd.bullets[:2]:
                p_pdb = doc.add_paragraph(style="List Bullet")
                p_pdb.paragraph_format.space_before = Pt(0)
                p_pdb.paragraph_format.space_after = Pt(0.5)
                r_b = p_pdb.add_run(b)
                r_b.font.name = "Times New Roman"
                r_b.font.size = Pt(9.6)
                r_b.font.color.rgb = COLOR_BODY

    # ==========================================================================
    # 6. EDUCATION (Part 9 & 11) - STRICTLY NO MECHANICAL ENGINEERING
    # ==========================================================================
    add_section_heading("EDUCATION")
    for edu in manifest.education:
        p_e = doc.add_paragraph()
        p_e.paragraph_format.space_before = Pt(1)
        p_e.paragraph_format.space_after = Pt(1)
        degree_clean = edu.degree.replace("in Mechanical Engineering", "").replace("Mechanical Engineering", "").strip()
        if not degree_clean:
            degree_clean = "B.Tech"

        cgpa_str = edu.cgpa if "/" in edu.cgpa else f"{edu.cgpa}/10"

        r_deg = p_e.add_run(f"{degree_clean} | ")
        r_deg.font.name = "Times New Roman"
        r_deg.font.size = Pt(9.6)
        r_deg.font.bold = True
        r_deg.font.color.rgb = COLOR_NAVY

        r_inst = p_e.add_run(f"{edu.institution} ({edu.duration})   |   ")
        r_inst.font.name = "Times New Roman"
        r_inst.font.size = Pt(9.6)
        r_inst.font.color.rgb = COLOR_BODY

        r_cgpa = p_e.add_run(f"CGPA: {cgpa_str}")
        r_cgpa.font.name = "Times New Roman"
        r_cgpa.font.size = Pt(9.6)
        r_cgpa.font.bold = True
        r_cgpa.font.color.rgb = COLOR_BODY

    # ==========================================================================
    # 7. LEADERSHIP & ACHIEVEMENTS (Part 9 & 12)
    # ==========================================================================
    add_section_heading("LEADERSHIP & ACHIEVEMENTS")
    for lead in manifest.leadership:
        p_l = doc.add_paragraph(style="List Bullet")
        p_l.paragraph_format.space_before = Pt(0)
        p_l.paragraph_format.space_after = Pt(0.5)
        r_lt = p_l.add_run(f"{lead.role} — {lead.organization}: ")
        r_lt.font.name = "Times New Roman"
        r_lt.font.size = Pt(9.6)
        r_lt.font.bold = True
        r_lt.font.color.rgb = COLOR_NAVY
        r_ld = p_l.add_run(lead.description)
        r_ld.font.name = "Times New Roman"
        r_ld.font.size = Pt(9.6)
        r_ld.font.color.rgb = COLOR_BODY

    target_phrase = "EPJ Web of Conferences (2026)"
    doi_url = "https://doi.org/10.1051/epjconf/202635501004"

    for ach in manifest.achievements:
        p_a = doc.add_paragraph(style="List Bullet")
        p_a.paragraph_format.space_before = Pt(0)
        p_a.paragraph_format.space_after = Pt(0.5)
        r_at = p_a.add_run(f"{ach.title}: ")
        r_at.font.name = "Times New Roman"
        r_at.font.size = Pt(9.6)
        r_at.font.bold = True
        r_at.font.color.rgb = COLOR_NAVY

        if target_phrase in ach.description:
            parts = ach.description.split(target_phrase)
            r_before = p_a.add_run(parts[0])
            r_before.font.name = "Times New Roman"
            r_before.font.size = Pt(9.6)
            r_before.font.color.rgb = COLOR_BODY

            add_hyperlink(p_a, target_phrase, doi_url, color_rgb=COLOR_HYPERLINK, underline=True)

            if len(parts) > 1:
                r_after = p_a.add_run(parts[1])
                r_after.font.name = "Times New Roman"
                r_after.font.size = Pt(9.6)
                r_after.font.color.rgb = COLOR_BODY
        else:
            r_ad = p_a.add_run(ach.description)
            r_ad.font.name = "Times New Roman"
            r_ad.font.size = Pt(9.6)
            r_ad.font.color.rgb = COLOR_BODY

    # ==========================================================================
    # 8. CERTIFICATIONS (Part 9 & 13)
    # ==========================================================================
    if manifest.certifications:
        add_section_heading("CERTIFICATIONS")
        p_cert = doc.add_paragraph()
        p_cert.paragraph_format.space_before = Pt(1)
        p_cert.paragraph_format.space_after = Pt(1)
        r_c = p_cert.add_run(" · ".join(manifest.certifications))
        r_c.font.name = "Times New Roman"
        r_c.font.size = Pt(9.6)
        r_c.font.color.rgb = COLOR_BODY

    doc.save(str(output_path))
    return output_path
