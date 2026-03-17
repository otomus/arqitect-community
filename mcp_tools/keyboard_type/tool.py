"""Type a text string using keyboard simulation."""


def run(text: str, interval: float = 0.0) -> str:
    """Type the given text string via simulated keystrokes.

    @param text: Text string to type.
    @param interval: Seconds between each keystroke.
    @returns Confirmation message with the number of characters typed.
    """
    try:
        import pyautogui
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"

    if not text:
        return "Error: text must not be empty"

    if interval < 0:
        return "Error: interval must be non-negative"

    pyautogui.typewrite(text, interval=interval)
    return f"Typed {len(text)} character(s)"
