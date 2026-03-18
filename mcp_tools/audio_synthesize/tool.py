"""Convert text to speech audio."""

import platform
import subprocess
import tempfile


def run(text: str, voice: str = "") -> str:
    """Synthesize speech from text and return the output file path."""
    if platform.system() != "Darwin":
        raise RuntimeError(
            "audio_synthesize currently only supports macOS (uses the 'say' command)."
        )

    output_path = tempfile.mktemp(suffix=".aiff")
    cmd = ["say", "-o", output_path]
    if voice:
        cmd.extend(["-v", voice])
    cmd.append(text)

    subprocess.run(cmd, check=True, timeout=60)
    return output_path
