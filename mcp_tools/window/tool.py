"""List, focus, or resize desktop windows."""

import platform
import subprocess
from typing import List


def run(operation: str, window_id: str = "", w: str = "", h: str = "") -> str:
    """Manage desktop windows: list all, focus one, or resize one.

    @param operation: 'list' to enumerate windows, 'focus' to activate, 'resize' to change dimensions.
    @param window_id: Window title or partial title (required for focus and resize).
    @param w: Target width in pixels (required for resize).
    @param h: Target height in pixels (required for resize).
    @returns Window list, confirmation, or error message.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "list":
        return _list_windows()
    if operation == "focus":
        return _focus_window(window_id)
    if operation == "resize":
        return _resize_window(window_id, int(w), int(h))
    raise ValueError(f"Invalid operation '{operation}'. Must be 'list', 'focus', or 'resize'.")


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def _list_windows() -> str:
    """List all open windows on the desktop."""
    system = platform.system()

    if system == "Darwin":
        windows = _list_windows_macos()
    elif system == "Linux":
        windows = _list_windows_linux()
    elif system == "Windows":
        windows = _list_windows_windows()
    else:
        return f"Error: unsupported platform '{system}'"

    if not windows:
        return "No windows found"

    header = f"Found {len(windows)} window(s):\n"
    return header + "\n".join(f"- {w}" for w in windows)


def _list_windows_macos() -> List[str]:
    """List window titles on macOS using AppleScript."""
    script = (
        'tell application "System Events" to get the name of every window '
        "of every application process whose visible is true"
    )
    result = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return []
    raw = result.stdout.strip()
    if not raw:
        return []
    return [w.strip() for w in raw.split(",") if w.strip()]


def _list_windows_linux() -> List[str]:
    """List window titles on Linux using wmctrl."""
    result = subprocess.run(
        ["wmctrl", "-l"], capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return []
    windows = []
    for line in result.stdout.strip().splitlines():
        parts = line.split(None, 3)
        if len(parts) >= 4:
            windows.append(parts[3])
    return windows


def _list_windows_windows() -> List[str]:
    """List window titles on Windows using pyautogui."""
    try:
        import pyautogui
        return [w.title for w in pyautogui.getAllWindows() if w.title.strip()]
    except (ImportError, AttributeError):
        return []


# ---------------------------------------------------------------------------
# Focus
# ---------------------------------------------------------------------------

def _focus_window(title: str) -> str:
    """Focus and activate a window by its title."""
    if not title:
        return "Error: title must not be empty"

    system = platform.system()
    if system == "Darwin":
        return _focus_macos(title)
    if system == "Linux":
        return _focus_linux(title)
    if system == "Windows":
        return _focus_windows_os(title)
    return f"Error: unsupported platform '{system}'"


def _focus_macos(title: str) -> str:
    script = (
        f'tell application "System Events"\n'
        f'    set targetProcess to first application process whose visible is true '
        f'and (name contains "{title}" or (exists (first window whose name contains "{title}")))\n'
        f'    set frontmost of targetProcess to true\n'
        f'end tell'
    )
    result = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return f"Error: could not focus window matching '{title}'"
    return f"Focused window matching '{title}'"


def _focus_linux(title: str) -> str:
    result = subprocess.run(
        ["wmctrl", "-a", title], capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return f"Error: could not focus window matching '{title}'"
    return f"Focused window matching '{title}'"


def _focus_windows_os(title: str) -> str:
    try:
        import pyautogui
        windows = [w for w in pyautogui.getAllWindows() if title.lower() in w.title.lower()]
        if not windows:
            return f"Error: no window found matching '{title}'"
        windows[0].activate()
        return f"Focused window matching '{title}'"
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"


# ---------------------------------------------------------------------------
# Resize
# ---------------------------------------------------------------------------

def _resize_window(title: str, width: int, height: int) -> str:
    """Resize a window to the specified dimensions."""
    if not title:
        return "Error: title must not be empty"
    if width <= 0 or height <= 0:
        return "Error: width and height must be positive"

    system = platform.system()
    if system == "Darwin":
        return _resize_macos(title, width, height)
    if system == "Linux":
        return _resize_linux(title, width, height)
    if system == "Windows":
        return _resize_windows_os(title, width, height)
    return f"Error: unsupported platform '{system}'"


def _resize_macos(title: str, width: int, height: int) -> str:
    script = (
        f'tell application "System Events"\n'
        f'    set targetProcess to first application process whose visible is true '
        f'and (name contains "{title}" or (exists (first window whose name contains "{title}")))\n'
        f'    tell targetProcess\n'
        f'        set size of first window to {{{width}, {height}}}\n'
        f'    end tell\n'
        f'end tell'
    )
    result = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return f"Error: could not resize window matching '{title}'"
    return f"Resized window '{title}' to {width}x{height}"


def _resize_linux(title: str, width: int, height: int) -> str:
    result = subprocess.run(
        ["wmctrl", "-r", title, "-e", f"0,-1,-1,{width},{height}"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return f"Error: could not resize window matching '{title}'"
    return f"Resized window '{title}' to {width}x{height}"


def _resize_windows_os(title: str, width: int, height: int) -> str:
    try:
        import pyautogui
        windows = [w for w in pyautogui.getAllWindows() if title.lower() in w.title.lower()]
        if not windows:
            return f"Error: no window found matching '{title}'"
        windows[0].resizeTo(width, height)
        return f"Resized window '{title}' to {width}x{height}"
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"
