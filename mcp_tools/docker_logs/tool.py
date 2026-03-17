"""Get logs from a Docker container."""

import subprocess
from typing import Optional


def run(container_id: str, tail: Optional[int] = None) -> str:
    """
    Retrieve logs from a Docker container.

    @param container_id: Container ID or name to get logs from.
    @param tail: Number of lines to show from the end of the logs.
    @returns: Container log output.
    """
    cmd = ["docker", "logs"]

    if tail is not None:
        cmd.extend(["--tail", str(tail)])

    cmd.append(container_id)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

    if result.returncode != 0:
        raise RuntimeError(f"docker logs failed: {result.stderr.strip()}")

    # Docker may write to both stdout and stderr for log output
    output = result.stdout + result.stderr
    return output.strip()
