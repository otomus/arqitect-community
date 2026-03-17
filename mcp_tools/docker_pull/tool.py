"""Pull a Docker image from a registry."""

import subprocess


def run(image: str) -> str:
    """
    Pull a Docker image from a container registry.

    @param image: Image name to pull (e.g. 'nginx:latest').
    @returns: Pull output from Docker.
    """
    cmd = ["docker", "pull", image]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        raise RuntimeError(f"docker pull failed: {result.stderr.strip()}")

    return result.stdout.strip()
