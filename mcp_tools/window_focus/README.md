# window_focus

Focus and activate a window by its title. Uses platform-specific approaches: AppleScript on macOS, wmctrl on Linux, and pyautogui on Windows.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| title | string | yes | Title (or partial title) of the window to focus |

## Usage

```python
result = run("Terminal")
# Returns: "Focused window matching 'Terminal'"
```
