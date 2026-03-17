"""Delete a file."""

import os


def run(path: str) -> str:
    """Delete the file at the given path."""
    resolved = os.path.abspath(path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"File not found: {resolved}")
    if not os.path.isfile(resolved):
        raise IsADirectoryError(f"Not a file: {resolved}")
    os.remove(resolved)
    return f"Deleted {resolved}"
