"""Extract text from an image using OCR via pytesseract."""

import os


def run(image_path: str, language: str = "eng") -> str:
    """Perform OCR on an image and return the extracted text.

    Args:
        image_path: Path to the image file to extract text from.
        language: Tesseract language code (e.g. 'eng', 'fra', 'deu').

    Returns:
        The extracted text, or an error message on failure.
    """
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow is not installed. Run: pip install Pillow"

    try:
        import pytesseract
    except ImportError:
        return "Error: pytesseract is not installed. Run: pip install pytesseract"

    resolved_path = os.path.abspath(image_path)
    if not os.path.isfile(resolved_path):
        return f"Error: image file not found: {resolved_path}"

    img = Image.open(resolved_path)
    text = pytesseract.image_to_string(img, lang=language)
    stripped = text.strip()

    if not stripped:
        return "No text detected in the image"

    return stripped
