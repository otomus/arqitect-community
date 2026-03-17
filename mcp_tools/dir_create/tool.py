"""Create a directory."""

import os


def run(path: str) -> str:
    """Create a directory, including parent directories."""
    resolved = os.path.abspath(path)
    os.makedirs(resolved, exist_ok=True)
    return f"Created directory: {resolved}"
