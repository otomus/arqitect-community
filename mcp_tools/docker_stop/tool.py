"""Stop a running Docker container."""

import subprocess


def run(container_id: str) -> str:
    """
    Stop a running Docker container by ID or name.

    @param container_id: Container ID or name to stop.
    @returns: The stopped container ID.
    """
    cmd = ["docker", "stop", container_id]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"docker stop failed: {result.stderr.strip()}")

    return result.stdout.strip()
