"""Dedicated Gitleaks-equivalent secret scanner for AI Resume Builder."""

from pathlib import Path
import re
import subprocess
import sys

RULES = {
    "Google API Key": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "Groq API Key": re.compile(r"gsk_[0-9A-Za-z]{20,}"),
    "OpenAI / OpenRouter Key": re.compile(r"sk-(?:or-)?[0-9A-Za-z\-_]{20,}"),
    "GitHub Token": re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{82}"),
    "AWS Access Key": re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
    "Generic Private Key": re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
    "Generic Token / Secret Assignment": re.compile(
        r"(?i)(?:api[_-]?key|secret[_-]?key|auth[_-]?token|password)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{16,}['\"]"
    ),
}

PRIVATE_CONTACTS = {
    "Private Phone Number": "9028574850",
    "Private Personal Email": "sujalsunilkadam@gmail.com",
}


def scan_git_history():
    """Scans all historical git commits if any exist."""
    findings = []
    try:
        rev_check = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if rev_check.returncode != 0:
            print("[INFO] Repository has zero prior Git commits (fresh repo). No commit history to scan.")
            return findings

        log_output = subprocess.check_output(["git", "log", "-p", "--all"], text=True)
        print("[INFO] Scanning historical Git commits across all branches...")
        lines = log_output.splitlines()
        for idx, line in enumerate(lines, 1):
            if not line.startswith("+"):
                continue
            for rule_name, pattern in RULES.items():
                if pattern.search(line):
                    findings.append(f"[HISTORY_SECRET] Line {idx} matches {rule_name}")
            for contact_name, indicator in PRIVATE_CONTACTS.items():
                if indicator in line:
                    findings.append(f"[HISTORY_PRIVATE_DATA] Line {idx} contains {contact_name}")
    except Exception as e:
        findings.append(f"[ERROR] Could not inspect git history: {e}")
    return findings


def scan_staged_files():
    staged_output = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True)
    staged_files = [line.strip() for line in staged_output.splitlines() if line.strip()]

    print(f"Auditing {len(staged_files)} staged files...")
    findings = []

    binary_extensions = (".png", ".pdf", ".docx", ".ico", ".jpg", ".jpeg")

    for fpath_str in staged_files:
        p = Path(fpath_str)
        if p.suffix.lower() in binary_extensions or p.name == "scan_secrets.py":
            continue

        if not p.is_file():
            continue

        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            for line_no, line in enumerate(lines, 1):
                # Skip harmless empty environment variable placeholders in .env.example
                if p.name == ".env.example" and line.strip().endswith("="):
                    continue

                # Check secret regex rules
                for rule_name, pattern in RULES.items():
                    if pattern.search(line):
                        findings.append(f"[SECRET] {fpath_str}:{line_no} matches {rule_name}")

                # Check private contact indicators
                for contact_name, indicator in PRIVATE_CONTACTS.items():
                    if indicator in line:
                        findings.append(f"[PRIVATE_DATA] {fpath_str}:{line_no} contains {contact_name}")

        except Exception as e:
            findings.append(f"[ERROR] Could not inspect {fpath_str}: {e}")

    return findings


def main():
    history_findings = scan_git_history()
    staged_findings = scan_staged_files()
    all_findings = history_findings + staged_findings

    if not all_findings:
        print("SECRET SCANNER PASSED: ZERO secrets and ZERO private candidate contacts detected in repository/staged files!")
        sys.exit(0)
    else:
        print(f"SECRET SCANNER FAILED: Found {len(all_findings)} issues:")
        for f in all_findings:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
