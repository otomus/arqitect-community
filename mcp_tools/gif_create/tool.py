"""Create an animated GIF from a list of image files using Pillow."""

import json
import os


def run(image_paths: str, output_path: str, duration: int = 500) -> str:
    """Create an animated GIF from multiple image frames.

    Args:
        image_paths: JSON array of image file paths.
        output_path: Path where the GIF will be saved.
        duration: Duration per frame in milliseconds.

    Returns:
        Confirmation message with the output path and frame count.
    """
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow is not installed. Run: pip install Pillow"

    try:
        paths = json.loads(image_paths)
    except json.JSONDecodeError:
        return "Error: image_paths must be a valid JSON array of file paths"

    if not isinstance(paths, list) or len(paths) < 2:
        return "Error: at least 2 image paths are required to create a GIF"

    resolved_paths = [os.path.abspath(p) for p in paths]
    for p in resolved_paths:
        if not os.path.isfile(p):
            return f"Error: image file not found: {p}"

    frames = [Image.open(p) for p in resolved_paths]

    # Ensure all frames are the same mode
    first_frame = frames[0].convert("RGBA")
    remaining_frames = [f.convert("RGBA") for f in frames[1:]]

    resolved_output = os.path.abspath(output_path)
    first_frame.save(
        resolved_output,
        format="GIF",
        save_all=True,
        append_images=remaining_frames,
        duration=duration,
        loop=0,
    )

    frame_count = len(frames)
    return f"GIF created with {frame_count} frames ({duration}ms per frame) and saved to {resolved_output}"
