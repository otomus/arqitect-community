"""Move the mouse cursor to specified screen coordinates."""


def run(x: int, y: int, duration: float = 0.0) -> str:
    """Move the mouse cursor to the given screen coordinates.

    @param x: X coordinate to move to.
    @param y: Y coordinate to move to.
    @param duration: Duration of the movement in seconds.
    @returns Confirmation message with target coordinates.
    """
    try:
        import pyautogui
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"

    if duration < 0:
        return "Error: duration must be non-negative"

    pyautogui.moveTo(x=x, y=y, duration=duration)
    return f"Mouse moved to ({x}, {y})"
