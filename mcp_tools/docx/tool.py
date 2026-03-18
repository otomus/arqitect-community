"""Read or create DOCX files."""

import os


def run(path: str, operation: str, content: str = "", template: str = "") -> str:
    """Read text from a DOCX or create a new DOCX from text content.

    @param path: Path to the DOCX file.
    @param operation: 'read' to extract text, 'create' to write a new DOCX.
    @param content: Text content for the DOCX (required for create).
    @param template: Path to a DOCX template file (optional, create only).
    @returns Extracted text or confirmation message.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "read":
        return _read_docx(path)
    if operation == "create":
        return _create_docx(path, content, template)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'read' or 'create'.")


def _read_docx(file_path: str) -> str:
    """Extract all text content from a DOCX file."""
    try:
        import docx
    except ImportError:
        return ("error: python-docx is required but not installed. "
                "Install it with: pip install python-docx")

    resolved = os.path.abspath(file_path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f"DOCX file not found: {resolved}")

    document = docx.Document(resolved)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]

    if not any(paragraphs):
        return "No text content found in the DOCX file."

    return "\n".join(paragraphs)


def _create_docx(file_path: str, content: str, template: str) -> str:
    """Create a DOCX file containing the provided text content."""
    try:
        import docx
    except ImportError:
        return ("error: python-docx is required but not installed. "
                "Install it with: pip install python-docx")

    resolved = os.path.abspath(file_path)
    parent_dir = os.path.dirname(resolved)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    if template and os.path.exists(template):
        document = docx.Document(template)
    else:
        document = docx.Document()

    lines = content.split("\n")
    for line in lines:
        document.add_paragraph(line)

    document.save(resolved)
    return f"DOCX created successfully at: {resolved}"
