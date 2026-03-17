"""Watch a file or directory and report its current state."""

import json
import os
from datetime import datetime, timezone


def run(path: str) -> str:
    """Snapshot the current state of a file or directory for change detection."""
    resolved = os.path.abspath(path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"Path not found: {resolved}")

    if os.path.isfile(resolved):
        st = os.stat(resolved)
        return json.dumps({
            "path": resolved,
            "type": "file",
            "size": st.st_size,
            "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        }, indent=2)

    entries = {}
    for name in sorted(os.listdir(resolved)):
        full = os.path.join(resolved, name)
        st = os.stat(full)
        entries[name] = {
            "type": "directory" if os.path.isdir(full) else "file",
            "size": st.st_size,
            "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        }
    return json.dumps({"path": resolved, "type": "directory", "entries": entries}, indent=2)
