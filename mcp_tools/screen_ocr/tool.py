"""Capture a screenshot and extract text via OCR."""

import os
import platform
import shutil
import subprocess
import tempfile


def run(region: str = "") -> str:
    """Take a screenshot and run OCR to extract text."""
    if platform.system() != "Darwin":
        raise RuntimeError("screen_ocr currently only supports macOS.")

    tesseract = shutil.which("tesseract")
    if not tesseract:
        raise RuntimeError(
            "Tesseract not found. Install it with: brew install tesseract"
        )

    # Capture screenshot
    screenshot_path = tempfile.mktemp(suffix=".png")
    cmd = ["screencapture", "-x"]
    if region:
        cmd.extend(["-R", region])
    cmd.append(screenshot_path)
    subprocess.run(cmd, check=True, timeout=10)

    # Run OCR
    try:
        result = subprocess.run(
            [tesseract, screenshot_path, "stdout"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Tesseract failed: {result.stderr}")
        return result.stdout.strip()
    finally:
        if os.path.exists(screenshot_path):
            os.unlink(screenshot_path)
