"""
Generates publication-grade, styled PDF documentation for AI Resume Builder:
1. docs/pdf/01_TECH_STACK_INTERVIEW_GUIDE.pdf
2. docs/pdf/02_SYSTEM_ARCHITECTURE_AND_WORKFLOW.pdf
3. docs/pdf/03_INTERVIEW_PREPARATION.pdf

Follows the Editorial Deep Teal & Warm Copper design system with running headers,
page numbering (Page X of Y), selectable text, and clean typography.
"""

from pathlib import Path
import re
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Colors
COLOR_TEAL = colors.HexColor("#174A45")
COLOR_COPPER = colors.HexColor("#C47A42")
COLOR_GRAPHITE = colors.HexColor("#263238")
COLOR_MUTED = colors.HexColor("#475B55")
COLOR_PALE_MINT = colors.HexColor("#E9F0ED")
COLOR_LIGHT_DIVIDER = colors.HexColor("#D4DFD9")
COLOR_HYPERLINK = colors.HexColor("#267BF1")
COLOR_BG_CODE = colors.HexColor("#F4F6F5")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw 'Page X of Y' and running headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        width, height = A4

        # Do not draw running header on cover/first page
        if self._pageNumber > 1:
            # Header rule & title
            self.setFont("Times-Roman", 8.5)
            self.setFillColor(COLOR_MUTED)
            self.drawString(36, height - 26, getattr(self, "doc_title", "AI Resume Builder — Documentation"))
            self.drawRightString(width - 36, height - 26, "Architecture & Engineering Manual")
            self.setStrokeColor(COLOR_LIGHT_DIVIDER)
            self.setLineWidth(0.6)
            self.line(36, height - 30, width - 36, height - 30)

        # Footer (drawn on all pages)
        self.setStrokeColor(COLOR_LIGHT_DIVIDER)
        self.setLineWidth(0.6)
        self.line(36, 32, width - 36, 32)

        self.setFont("Times-Roman", 8.5)
        self.setFillColor(COLOR_MUTED)
        self.drawString(36, 20, "AI Resume Builder — High-Assurance Portfolio Project")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - 36, 20, page_str)

        self.restoreState()


def get_doc_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=20,
        leading=24,
        textColor=COLOR_TEAL,
        alignment=0,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=11,
        leading=15,
        textColor=COLOR_COPPER,
        alignment=0,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=14,
        leading=17,
        textColor=COLOR_TEAL,
        spaceBefore=14,
        spaceAfter=4,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=11.5,
        leading=14.5,
        textColor=COLOR_COPPER,
        spaceBefore=10,
        spaceAfter=3,
        keepWithNext=True,
    )

    h3_style = ParagraphStyle(
        "Heading3_Custom",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        textColor=COLOR_TEAL,
        spaceBefore=7,
        spaceAfter=2,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9.5,
        leading=13,
        textColor=COLOR_GRAPHITE,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9.5,
        leading=13,
        textColor=COLOR_GRAPHITE,
        leftIndent=14,
        firstLineIndent=-9,
        spaceAfter=2.5,
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10.5,
        textColor=COLOR_GRAPHITE,
        backColor=COLOR_BG_CODE,
        borderPadding=4,
        spaceBefore=4,
        spaceAfter=4,
    )

    callout_style = ParagraphStyle(
        "Callout_Custom",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        leading=12.5,
        textColor=COLOR_GRAPHITE,
        leftIndent=8,
        rightIndent=8,
        spaceAfter=4,
    )

    table_cell_style = ParagraphStyle(
        "TableCell_Custom",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_GRAPHITE,
    )

    table_header_style = ParagraphStyle(
        "TableHeader_Custom",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "h1": h1_style,
        "h2": h2_style,
        "h3": h3_style,
        "body": body_style,
        "bullet": bullet_style,
        "code": code_style,
        "callout": callout_style,
        "table_cell": table_cell_style,
        "table_header": table_header_style,
    }


