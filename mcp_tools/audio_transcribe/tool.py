"""Transcribe audio to text using whisper CLI."""

import shutil
import subprocess


def run(path: str, language: str = "") -> str:
    """Transcribe an audio file using the whisper CLI."""
    whisper_bin = shutil.which("whisper")
    if not whisper_bin:
        raise RuntimeError(
            "Whisper CLI not found. Install it with: pip install openai-whisper"
        )

    cmd = [whisper_bin, path, "--output_format", "txt"]
    if language:
        cmd.extend(["--language", language])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Whisper failed: {result.stderr}")
    return result.stdout.strip()
