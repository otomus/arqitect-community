"""Convert an image to a different format using Pillow."""

import os

SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp", "bmp"}

FORMAT_MAP = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "bmp": "BMP",
}


def run(input_path: str, output_path: str, format: str) -> str:
    """Convert an image file to the specified format.

    Args:
        input_path: Path to the source image file.
        output_path: Path where the converted image will be saved.
        format: Target format (png, jpg, webp, or bmp).

    Returns:
        Confirmation message with the output path and target format.
    """
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow is not installed. Run: pip install Pillow"

    fmt_lower = format.lower()
    if fmt_lower not in SUPPORTED_FORMATS:
        return f"Error: unsupported format '{format}'. Supported: png, jpg, webp, bmp"

    resolved_input = os.path.abspath(input_path)
    if not os.path.isfile(resolved_input):
        return f"Error: input file not found: {resolved_input}"

    resolved_output = os.path.abspath(output_path)
    img = Image.open(resolved_input)

    # Convert RGBA to RGB for formats that do not support alpha
    pillow_format = FORMAT_MAP[fmt_lower]
    if pillow_format in ("JPEG", "BMP") and img.mode == "RGBA":
        img = img.convert("RGB")

    img.save(resolved_output, format=pillow_format)
    return f"Image converted to {fmt_lower} and saved to {resolved_output}"
