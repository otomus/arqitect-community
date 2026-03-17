"""Copy a file from source to destination."""

import os
import shutil


def run(source: str, dest: str) -> str:
    """Copy a file, creating destination directories if needed."""
    src = os.path.abspath(source)
    dst = os.path.abspath(dest)
    if not os.path.isfile(src):
        raise FileNotFoundError(f"Source file not found: {src}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return f"Copied {src} to {dst}"