def clean_markdown_inline(text: str) -> str:
    """Escapes XML and translates markdown bold, italic, code, and links to ReportLab markup."""
    # First escape bare &
    text = text.replace("&", "&amp;")
    # Escape < and > if not tags
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    # Re-enable ReportLab supported formatting
    # Bold **text** -> <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic *text* -> <i>text</i>
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Inline code `text` -> <font face="Courier" color="#174A45">\1</font>
    text = re.sub(r"`(.+?)`", r'<font face="Courier" color="#174A45">\1</font>', text)
    # Hyperlinks [text](url) -> <a href="url" color="#267BF1"><u>text</u></a>
    text = re.sub(
        r"\[(.+?)\]\((.+?)\)",
        r'<a href="\2" color="#267BF1"><u>\1</u></a>',
        text,
    )

    return text


def parse_markdown_to_flowables(md_content: str, styles: dict) -> List:
    flowables = []
    lines = md_content.splitlines()
    i = 0
    n = len(lines)

    in_code_block = False
    code_lines = []

    while i < n:
        line = lines[i]

        # Handle fenced code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                # End of code block
                code_text = "<br/>".join(code_lines)
                flowables.append(Paragraph(code_text, styles["code"]))
                in_code_block = False
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(clean_markdown_inline(line))
            i += 1
            continue

        line_str = line.strip()

        if not line_str:
            i += 1
            continue

        # Horizontal Rule
        if line_str in ("---", "***", "___"):
            flowables.append(
                HRFlowable(width="100%", thickness=0.8, color=COLOR_LIGHT_DIVIDER, spaceBefore=4, spaceAfter=6)
            )
            i += 1
            continue

        # Markdown Table Detection
        if line_str.startswith("|") and line_str.endswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 2:
                # Parse markdown table
                header_raw = [c.strip() for c in table_lines[0].split("|")[1:-1]]
                data_rows = []
                for row_line in table_lines[2:]:  # skip separator row
                    row_cells = [c.strip() for c in row_line.split("|")[1:-1]]
                    data_rows.append(row_cells)

                if header_raw and data_rows:
                    table_data = []
                    # Header
                    h_row = [Paragraph(clean_markdown_inline(c), styles["table_header"]) for c in header_raw]
                    table_data.append(h_row)

                    for r in data_rows:
                        # Pad or trim to header length
                        cells = []
                        for col_idx in range(len(header_raw)):
                            cell_val = r[col_idx] if col_idx < len(r) else ""
                            cells.append(Paragraph(clean_markdown_inline(cell_val), styles["table_cell"]))
                        table_data.append(cells)

                    # Total usable width = 523.27 pt
                    num_cols = len(header_raw)
                    col_width = 523.27 / num_cols if num_cols > 0 else 100
                    # For unequal columns, adjust if 4 or 5 cols
                    col_widths = [col_width] * num_cols

                    t = Table(table_data, colWidths=col_widths, repeatRows=1)
                    t.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("TOPPADDING", (0, 0), (-1, -1), 3),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LIGHT_DIVIDER),
                                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG_CODE]),
                            ]
                        )
                    )
                    flowables.append(Spacer(1, 4))
                    flowables.append(t)
                    flowables.append(Spacer(1, 4))
            continue

        # Headers
        if line_str.startswith("# "):
            title_text = clean_markdown_inline(line_str[2:].strip())
            flowables.append(Paragraph(title_text, styles["title"]))
            flowables.append(
                HRFlowable(width="100%", thickness=1.5, color=COLOR_COPPER, spaceBefore=2, spaceAfter=8)
            )
            i += 1
            continue

        if line_str.startswith("## "):
            h1_text = clean_markdown_inline(line_str[3:].strip())
            # Heading banner with left copper accent
            p = Paragraph(h1_text.upper(), styles["h1"])
            banner_table = Table([[p]], colWidths=[523.27])
            banner_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), COLOR_PALE_MINT),
                        ("LINEBEFORE", (0, 0), (0, 0), 3.0, COLOR_COPPER),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            flowables.append(Spacer(1, 6))
            flowables.append(banner_table)
            flowables.append(
                HRFlowable(width="100%", thickness=1.0, color=COLOR_COPPER, spaceBefore=1, spaceAfter=4)
            )
            i += 1
            continue

        if line_str.startswith("### "):
            h2_text = clean_markdown_inline(line_str[4:].strip())
            flowables.append(Paragraph(h2_text, styles["h2"]))
            i += 1
            continue

        if line_str.startswith("#### "):
            h3_text = clean_markdown_inline(line_str[5:].strip())
            flowables.append(Paragraph(h3_text, styles["h3"]))
            i += 1
            continue

        # Blockquote / Alert Callouts
        if line_str.startswith(">"):
            callout_text = clean_markdown_inline(line_str.lstrip(">").strip())
            cp = Paragraph(callout_text, styles["callout"])
            box = Table([[cp]], colWidths=[523.27])
            box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), COLOR_PALE_MINT),
                        ("LINEBEFORE", (0, 0), (0, 0), 2.5, COLOR_TEAL),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            flowables.append(box)
            flowables.append(Spacer(1, 3))
            i += 1
            continue

        # Bullet List Items
        if line_str.startswith(("- ", "* ", "+ ")):
            bullet_text = clean_markdown_inline(line_str[2:].strip())
            flowables.append(Paragraph(f"• &nbsp; {bullet_text}", styles["bullet"]))
            i += 1
            continue

        # Numbered List Items
        num_match = re.match(r"^(\d+)\.\s+(.*)", line_str)
        if num_match:
            idx_num = num_match.group(1)
            item_text = clean_markdown_inline(num_match.group(2).strip())
            flowables.append(Paragraph(f"<b>{idx_num}.</b> &nbsp; {item_text}", styles["bullet"]))
            i += 1
            continue

        # Regular Paragraph
        p_text = clean_markdown_inline(line_str)
        flowables.append(Paragraph(p_text, styles["body"]))
        i += 1

    return flowables


