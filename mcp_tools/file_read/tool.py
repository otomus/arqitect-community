"""Read the contents of a file."""

import os


def run(path: str, offset: int = 0, limit: int = 0) -> str:
    """Read file contents, optionally from a line offset with a line limit."""
    resolved = os.path.abspath(path)
    with open(resolved, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if offset > 0:
        lines = lines[offset:]
    if limit > 0:
        lines = lines[:limit]
    return "".join(lines)
