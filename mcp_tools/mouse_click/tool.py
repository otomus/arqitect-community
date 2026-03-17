"""Click the mouse at specified screen coordinates."""


def run(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """Click the mouse at the given screen coordinates.

    @param x: X coordinate on screen.
    @param y: Y coordinate on screen.
    @param button: Mouse button to click (left, right, middle).
    @param clicks: Number of clicks to perform.
    @returns Confirmation message with click details.
    """
    try:
        import pyautogui
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"

    valid_buttons = ("left", "right", "middle")
    if button not in valid_buttons:
        return f"Error: button must be one of {valid_buttons}, got '{button}'"

    if clicks < 1:
        return "Error: clicks must be at least 1"

    pyautogui.click(x=x, y=y, button=button, clicks=clicks)
    return f"Clicked {button} button {clicks} time(s) at ({x}, {y})"
