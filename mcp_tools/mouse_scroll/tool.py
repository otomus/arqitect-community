"""Scroll the mouse wheel at an optional position."""

from typing import Optional


def run(clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> str:
    """Scroll the mouse wheel.

    @param clicks: Number of scroll clicks (positive=up, negative=down).
    @param x: Optional X coordinate to scroll at.
    @param y: Optional Y coordinate to scroll at.
    @returns Confirmation message with scroll details.
    """
    try:
        import pyautogui
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"

    if clicks == 0:
        return "Error: clicks must be non-zero"

    pyautogui.scroll(clicks, x=x, y=y)

    direction = "up" if clicks > 0 else "down"
    position = f" at ({x}, {y})" if x is not None and y is not None else ""
    return f"Scrolled {direction} {abs(clicks)} click(s){position}"
