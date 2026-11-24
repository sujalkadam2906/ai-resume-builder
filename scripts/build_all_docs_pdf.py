"""Batch documentation PDF generator using ReportLab."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.compile_markdown_to_pdf import compile_md_to_pdf
DOCS_DIR = PROJECT_ROOT / "docs"
PDF_DIR = DOCS_DIR / "pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)

DOCUMENTS = [
    ("PROJECT_ARCHITECTURE.md", "01_PROJECT_ARCHITECTURE.pdf", "Project Architecture & System Design"),
    ("SETUP_AND_INSTALLATION.md", "02_SETUP_AND_INSTALLATION.pdf", "Setup and Installation Guide"),
    ("API_DOCUMENTATION.md", "03_API_DOCUMENTATION.pdf", "REST API Reference Manual"),
    ("USER_GUIDE.md", "04_USER_GUIDE.pdf", "End-User Workflow & Operations Manual"),
    ("SECURITY_AND_DEPLOYMENT.md", "05_SECURITY_AND_DEPLOYMENT.pdf", "Security Architecture & Production Deployment"),
    ("TESTING_GUIDE.md", "06_TESTING_GUIDE.pdf", "Quality Assurance & Testing Manual"),
    ("PROJECT_STATUS.md", "07_FINAL_TECHNICAL_DOCUMENTATION.pdf", "Project Status & Milestone Ledger"),
]


def build_all():
    print(f"=== BATCH COMPILING {len(DOCUMENTS)} DOCUMENTATION PDFS ===")
    results = []
    for md_name, pdf_name, title in DOCUMENTS:
        md_path = DOCS_DIR / md_name
        pdf_path = PDF_DIR / pdf_name
        if not md_path.exists():
            print(f"[ERROR] Source Markdown missing: {md_path}")
            continue
        try:
            out_pdf = compile_md_to_pdf(md_path, pdf_path, title)
            results.append((pdf_name, out_pdf.stat().st_size))
        except Exception as exc:
            print(f"[FAIL] Error compiling {md_name}: {exc}")
            raise

    print("\n=== COMPILATION COMPLETE ===")
    for name, size in results:
        print(f"  ✓ {name}: {size:,} bytes")


if __name__ == "__main__":
    build_all()
