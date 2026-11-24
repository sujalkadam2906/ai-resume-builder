"""Publication-grade Markdown to PDF Compiler using ReportLab.

Transforms Markdown documentation into styled, professional A4 PDFs:
- Two-pass NumberedCanvas for 'Page X of Y' and dynamic running headers
- Editorial Teal & Copper typography palette
- Structured headings, tables, code blocks, callouts, and bullet lists
- Clean XML escaping to prevent ReportLab markup parsing crashes
"""

import html
from pathlib import Path
import re
import sys
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Design System Palette
COLOR_TEAL = colors.HexColor("#174A45")
COLOR_COPPER = colors.HexColor("#C47A42")
COLOR_GRAPHITE = colors.HexColor("#263238")
COLOR_MUTED = colors.HexColor("#475B55")
COLOR_PALE_MINT = colors.HexColor("#E9F0ED")
COLOR_LIGHT_DIVIDER = colors.HexColor("#D4DFD9")
COLOR_BG_CODE = colors.HexColor("#F4F6F5")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for total page count calculation and professional headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.doc_title = getattr(self, "doc_title", "AI Resume Builder Documentation")

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages: int):
        self.saveState()
        width, height = A4

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.setFont("Times-Roman", 8.5)
            self.setFillColor(COLOR_MUTED)
            self.drawString(36, height - 26, str(self.doc_title)[:60])
            self.drawRightString(width - 36, height - 26, "AI Resume Builder Platform")
            self.setStrokeColor(COLOR_LIGHT_DIVIDER)
            self.setLineWidth(0.6)
            self.line(36, height - 30, width - 36, height - 30)

        # Running footer
        self.setStrokeColor(COLOR_LIGHT_DIVIDER)
        self.setLineWidth(0.6)
        self.line(36, 32, width - 36, 32)

        self.setFont("Times-Roman", 8.5)
        self.setFillColor(COLOR_MUTED)
        self.drawString(36, 20, "Confidential & Proprietary — Engineering Documentation")
        self.drawRightString(width - 36, 20, f"Page {self._pageNumber} of {total_pages}")

        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "DocTitle",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=18,
            leading=22,
            textColor=COLOR_TEAL,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=14,
            textColor=COLOR_COPPER,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "Heading1_Custom",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=13,
            leading=16,
            textColor=COLOR_TEAL,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Heading2_Custom",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=11,
            leading=14,
            textColor=COLOR_COPPER,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Heading3_Custom",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=9.5,
            leading=12.5,
            textColor=COLOR_GRAPHITE,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body_Custom",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=8.5,
            leading=11.5,
            textColor=COLOR_GRAPHITE,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet_Custom",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=8.5,
            leading=11.5,
            textColor=COLOR_GRAPHITE,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "Code_Custom",
            parent=base["Normal"],
            fontName="Courier",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_GRAPHITE,
            backColor=COLOR_BG_CODE,
            borderPadding=4,
            spaceAfter=4,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_GRAPHITE,
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        ),
    }


