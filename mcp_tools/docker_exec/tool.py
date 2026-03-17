"""Execute a command inside a running Docker container."""

import shlex
import subprocess


def run(container_id: str, command: str) -> str:
    """
    Execute a command inside a running Docker container.

    Uses shlex.split to safely parse the command string into arguments,
    avoiding shell injection.

    @param container_id: Container ID or name to execute the command in.
    @param command: Command to execute inside the container.
    @returns: Command output from the container.
    """
    cmd = ["docker", "exec", container_id] + shlex.split(command)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        raise RuntimeError(f"docker exec failed: {result.stderr.strip()}")

    return result.stdout.strip()
