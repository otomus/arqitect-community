"""List contents of a directory."""

import fnmatch
import json
import os


def run(path: str, pattern: str = "*") -> str:
    """List directory contents, optionally filtered by glob pattern."""
    resolved = os.path.abspath(path)
    if not os.path.isdir(resolved):
        raise NotADirectoryError(f"Not a directory: {resolved}")
    entries = []
    for name in sorted(os.listdir(resolved)):
        if not fnmatch.fnmatch(name, pattern):
            continue
        full = os.path.join(resolved, name)
        entries.append({
            "name": name,
            "type": "directory" if os.path.isdir(full) else "file",
            "size": os.path.getsize(full) if os.path.isfile(full) else None,
        })
    return json.dumps(entries, indent=2)
