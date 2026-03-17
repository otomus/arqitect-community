"""Move or rename a file."""

import os
import shutil


def run(source: str, dest: str) -> str:
    """Move a file to a new location, creating directories if needed."""
    src = os.path.abspath(source)
    dst = os.path.abspath(dest)
    if not os.path.isfile(src):
        raise FileNotFoundError(f"Source file not found: {src}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return f"Moved {src} to {dst}"
