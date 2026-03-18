"""Capture an image from a connected camera."""

import platform
import shutil
import subprocess
import tempfile


def run(device_id: str = "", resolution: str = "") -> str:
    """Capture a photo from the camera and return the file path."""
    if platform.system() != "Darwin":
        raise RuntimeError("camera_capture currently only supports macOS.")

    imagesnap = shutil.which("imagesnap")
    if not imagesnap:
        raise RuntimeError(
            "imagesnap not found. Install it with: brew install imagesnap"
        )

    output_path = tempfile.mktemp(suffix=".jpg")
    cmd = [imagesnap, output_path]
    if device_id:
        cmd.extend(["-d", device_id])

    subprocess.run(cmd, check=True, timeout=10)
    return output_path
