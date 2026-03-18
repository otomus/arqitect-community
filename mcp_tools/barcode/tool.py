"""Generate or read barcodes."""

import os

SUPPORTED_BARCODE_TYPES = ("code128", "ean13", "upc")

BARCODE_TYPE_MAP = {
    "code128": "code128",
    "ean13": "ean13",
    "upc": "upca",
}


def run(operation: str, content: str = "", image_path: str = "", type: str = "code128") -> str:
    """Generate a barcode image or read a barcode from an image.

    @param operation: 'generate' to create a barcode, 'read' to decode one.
    @param content: Data to encode (required for generate).
    @param image_path: Output path (generate) or input path (read).
    @param type: Barcode format (code128, ean13, upc). Defaults to code128.
    @returns Confirmation message or decoded barcode data.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "generate":
        return _generate(content, image_path, type)
    if operation == "read":
        return _read(image_path)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'generate' or 'read'.")


def _generate(data: str, output_path: str, barcode_type: str) -> str:
    """Generate a barcode image and save it to a file."""
    try:
        import barcode as barcode_lib
        from barcode.writer import ImageWriter
    except ImportError:
        return ("error: python-barcode is required but not installed. "
                "Install it with: pip install python-barcode Pillow")

    if not data.strip():
        raise ValueError("Data cannot be empty")

    if barcode_type not in SUPPORTED_BARCODE_TYPES:
        raise ValueError(
            f"Unsupported barcode type: {barcode_type}. "
            f"Supported types: {', '.join(SUPPORTED_BARCODE_TYPES)}"
        )

    internal_type = BARCODE_TYPE_MAP[barcode_type]
    barcode_class = barcode_lib.get_barcode_class(internal_type)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    base_path = _strip_image_extension(output_path)

    writer = ImageWriter()
    barcode_instance = barcode_class(data, writer=writer)
    saved_path = barcode_instance.save(base_path)

    return f"Barcode saved to {saved_path}"


def _strip_image_extension(path: str) -> str:
    """Remove common image extensions so python-barcode can add its own."""
    for ext in (".png", ".svg", ".jpg", ".jpeg"):
        if path.lower().endswith(ext):
            return path[: -len(ext)]
    return path


def _read(image_path: str) -> str:
    """Read and decode a barcode from an image file."""
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        from pyzbar.pyzbar import decode
        from PIL import Image
    except ImportError:
        return ("error: pyzbar and Pillow are required but not installed. "
                "Install them with: pip install pyzbar Pillow")

    img = Image.open(image_path)
    results = decode(img)

    if not results:
        raise ValueError(f"No barcode found in image: {image_path}")

    entries = []
    for result in results:
        barcode_data = result.data.decode("utf-8")
        barcode_type = result.type
        entries.append(f"[{barcode_type}] {barcode_data}")

    return "\n".join(entries)
