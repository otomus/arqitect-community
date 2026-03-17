"""Delete a directory and its contents."""

import os
import shutil


def run(path: str) -> str:
    """Delete a directory recursively."""
    resolved = os.path.abspath(path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"Directory not found: {resolved}")
    if not os.path.isdir(resolved):
        raise NotADirectoryError(f"Not a directory: {resolved}")
    shutil.rmtree(resolved)
    return f"Deleted directory: {resolved}"
