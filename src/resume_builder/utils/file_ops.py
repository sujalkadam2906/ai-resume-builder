"""File operations, atomic writes, Windows path safety, and backups."""

import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def sanitize_filename(name: str, max_length: int = 60) -> str:
    """Sanitize strings for Windows-compatible filenames."""
    # Replace illegal Windows characters: < > : " / \ | ? *
    clean = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove control characters and normalize whitespace
    clean = re.sub(r'[\r\n\t]+', ' ', clean)
    clean = re.sub(r'\s+', '_', clean).strip('._ ')
    if not clean:
        clean = "Untitled"
    if len(clean) > max_length:
        clean = clean[:max_length].rstrip('._ ')
    return clean


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text atomically using a temporary file in the same directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    dir_name = str(path.parent)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding=encoding) as tf:
        temp_path = Path(tf.name)
        tf.write(content)
    try:
        shutil.move(str(temp_path), str(path))
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def atomic_write_json(path: Path, data: Any, indent: int = 2) -> None:
    """Write JSON data atomically."""
    json_str = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write_text(path, json_str)


def create_backup(source_path: Path, backups_dir: Path) -> Path:
    """Create a timestamped backup copy of a critical file before modification."""
    if not source_path.exists():
        raise FileNotFoundError(f"Source file does not exist: {source_path}")
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
    backup_path = backups_dir / backup_filename
    shutil.copy2(source_path, backup_path)
    return backup_path
