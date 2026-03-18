"""Read or create PowerPoint PPTX files."""

import json
import os


def run(path: str, operation: str, slides: str = "") -> str:
    """Read text from a PPTX or create a new PPTX from slide data.

    @param path: Path to the PPTX file.
    @param operation: 'read' to extract text, 'create' to write a new PPTX.
    @param slides: JSON array of slide objects (required for create).
    @returns Extracted text or confirmation message.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "read":
        return _read_pptx(path)
    if operation == "create":
        return _create_pptx(path, slides)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'read' or 'create'.")


def _read_pptx(file_path: str) -> str:
    """Extract all text content from a PowerPoint file."""
    try:
        from pptx import Presentation
    except ImportError:
        return ("error: python-pptx is required but not installed. "
                "Install it with: pip install python-pptx")

    resolved = os.path.abspath(file_path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"PowerPoint file not found: {resolved}")

    presentation = Presentation(resolved)
    slides_text: list[str] = []

    for slide_number, slide in enumerate(presentation.slides, start=1):
        texts = _extract_slide_text(slide)
        if texts:
            slide_content = "\n".join(texts)
            slides_text.append(f"--- Slide {slide_number} ---\n{slide_content}")

    if not slides_text:
        return "No text content found in the PowerPoint file."

    return "\n\n".join(slides_text)


def _extract_slide_text(slide: object) -> list[str]:
    """Extract all text fragments from a single slide's shapes."""
    texts: list[str] = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                text = paragraph.text.strip()
                if text:
                    texts.append(text)
    return texts


def _create_pptx(file_path: str, slides: str) -> str:
    """Create a PowerPoint file from JSON slide data."""
    try:
        from pptx import Presentation
    except ImportError:
        return ("error: python-pptx is required but not installed. "
                "Install it with: pip install python-pptx")

    try:
        slide_data = json.loads(slides)
    except json.JSONDecodeError as err:
        raise ValueError(f"Invalid JSON slides data: {err}")

    if not isinstance(slide_data, list):
        raise ValueError("Slides must be a JSON array of slide objects.")

    resolved = os.path.abspath(file_path)
    parent_dir = os.path.dirname(resolved)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    presentation = Presentation()

    for index, slide_info in enumerate(slide_data):
        if not isinstance(slide_info, dict):
            raise ValueError(
                f"Slide at index {index} must be an object with 'title' and 'content'."
            )
        title = slide_info.get("title", "")
        content = slide_info.get("content", "")

        slide_layout = presentation.slide_layouts[1]
        slide = presentation.slides.add_slide(slide_layout)

        if slide.shapes.title:
            slide.shapes.title.text = title

        for placeholder in slide.placeholders:
            if placeholder.placeholder_format.idx == 1:
                placeholder.text = content
                break

    presentation.save(resolved)
    return f"PowerPoint file created successfully at: {resolved}"
