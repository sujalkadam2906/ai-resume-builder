"""Automated PostgreSQL Database Backup Script for AI Resume Builder Platform."""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def compute_sha256(path: Path) -> str:
    """Compute SHA256 checksum of a backup file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def backup_database(container_name: str = "resume_builder_db", db_name: str = "resume_builder", user: str = "postgres") -> Path:
    """Execute pg_dump via docker container or local pg_dump."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"resume_builder_backup_{timestamp}.sql"
    meta_file = BACKUP_DIR / f"resume_builder_backup_{timestamp}.json"

    print(f"[INFO] Creating database backup: {backup_file.name}")

    # Attempt via Docker container first
    cmd = ["docker", "exec", container_name, "pg_dump", "-U", user, db_name]
    try:
        with open(backup_file, "wb") as f:
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"[WARN] Docker pg_dump failed ({exc}). Attempting host pg_dump...")
        host_cmd = ["pg_dump", "-U", user, "-d", db_name]
        with open(backup_file, "wb") as f:
            subprocess.run(host_cmd, stdout=f, check=True)

    if not backup_file.exists() or backup_file.stat().st_size == 0:
        raise RuntimeError(f"Backup file {backup_file} is empty or was not created.")

    size_bytes = backup_file.stat().st_size
    checksum = compute_sha256(backup_file)

    metadata = {
        "timestamp": timestamp,
        "backup_file": backup_file.name,
        "size_bytes": size_bytes,
        "sha256": checksum,
        "database": db_name,
        "user": user,
    }
    meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"[SUCCESS] Database backup created successfully:")
    print(f"  File: {backup_file}")
    print(f"  Size: {size_bytes:,} bytes")
    print(f"  SHA256: {checksum}")
    return backup_file


if __name__ == "__main__":
    backup_database()
