"""Generate or read QR codes."""

import os


def run(operation: str, content: str = "", image_path: str = "") -> str:
    """Generate a QR code image or read a QR code from an image.

    @param operation: 'generate' to create a QR code, 'read' to decode one.
    @param content: Data to encode (required for generate).
    @param image_path: Output path (generate) or input path (read).
    @returns Confirmation message or decoded QR data.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "generate":
        return _generate(content, image_path)
    if operation == "read":
        return _read(image_path)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'generate' or 'read'.")


def _generate(data: str, output_path: str) -> str:
    """Generate a QR code image and save it to a file."""
    try:
        import qrcode
    except ImportError:
        return ("error: qrcode is required but not installed. "
                "Install it with: pip install qrcode[pil]")

    if not data.strip():
        raise ValueError("Data cannot be empty")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    img.save(output_path)
    return f"QR code saved to {output_path}"


def _read(image_path: str) -> str:
    """Read and decode a QR code from an image file."""
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    decoded_data = _try_pyzbar(image_path)
    if decoded_data is not None:
        return decoded_data

    decoded_data = _try_cv2(image_path)
    if decoded_data is not None:
        return decoded_data

    return ("error: No QR code reader available. Install one of: "
            "pip install pyzbar Pillow  OR  pip install opencv-python")


def _try_pyzbar(image_path: str) -> str | None:
    """Attempt to decode using pyzbar and Pillow."""
    try:
        from pyzbar.pyzbar import decode
        from PIL import Image
    except ImportError:
        return None

    img = Image.open(image_path)
    results = decode(img)

    if not results:
        raise ValueError(f"No QR code found in image: {image_path}")

    decoded_values = [result.data.decode("utf-8") for result in results]
    return "\n".join(decoded_values)


def _try_cv2(image_path: str) -> str | None:
    """Attempt to decode using OpenCV's built-in QR detector."""
    try:
        import cv2
    except ImportError:
        return None

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)

    if not data:
        raise ValueError(f"No QR code found in image: {image_path}")

    return data
