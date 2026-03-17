"""Focus and activate a window by its title."""

import platform
import subprocess


def _focus_macos(title: str) -> str:
    """Focus a window on macOS using AppleScript."""
    script = f'''
    tell application "System Events"
        set targetProcess to first application process whose visible is true and (name contains "{title}" or (exists (first window whose name contains "{title}")))
        set frontmost of targetProcess to true
    end tell
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return f"Error: could not focus window matching '{title}'"
    return f"Focused window matching '{title}'"


def _focus_linux(title: str) -> str:
    """Focus a window on Linux using wmctrl."""
    result = subprocess.run(
        ["wmctrl", "-a", title],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return f"Error: could not focus window matching '{title}'"
    return f"Focused window matching '{title}'"


def _focus_windows(title: str) -> str:
    """Focus a window on Windows using pyautogui."""
    try:
        import pyautogui
        windows = [w for w in pyautogui.getAllWindows() if title.lower() in w.title.lower()]
        if not windows:
            return f"Error: no window found matching '{title}'"
        windows[0].activate()
        return f"Focused window matching '{title}'"
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"


def run(title: str) -> str:
    """Focus and activate a window by its title.

    @param title: Title or partial title of the window to focus.
    @returns Confirmation message or error if window not found.
    """
    if not title:
        return "Error: title must not be empty"

    system = platform.system()

    if system == "Darwin":
        return _focus_macos(title)
    elif system == "Linux":
        return _focus_linux(title)
    elif system == "Windows":
        return _focus_windows(title)
    else:
        return f"Error: unsupported platform '{system}'"
