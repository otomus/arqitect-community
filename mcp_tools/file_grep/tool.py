"""Search for a text pattern inside files."""

import fnmatch
import json
import os
import re

MAX_RESULTS = 100


def run(pattern: str, path: str = ".", glob: str = "*") -> str:
    """Search file contents for a regex pattern."""
    resolved = os.path.abspath(path)
    compiled = re.compile(pattern)
    results = []

    if os.path.isfile(resolved):
        files = [resolved]
    else:
        files = []
        for root, _, filenames in os.walk(resolved):
            for fname in filenames:
                if fnmatch.fnmatch(fname, glob):
                    files.append(os.path.join(root, fname))

    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if compiled.search(line):
                        results.append({"file": fpath, "line": line_num, "text": line.rstrip()})
                        if len(results) >= MAX_RESULTS:
                            return json.dumps({"truncated": True, "count": len(results), "matches": results}, indent=2)
        except (PermissionError, OSError):
            continue

    return json.dumps({"count": len(results), "matches": results}, indent=2)
