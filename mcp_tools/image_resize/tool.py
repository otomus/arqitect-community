"""Resize an image to the specified width and height using Pillow."""

import os


def run(input_path: str, output_path: str, width: int, height: int) -> str:
    """Resize an image to the given dimensions and save the result.

    Args:
        input_path: Path to the source image file.
        output_path: Path where the resized image will be saved.
        width: Target width in pixels.
        height: Target height in pixels.

    Returns:
        Confirmation message with the output path and new dimensions.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If width or height is not positive.
    """
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow is not installed. Run: pip install Pillow"

    if width <= 0 or height <= 0:
        return "Error: width and height must be positive integers"

    resolved_input = os.path.abspath(input_path)
    if not os.path.isfile(resolved_input):
        return f"Error: input file not found: {resolved_input}"

    resolved_output = os.path.abspath(output_path)
    img = Image.open(resolved_input)
    resized = img.resize((width, height), Image.LANCZOS)
    resized.save(resolved_output)

    return f"Image resized to {width}x{height} and saved to {resolved_output}"
