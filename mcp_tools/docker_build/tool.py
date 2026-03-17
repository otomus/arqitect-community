"""Build a Docker image from a Dockerfile."""

import subprocess


def run(path: str, tag: str) -> str:
    """
    Build a Docker image from a Dockerfile in the given path.

    @param path: Path to the build context directory containing the Dockerfile.
    @param tag: Tag for the built image (e.g. 'myapp:latest').
    @returns: Build output from Docker.
    """
    cmd = ["docker", "build", "-t", tag, path]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        raise RuntimeError(f"docker build failed: {result.stderr.strip()}")

    return result.stdout.strip()
