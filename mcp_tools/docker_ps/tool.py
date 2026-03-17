"""List Docker containers."""

import subprocess


def run(all: bool = False) -> str:
    """
    List Docker containers, optionally including stopped ones.

    @param all: If True, show all containers including stopped ones.
    @returns: Formatted table of containers.
    """
    cmd = ["docker", "ps"]

    if all:
        cmd.append("-a")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

    if result.returncode != 0:
        raise RuntimeError(f"docker ps failed: {result.stderr.strip()}")

    return result.stdout.strip()