def build_pdf_from_markdown(md_path: Path, output_pdf_path: Path, doc_title: str):
    """Parses markdown file and compiles a high-assurance publication PDF."""
    print(f"Compiling: {md_path.name} -> {output_pdf_path.name}...")
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    md_content = md_path.read_text(encoding="utf-8")
    styles = get_doc_styles()
    flowables = parse_markdown_to_flowables(md_content, styles)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    # Attach document title to custom canvas
    def make_canvas(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.doc_title = doc_title
        return c

    doc.build(flowables, canvasmaker=make_canvas)
    print(f"  [SUCCESS] Created {output_pdf_path.name} (File size: {output_pdf_path.stat().st_size} bytes)")


def main():
    docs_dir = Path("docs")
    pdf_dir = docs_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    targets = [
        (
            docs_dir / "01_TECH_STACK_INTERVIEW_GUIDE.md",
            pdf_dir / "01_TECH_STACK_INTERVIEW_GUIDE.pdf",
            "AI Resume Builder — Technology Stack Interview Guide",
        ),
        (
            docs_dir / "02_SYSTEM_ARCHITECTURE_AND_WORKFLOW.md",
            pdf_dir / "02_SYSTEM_ARCHITECTURE_AND_WORKFLOW.pdf",
            "AI Resume Builder — System Architecture & Complete Workflow",
        ),
        (
            docs_dir / "03_INTERVIEW_PREPARATION.md",
            pdf_dir / "03_INTERVIEW_PREPARATION.pdf",
            "AI Resume Builder — Technical Interview Preparation & Defense",
        ),
    ]

    for md_file, pdf_file, title in targets:
        if md_file.exists():
            build_pdf_from_markdown(md_file, pdf_file, title)
        else:
            print(f"  [ERROR] Source markdown missing: {md_file}")


if __name__ == "__main__":
    main()
