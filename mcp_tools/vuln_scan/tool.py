"""Scan files for common security vulnerabilities."""

import json
import os
import re

SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*[\'\"\`]([^\'\"\ \`]{8,})", "API Key"),
    (r"(?i)(secret|password|passwd|pwd)\s*[:=]\s*[\'\"\`]([^\'\"\ \`]{6,})", "Password/Secret"),
    (r"(?i)(aws_access_key_id)\s*[:=]\s*[\'\"\`]?(AKIA[A-Z0-9]{16})", "AWS Access Key"),
    (r"(?i)(private[_-]?key)\s*[:=]", "Private Key Reference"),
    (r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", "Private Key File"),
    (r"ghp_[A-Za-z0-9_]{36}", "GitHub Personal Access Token"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI/Stripe Secret Key"),
]

MAX_FILE_SIZE = 1_000_000


def run(path: str, type: str = "secrets") -> str:
    """Scan files for security issues."""
    resolved = os.path.abspath(path)
    findings = []

    if os.path.isfile(resolved):
        files = [resolved]
    elif os.path.isdir(resolved):
        files = []
        for root, _, filenames in os.walk(resolved):
            for fname in filenames:
                files.append(os.path.join(root, fname))
    else:
        raise FileNotFoundError(f"Path not found: {resolved}")

    for fpath in files:
        if os.path.getsize(fpath) > MAX_FILE_SIZE:
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    for pattern, name in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            findings.append({
                                "file": fpath, "line": line_num,
                                "type": name, "snippet": line.strip()[:100]
                            })
        except (PermissionError, OSError):
            continue

    return json.dumps({"scan_type": type, "path": resolved, "finding_count": len(findings), "findings": findings}, indent=2)
