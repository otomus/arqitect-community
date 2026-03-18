"""Convert Markdown to HTML or PDF."""

import os
import re


FONT_NAME = "Helvetica"
FONT_NAME_BOLD = "Helvetica-Bold"
FONT_SIZE_BODY = 12
FONT_SIZE_H1 = 24
FONT_SIZE_H2 = 20
FONT_SIZE_H3 = 16
MARGIN = 72


def run(content: str, format: str) -> str:
    """Convert Markdown text to the specified output format.

    @param content: Markdown text to convert.
    @param format: 'html' or 'pdf'.
    @returns HTML string or confirmation message with PDF path.
    @throws ValueError: If the format is invalid.
    """
    if format == "html":
        return _to_html(content)
    if format == "pdf":
        return _to_pdf(content)
    raise ValueError(f"Invalid format '{format}'. Must be 'html' or 'pdf'.")


def _to_html(markdown_text: str) -> str:
    """Convert Markdown text into HTML."""
    try:
        import markdown
    except ImportError:
        return ("error: markdown is required but not installed. "
                "Install it with: pip install markdown")

    extensions = ["tables", "fenced_code", "toc"]
    return markdown.markdown(markdown_text, extensions=extensions)


def _to_pdf(markdown_text: str) -> str:
    """Convert Markdown text to a PDF file and return the path."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return ("error: reportlab is required but not installed. "
                "Install it with: pip install reportlab")

    output_path = os.path.abspath("markdown_output.pdf")
    page_width, page_height = A4
    pdf_canvas = canvas.Canvas(output_path, pagesize=A4)
    y_position = page_height - MARGIN

    lines = markdown_text.split("\n")

    for line in lines:
        font_name, font_size, text = _parse_line(line)

        if y_position < MARGIN:
            pdf_canvas.showPage()
            y_position = page_height - MARGIN

        pdf_canvas.setFont(font_name, font_size)
        pdf_canvas.drawString(MARGIN, y_position, text)
        y_position -= font_size + 4

    pdf_canvas.save()
    return f"PDF created from Markdown at: {output_path}"


def _parse_line(line: str) -> tuple[str, int, str]:
    """Determine font style and cleaned text for a Markdown line."""
    stripped = line.strip()

    if stripped.startswith("### "):
        return FONT_NAME_BOLD, FONT_SIZE_H3, stripped[4:]
    if stripped.startswith("## "):
        return FONT_NAME_BOLD, FONT_SIZE_H2, stripped[3:]
    if stripped.startswith("# "):
        return FONT_NAME_BOLD, FONT_SIZE_H1, stripped[2:]
    if stripped.startswith("- ") or stripped.startswith("* "):
        return FONT_NAME, FONT_SIZE_BODY, f"  \u2022 {stripped[2:]}"

    cleaned = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", stripped)
    return FONT_NAME, FONT_SIZE_BODY, cleaned
