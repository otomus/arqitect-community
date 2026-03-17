"""Search for files matching a glob pattern."""

import glob
import json
import os


def run(pattern: str, path: str = ".") -> str:
    """Find files matching a glob pattern in a directory tree."""
    resolved = os.path.abspath(path)
    full_pattern = os.path.join(resolved, pattern)
    matches = sorted(glob.glob(full_pattern, recursive=True))
    return json.dumps({"pattern": pattern, "root": resolved, "count": len(matches), "matches": matches}, indent=2)
