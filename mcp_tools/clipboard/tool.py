"""Read from or write to the system clipboard."""


def run(operation: str, content: str = "") -> str:
    """Read or write the system clipboard.

    @param operation: 'read' to get clipboard text, 'write' to set it.
    @param content: Text to write (required for write).
    @returns Clipboard contents or confirmation message.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "read":
        return _read()
    if operation == "write":
        return _write(content)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'read' or 'write'.")


def _read() -> str:
    """Read text from the system clipboard."""
    try:
        import pyperclip
    except ImportError:
        return "Error: pyperclip is not installed. Run: pip install pyperclip"

    try:
        text = pyperclip.paste()
    except pyperclip.PyperclipException as exc:
        return f"Error: could not read clipboard: {exc}"

    if not text:
        return "Clipboard is empty"

    return f"Clipboard contents:\n{text}"


def _write(text: str) -> str:
    """Write text to the system clipboard."""
    try:
        import pyperclip
    except ImportError:
        return "Error: pyperclip is not installed. Run: pip install pyperclip"

    if not text:
        return "Error: text must not be empty"

    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as exc:
        return f"Error: could not write to clipboard: {exc}"

    return f"Copied {len(text)} character(s) to clipboard"
