"""Get metadata about a file."""

import json
import os
import stat
from datetime import datetime, timezone


def run(path: str) -> str:
    """Get file metadata: size, timestamps, permissions."""
    resolved = os.path.abspath(path)
    st = os.stat(resolved)
    return json.dumps({
        "path": resolved,
        "size_bytes": st.st_size,
        "created": datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat(),
        "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "permissions": stat.filemode(st.st_mode),
        "is_file": os.path.isfile(resolved),
        "is_directory": os.path.isdir(resolved),
    }, indent=2)
