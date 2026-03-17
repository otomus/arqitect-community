"""Extract frames from a video at a specified frame rate using ffmpeg."""

import os
import subprocess


def run(input_path: str, output_dir: str, fps: float = 1.0) -> str:
    """Extract frames from a video file at the given FPS.

    Args:
        input_path: Path to the source video file.
        output_dir: Directory where extracted frames will be saved as PNGs.
        fps: Frames per second to extract.

    Returns:
        Confirmation message with the output directory and FPS.
    """
    resolved_input = os.path.abspath(input_path)
    if not os.path.isfile(resolved_input):
        return f"Error: input file not found: {resolved_input}"

    if fps <= 0:
        return "Error: fps must be a positive number"

    resolved_output_dir = os.path.abspath(output_dir)
    os.makedirs(resolved_output_dir, exist_ok=True)

    output_pattern = os.path.join(resolved_output_dir, "frame_%04d.png")

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", resolved_input,
                "-vf", f"fps={fps}",
                output_pattern,
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
        return "Error: frame extraction timed out after 300 seconds"

    if result.returncode != 0:
        return f"Error extracting frames: {result.stderr.strip()}"

    extracted_files = [f for f in os.listdir(resolved_output_dir) if f.startswith("frame_")]
    return f"Extracted {len(extracted_files)} frames at {fps} fps to {resolved_output_dir}"
