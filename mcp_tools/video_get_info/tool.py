"""Get video metadata using ffprobe."""

import json
import os
import subprocess


def run(input_path: str) -> str:
    """Retrieve metadata for a video file using ffprobe.

    Args:
        input_path: Path to the video file.

    Returns:
        JSON-formatted string containing video metadata (duration, resolution, codecs, etc.).
    """
    resolved_input = os.path.abspath(input_path)
    if not os.path.isfile(resolved_input):
        return f"Error: input file not found: {resolved_input}"

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                resolved_input,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return "Error: ffprobe is not installed or not found in PATH"
    except subprocess.TimeoutExpired:
        return "Error: ffprobe timed out after 30 seconds"

    if result.returncode != 0:
        return f"Error reading video info: {result.stderr.strip()}"

    try:
        probe_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return f"Error: could not parse ffprobe output"

    info = _extract_summary(probe_data)
    return json.dumps(info, indent=2)


def _extract_summary(probe_data: dict) -> dict:
    """Build a concise summary from raw ffprobe JSON output."""
    summary: dict = {}

    fmt = probe_data.get("format", {})
    summary["filename"] = fmt.get("filename", "unknown")
    summary["format"] = fmt.get("format_long_name", fmt.get("format_name", "unknown"))
    summary["duration_seconds"] = fmt.get("duration", "unknown")
    summary["size_bytes"] = fmt.get("size", "unknown")
    summary["bit_rate"] = fmt.get("bit_rate", "unknown")

    streams = probe_data.get("streams", [])
    summary["streams"] = []
    for stream in streams:
        stream_info: dict = {
            "type": stream.get("codec_type", "unknown"),
            "codec": stream.get("codec_long_name", stream.get("codec_name", "unknown")),
        }
        if stream.get("codec_type") == "video":
            stream_info["width"] = stream.get("width")
            stream_info["height"] = stream.get("height")
            stream_info["fps"] = stream.get("r_frame_rate", "unknown")
        elif stream.get("codec_type") == "audio":
            stream_info["sample_rate"] = stream.get("sample_rate", "unknown")
            stream_info["channels"] = stream.get("channels", "unknown")
        summary["streams"].append(stream_info)

    return summary
