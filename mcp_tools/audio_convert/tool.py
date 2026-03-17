"""Convert audio to a different format using ffmpeg."""

import os
import subprocess

SUPPORTED_FORMATS = {"mp3", "wav", "ogg", "flac"}


def run(input_path: str, output_path: str, format: str) -> str:
    """Convert an audio file to the specified format.

    Args:
        input_path: Path to the source audio file.
        output_path: Path where the converted audio will be saved.
        format: Target format (mp3, wav, ogg, or flac).

    Returns:
        Confirmation message with the output path and target format.
    """
    fmt_lower = format.lower()
    if fmt_lower not in SUPPORTED_FORMATS:
        return f"Error: unsupported format '{format}'. Supported: mp3, wav, ogg, flac"

    resolved_input = os.path.abspath(input_path)
    if not os.path.isfile(resolved_input):
        return f"Error: input file not found: {resolved_input}"

    resolved_output = os.path.abspath(output_path)

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", resolved_input,
                resolved_output,
                "-y",
                "-loglevel", "error",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        return "Error: ffmpeg is not installed or not found in PATH"
    except subprocess.TimeoutExpired:
        return "Error: audio conversion timed out after 300 seconds"

    if result.returncode != 0:
        return f"Error converting audio: {result.stderr.strip()}"

    return f"Audio converted to {fmt_lower} and saved to {resolved_output}"
