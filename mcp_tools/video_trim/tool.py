"""Trim a video by start and end time using ffmpeg."""

import os
import re
import subprocess

TIMESTAMP_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}$")


def _validate_timestamp(value: str) -> bool:
    """Check whether a string matches HH:MM:SS format."""
    return bool(TIMESTAMP_PATTERN.match(value))


def run(input_path: str, output_path: str, start: str, end: str) -> str:
    """Trim a video to the segment between start and end timestamps.

    Args:
        input_path: Path to the source video file.
        output_path: Path where the trimmed video will be saved.
        start: Start time in HH:MM:SS format.
        end: End time in HH:MM:SS format.

    Returns:
        Confirmation message with the output path and time range.
    """
    resolved_input = os.path.abspath(input_path)
    if not os.path.isfile(resolved_input):
        return f"Error: input file not found: {resolved_input}"

    if not _validate_timestamp(start):
        return f"Error: invalid start time '{start}' — expected HH:MM:SS format"

    if not _validate_timestamp(end):
        return f"Error: invalid end time '{end}' — expected HH:MM:SS format"

    resolved_output = os.path.abspath(output_path)

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", resolved_input,
                "-ss", start,
                "-to", end,
                "-c", "copy",
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
        return "Error: video trimming timed out after 300 seconds"

    if result.returncode != 0:
        return f"Error trimming video: {result.stderr.strip()}"

    return f"Video trimmed from {start} to {end} and saved to {resolved_output}"