def parse_markdown_to_flowables(md_text: str, styles: dict) -> List[any]:
    """Parse common Markdown constructs into styled ReportLab Flowables."""
    flowables = []
    lines = md_text.splitlines()
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            in_table = False
            return

        col_count = max(len(r) for r in table_rows)
        # Normalize rows
        processed_rows = []
        for i, row in enumerate(table_rows):
            # Pad short rows
            row_padded = row + [""] * (col_count - len(row))
            cell_paragraphs = []
            for cell in row_padded:
                cell_style = styles["table_head"] if i == 0 else styles["table_cell"]
                cell_text = html.escape(cell.strip())
                # Handle bold inside cell
                cell_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", cell_text)
                cell_text = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", cell_text)
                cell_paragraphs.append(Paragraph(cell_text, cell_style))
            processed_rows.append(cell_paragraphs)

        # Standard column widths for A4
        available_width = 523.0  # 595 - 2*36
        col_width = available_width / col_count

        t = Table(processed_rows, colWidths=[col_width] * col_count)
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LIGHT_DIVIDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_PALE_MINT]),
            ])
        )
        flowables.append(t)
        flowables.append(Spacer(1, 6))
        table_rows = []
        in_table = False

    def sanitize_inline(text: str) -> str:
        esc = html.escape(text)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc)
        esc = re.sub(r"\*(.+?)\*", r"<i>\1</i>", esc)
        esc = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", esc)
        esc = re.sub(r"\[(.+?)\]\((.+?)\)", r'<font color="#267BF1"><u>\1</u></font>', esc)
        return esc

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # 1. Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_text = html.escape("\n".join(code_lines))
                flowables.append(Preformatted(code_text, styles["code"]))
                code_lines = []
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_lines = []
            idx += 1
            continue

        if in_code_block:
            code_lines.append(line)
            idx += 1
            continue

        # 2. Markdown Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            # Check if separator row e.g. |:---|:---|
            if re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", stripped):
                idx += 1
                continue
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            table_rows.append(cells)
            idx += 1
            continue
        elif in_table:
            flush_table()

        # 3. Blank lines
        if not stripped:
            idx += 1
            continue

        # 4. Horizontal Rule
        if re.match(r"^(?:---|\*\*\*|___)$", stripped):
            flowables.append(HRFlowable(width="100%", thickness=0.8, color=COLOR_LIGHT_DIVIDER, spaceBefore=4, spaceAfter=6))
            idx += 1
            continue

        # 5. Headings
        if stripped.startswith("# "):
            title_text = sanitize_inline(stripped[2:].strip())
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph(title_text, styles["title"]))
            flowables.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_TEAL, spaceBefore=2, spaceAfter=8))
            idx += 1
            continue
        elif stripped.startswith("## "):
            h1_text = sanitize_inline(stripped[3:].strip())
            flowables.append(Paragraph(h1_text, styles["h1"]))
            idx += 1
            continue
        elif stripped.startswith("### "):
            h2_text = sanitize_inline(stripped[4:].strip())
            flowables.append(Paragraph(h2_text, styles["h2"]))
            idx += 1
            continue
        elif stripped.startswith("#### "):
            h3_text = sanitize_inline(stripped[5:].strip())
            flowables.append(Paragraph(h3_text, styles["h3"]))
            idx += 1
            continue

        # 6. Bullet lists
        if re.match(r"^[-*]\s+", stripped):
            bullet_text = "&bull; " + sanitize_inline(re.sub(r"^[-*]\s+", "", stripped))
            flowables.append(Paragraph(bullet_text, styles["bullet"]))
            idx += 1
            continue
        if re.match(r"^\d+\.\s+", stripped):
            num_match = re.match(r"^(\d+\.)\s+(.+)$", stripped)
            if num_match:
                bullet_text = f"<b>{num_match.group(1)}</b> {sanitize_inline(num_match.group(2))}"
                flowables.append(Paragraph(bullet_text, styles["bullet"]))
                idx += 1
                continue

        # 7. Blockquote / Callout
        if stripped.startswith(">"):
            quote_text = sanitize_inline(stripped.lstrip("> ").strip())
            flowables.append(Paragraph(f"<i>{quote_text}</i>", styles["body"]))
            idx += 1
            continue

        # 8. Standard paragraph
        p_text = sanitize_inline(stripped)
        flowables.append(Paragraph(p_text, styles["body"]))
        idx += 1

    if in_table:
        flush_table()
    if in_code_block and code_lines:
        flowables.append(Preformatted(html.escape("\n".join(code_lines)), styles["code"]))

    return flowables


def compile_md_to_pdf(md_path: Path, output_pdf_path: Path, doc_title: str) -> Path:
    """Compile a Markdown file into a styled ReportLab PDF."""
    print(f"[COMPILING] {md_path.name} -> {output_pdf_path.name}")
    md_text = md_path.read_text(encoding="utf-8", errors="ignore")
    styles = get_styles()

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    flowables = parse_markdown_to_flowables(md_text, styles)

    # Attach doc title to canvas class dynamically
    class CustomCanvas(NumberedCanvas):
        pass
    CustomCanvas.doc_title = doc_title

    doc.build(flowables, canvasmaker=CustomCanvas)

    size = output_pdf_path.stat().st_size
    print(f"[SUCCESS] Generated {output_pdf_path.name}: {size:,} bytes")
    return output_pdf_path


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        src = Path(sys.argv[1])
        dest = Path(sys.argv[2])
        title = sys.argv[3] if len(sys.argv) > 3 else src.stem
        compile_md_to_pdf(src, dest, title)
    else:
        print("Usage: python compile_markdown_to_pdf.py <input.md> <output.pdf> [title]")
