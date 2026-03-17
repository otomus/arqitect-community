"""Check whether a file exists."""

import json
import os


def run(path: str) -> str:
    """Check if a file exists and return its type."""
    resolved = os.path.abspath(path)
    exists = os.path.exists(resolved)
    is_file = os.path.isfile(resolved)
    is_dir = os.path.isdir(resolved)
    return json.dumps({"path": resolved, "exists": exists, "is_file": is_file, "is_directory": is_dir})
