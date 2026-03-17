"""List running system processes with optional filtering."""

import subprocess
from typing import Optional


def run(filter: Optional[str] = None) -> str:
    """
    List running system processes, optionally filtered by name.

    Uses 'ps aux' to retrieve the process list and filters results
    in Python to avoid shell=True.

    @param filter: Optional string to filter process names by substring match.
    @returns: Filtered process listing.
    """
    cmd = ["ps", "aux"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    if result.returncode != 0:
        raise RuntimeError(f"ps failed: {result.stderr.strip()}")

    output = result.stdout

    if filter:
        lines = output.splitlines()
        header = lines[0] if lines else ""
        filtered = [line for line in lines[1:] if filter.lower() in line.lower()]
        return header + "\n" + "\n".join(filtered)

    return output.strip()
