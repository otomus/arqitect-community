"""Capture a screenshot of the screen."""

import platform
import subprocess
import tempfile


def run(region: str = "") -> str:
    """Take a screenshot and return the file path."""
    if platform.system() != "Darwin":
        raise RuntimeError("screen_capture currently only supports macOS.")

    output_path = tempfile.mktemp(suffix=".png")
    cmd = ["screencapture", "-x"]

    if region:
        cmd.extend(["-R", region])

    cmd.append(output_path)
    subprocess.run(cmd, check=True, timeout=10)
    return output_path
