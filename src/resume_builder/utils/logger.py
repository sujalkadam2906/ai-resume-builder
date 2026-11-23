"""Logging setup with secret redaction for the resume builder system."""

import logging
import os
import re
from pathlib import Path
from typing import Optional

_SECRET_PATTERN = re.compile(r"(AIza[0-9A-Za-z-_]{35}|[0-9a-zA-Z]{32,})")


class RedactingFormatter(logging.Formatter):
    """Custom formatter to redact sensitive API keys and secrets."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key and len(api_key) > 6:
            msg = msg.replace(api_key, "[REDACTED_API_KEY]")
        # Redact potential standard Gemini/Google keys
        msg = _SECRET_PATTERN.sub("[REDACTED_SECRET]", msg)
        return msg


def setup_logger(name: str = "resume_builder", log_dir: Optional[Path] = None, verbose: bool = False) -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = RedactingFormatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "resume_builder.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
