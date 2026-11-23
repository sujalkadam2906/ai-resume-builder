"""Utility functions for resume builder."""

from .file_ops import atomic_write_json, atomic_write_text, create_backup, sanitize_filename
from .logger import setup_logger
from .text_cleaner import clean_bullets, clean_text, escape_xml

__all__ = [
    "setup_logger",
    "sanitize_filename",
    "atomic_write_text",
    "atomic_write_json",
    "create_backup",
    "clean_text",
    "escape_xml",
    "clean_bullets",
]
