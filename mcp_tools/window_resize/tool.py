"""Resize a window by its title to specified dimensions."""

import platform
import subprocess


def _resize_macos(title: str, width: int, height: int) -> str:
    """Resize a window on macOS using AppleScript."""
    script = f'''
    tell application "System Events"
        set targetProcess to first application process whose visible is true and (name contains "{title}" or (exists (first window whose name contains "{title}")))
        tell targetProcess
            set size of first window to {{{width}, {height}}}
        end tell
    end tell
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return f"Error: could not resize window matching '{title}'"
    return f"Resized window '{title}' to {width}x{height}"


def _resize_linux(title: str, width: int, height: int) -> str:
    """Resize a window on Linux using wmctrl."""
    result = subprocess.run(
        ["wmctrl", "-r", title, "-e", f"0,-1,-1,{width},{height}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return f"Error: could not resize window matching '{title}'"
    return f"Resized window '{title}' to {width}x{height}"


def _resize_windows(title: str, width: int, height: int) -> str:
    """Resize a window on Windows using pyautogui."""
    try:
        import pyautogui
        windows = [w for w in pyautogui.getAllWindows() if title.lower() in w.title.lower()]
        if not windows:
            return f"Error: no window found matching '{title}'"
        windows[0].resizeTo(width, height)
        return f"Resized window '{title}' to {width}x{height}"
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"


def run(title: str, width: int, height: int) -> str:
    """Resize a window to the specified dimensions.

    @param title: Title or partial title of the window to resize.
    @param width: Target width in pixels.
    @param height: Target height in pixels.
    @returns Confirmation message or error if window not found.
    """
    if not title:
        return "Error: title must not be empty"

    if width <= 0 or height <= 0:
        return "Error: width and height must be positive"

    system = platform.system()

    if system == "Darwin":
        return _resize_macos(title, width, height)
    elif system == "Linux":
        return _resize_linux(title, width, height)
    elif system == "Windows":
        return _resize_windows(title, width, height)
    else:
        return f"Error: unsupported platform '{system}'"
