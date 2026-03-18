"""Capture a screenshot on macOS."""

import platform
import subprocess
import tempfile


def run(region: str = "", window: str = "") -> str:
    """Capture a screenshot and return the file path."""
    if platform.system() != "Darwin":
        raise RuntimeError("image_capture is only supported on macOS.")

    output_path = tempfile.mktemp(suffix=".png")
    cmd = ["screencapture", "-x"]

    if window:
        cmd.extend(["-l", window])
    elif region:
        cmd.extend(["-R", region])

    cmd.append(output_path)
    subprocess.run(cmd, check=True, timeout=10)
    return output_path
