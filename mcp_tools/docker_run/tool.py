"""Run a Docker container from a specified image."""

import subprocess
from typing import Optional


def run(image: str, name: Optional[str] = None, ports: Optional[str] = None, detach: bool = True) -> str:
    """
    Run a Docker container from the given image.

    @param image: Docker image to run (e.g. 'nginx:latest').
    @param name: Optional name to assign to the container.
    @param ports: Port mapping in host:container format (e.g. '8080:80').
    @param detach: Whether to run in detached mode. Defaults to True.
    @returns: Container ID or command output.
    """
    cmd = ["docker", "run"]

    if detach:
        cmd.append("-d")

    if name:
        cmd.extend(["--name", name])

    if ports:
        cmd.extend(["-p", ports])

    cmd.append(image)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        raise RuntimeError(f"docker run failed: {result.stderr.strip()}")

    return result.stdout.strip()
