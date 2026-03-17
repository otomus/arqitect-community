"""Write content to a file."""

import os


def run(path: str, content: str) -> str:
    """Write content to a file, creating parent directories if needed."""
    resolved = os.path.abspath(path)
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w", encoding="utf-8") as f:
        bytes_written = f.write(content)
    return f"Wrote {bytes_written} characters to {resolved}"
