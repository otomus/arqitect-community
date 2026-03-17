"""Read the current contents of the system clipboard."""


def run() -> str:
    """Read text from the system clipboard.

    @returns The current clipboard text, or an error message.
    """
    try:
        import pyperclip
    except ImportError:
        return "Error: pyperclip is not installed. Run: pip install pyperclip"

    try:
        content = pyperclip.paste()
    except pyperclip.PyperclipException as exc:
        return f"Error: could not read clipboard: {exc}"

    if not content:
        return "Clipboard is empty"

    return f"Clipboard contents:\n{content}"
