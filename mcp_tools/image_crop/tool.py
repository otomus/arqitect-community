"""Crop an image to the specified bounding box using Pillow."""

import os


def run(input_path: str, output_path: str, left: int, top: int, right: int, bottom: int) -> str:
    """Crop an image using a bounding box and save the result.

    Args:
        input_path: Path to the source image file.
        output_path: Path where the cropped image will be saved.
        left: Left edge of the crop box in pixels.
        top: Top edge of the crop box in pixels.
        right: Right edge of the crop box in pixels.
        bottom: Bottom edge of the crop box in pixels.

    Returns:
        Confirmation message with the output path and crop dimensions.
    """
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow is not installed. Run: pip install Pillow"

    if left >= right or top >= bottom:
        return "Error: invalid crop box — left must be less than right, top must be less than bottom"

    resolved_input = os.path.abspath(input_path)
    if not os.path.isfile(resolved_input):
        return f"Error: input file not found: {resolved_input}"

    resolved_output = os.path.abspath(output_path)
    img = Image.open(resolved_input)
    cropped = img.crop((left, top, right, bottom))
    cropped.save(resolved_output)

    crop_width = right - left
    crop_height = bottom - top
    return f"Image cropped to {crop_width}x{crop_height} and saved to {resolved_output}"
