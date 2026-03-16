#!/usr/bin/env python3
"""Secret scanner — checks files for leaked credentials, keys, and absolute paths."""

import os
import re
import sys

# Filenames that should never be committed
FORBIDDEN_FILES = {".env", "credentials.json"}
FORBIDDEN_EXTENSIONS = {".pem", ".key"}

# Content patterns that indicate leaked secrets
SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI/Stripe secret key"),
    (r"ghp_[A-Za-z0-9]{36,}", "GitHub personal access token"),
    (r"AKIA[A-Z0-9]{16}", "AWS access key ID"),
    (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", "Bearer token"),
    (r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----", "Private key"),
    (r"(?:mongodb|postgres|mysql)://[^\s\"']+:[^\s\"']+@", "Database connection string"),
    (r"(?:api_key|apikey|api-key)\s*[=:]\s*[\"']?[A-Za-z0-9\-._]{16,}", "API key assignment"),
    (r"(?:secret|password|passwd)\s*[=:]\s*[\"']?[^\s\"']{8,}", "Secret/password assignment"),
]

# Absolute path patterns
ABS_PATH_PATTERNS = [
    (r"/Users/[^\s\"']+", "macOS absolute path"),
    (r"/home/[^\s\"']+", "Linux absolute path"),
    (r"C:\\Users\\[^\s\"']+", "Windows absolute path"),
]


def find_pattern_violations(
    content: str,
    patterns: list[tuple[str, str]],
    filepath: str,
    truncate: int = 40,
    suffix: str = "",
) -> list[str]:
    """Match a list of (regex, description) patterns against content.

    Returns violation messages with matches truncated to the given length.
    A fixed suffix (e.g. '...') is appended after the truncated match text.
    """
    violations = []
    for pattern, desc in patterns:
        for match in re.findall(pattern, content):
            violations.append(f"  {desc}: {filepath} ({match[:truncate]}{suffix})")
    return violations


def check_forbidden(filepath: str) -> list[str]:
    """Check whether a file is forbidden by name or extension.

    Returns a single-element list with a violation message, or an empty list.
    """
    basename = os.path.basename(filepath)
    _, ext = os.path.splitext(basename)
    if basename in FORBIDDEN_FILES or ext in FORBIDDEN_EXTENSIONS:
        return [f"  FORBIDDEN FILE: {filepath}"]
    return []


def read_text(filepath: str) -> str | None:
    """Read a file as UTF-8 text, returning None on failure."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def check_file(filepath: str) -> list[str]:
    """Check a single file for secrets. Returns list of violation messages."""
    forbidden = check_forbidden(filepath)
    if forbidden:
        return forbidden

    content = read_text(filepath)
    if content is None:
        return []

    violations = find_pattern_violations(content, SECRET_PATTERNS, filepath, truncate=40, suffix="...")
    violations += find_pattern_violations(content, ABS_PATH_PATTERNS, filepath, truncate=60)
    return violations


def iter_files(path: str):
    """Yield file paths under a directory, skipping hidden dirs and node_modules."""
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        for fname in files:
            yield os.path.join(root, fname)


def scan_directory(path: str) -> list[str]:
    """Scan a directory tree for secrets. Returns list of violations."""
    violations = []
    for filepath in iter_files(path):
        violations.extend(check_file(filepath))
    return violations


def main():
    """Entry point — scan paths from argv (or cwd) and report violations."""
    paths = sys.argv[1:] if len(sys.argv) > 1 else ["."]
    all_violations = []

    for path in paths:
        if os.path.isfile(path):
            all_violations.extend(check_file(path))
        elif os.path.isdir(path):
            all_violations.extend(scan_directory(path))

    if all_violations:
        print("SECRET SCAN FAILED — violations found:")
        for v in all_violations:
            print(v)
        sys.exit(1)
    else:
        print("Secret scan passed — no violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
