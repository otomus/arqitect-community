"""List all open windows on the desktop."""

import platform
import subprocess
from typing import List


def _list_windows_macos() -> List[str]:
    """List window titles on macOS using AppleScript."""
    script = (
        'tell application "System Events" to get the name of every window '
        "of every application process whose visible is true"
    )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
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
        ["wmctrl", "-l"],
        capture_output=True,
        text=True,
        timeout=10,
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


def run() -> str:
    """List all open windows on the desktop.

    @returns Newline-separated list of window titles, or an error message.
    """
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
