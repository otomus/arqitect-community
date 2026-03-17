"""Press a key or key combination on the keyboard."""


def run(key: str, modifiers: str = "") -> str:
    """Press a key, optionally with modifier keys held down.

    @param key: Key to press (e.g. enter, tab, a, f1).
    @param modifiers: Comma-separated modifier keys (e.g. ctrl,shift).
    @returns Confirmation message with the key combination pressed.
    """
    try:
        import pyautogui
    except ImportError:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"

    if not key:
        return "Error: key must not be empty"

    if modifiers:
        modifier_list = [m.strip() for m in modifiers.split(",") if m.strip()]
        combo = modifier_list + [key]
        pyautogui.hotkey(*combo)
        combo_str = "+".join(combo)
        return f"Pressed key combination: {combo_str}"

    pyautogui.press(key)
    return f"Pressed key: {key}"
