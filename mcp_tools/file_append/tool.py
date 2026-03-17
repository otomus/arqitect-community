"""Append content to the end of a file."""

import os


def run(path: str, content: str) -> str:
    """Append content to a file, creating it if it does not exist."""
    resolved = os.path.abspath(path)
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "a", encoding="utf-8") as f:
        bytes_written = f.write(content)
    return f"Appended {bytes_written} characters to {resolved}"
