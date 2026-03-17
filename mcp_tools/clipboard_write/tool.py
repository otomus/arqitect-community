"""Write text to the system clipboard."""


def run(text: str) -> str:
    """Write the given text to the system clipboard.

    @param text: Text to write to the clipboard.
    @returns Confirmation message with the number of characters written.
    """
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
