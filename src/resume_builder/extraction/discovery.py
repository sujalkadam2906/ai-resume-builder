"""Discovery of original resume files case-insensitively across directories."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def find_resume_files(search_dir: Path) -> Dict[str, Optional[Path]]:
    """
    Search directory and subdirectories for original resume files:
    - Sujal_Kadam_Resume
    - Sujal_Kadam_Resume_new
    Returns a dict with keys 'r1' and 'r2'.
    """
    results: Dict[str, Optional[Path]] = {"r1": None, "r2": None}

    # Priority folders to check: search_dir itself, 'Current Resumes', 'resumes', 'data'
    candidate_paths: List[Path] = []
    for root, _, files in os.walk(search_dir):
        # Skip output, logs, .venv, git directories
        root_path = Path(root)
        if any(ignored in root_path.parts for ignored in ["output", "logs", ".venv", "venv", ".git", "__pycache__"]):
            continue
        for file in files:
            p = root_path / file
            candidate_paths.append(p)

    for path in candidate_paths:
        stem = path.stem.lower()
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        if "sujal" in stem and "kadam" in stem and "resume" in stem:
            if "new" in stem:
                if results["r2"] is None:
                    results["r2"] = path
            else:
                if results["r1"] is None:
                    results["r1"] = path

    return results


def validate_discovered_files(files: Dict[str, Optional[Path]]) -> Tuple[Path, Path]:
    """Validate that both resumes are discovered, or raise helpful errors."""
    r1 = files.get("r1")
    r2 = files.get("r2")
    missing = []
    if not r1:
        missing.append("Sujal_Kadam_Resume.[pdf|docx|txt]")
    if not r2:
        missing.append("Sujal_Kadam_Resume_new.[pdf|docx|txt]")

    if missing:
        raise FileNotFoundError(
            f"Missing required source resume file(s): {', '.join(missing)}. "
            "Please ensure both Sujal_Kadam_Resume and Sujal_Kadam_Resume_new exist "
            "in the project folder or 'Current Resumes/' subfolder."
        )
    return r1, r2  # type: ignore
