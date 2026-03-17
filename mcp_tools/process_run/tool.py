"""Run a system process safely using subprocess."""

import shlex
import subprocess


def run(command: str, timeout: int = 30) -> str:
    """
    Run a system process, parsing the command safely with shlex.split.

    Never uses shell=True to prevent shell injection attacks.

    @param command: Command string to execute (e.g. 'ls -la /tmp').
    @param timeout: Timeout in seconds for the command. Defaults to 30.
    @returns: Combined stdout and stderr output from the process.
    @throws RuntimeError: If the command exits with a non-zero return code.
    @throws subprocess.TimeoutExpired: If the command exceeds the timeout.
    """
    args = shlex.split(command)

    if not args:
        raise ValueError("Command cannot be empty")

    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0:
        raise RuntimeError(
            f"Process exited with code {result.returncode}: {result.stderr.strip()}"
        )

    return result.stdout.strip()
