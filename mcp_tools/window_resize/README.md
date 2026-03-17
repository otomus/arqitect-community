# window_resize

Resize a window by its title to specified dimensions. Uses platform-specific approaches: AppleScript on macOS, wmctrl on Linux, and pyautogui on Windows.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| title | string | yes | Title (or partial title) of the window to resize |
| width | integer | yes | Target width in pixels |
| height | integer | yes | Target height in pixels |

## Usage

```python
result = run("Terminal", 1024, 768)
# Returns: "Resized window 'Terminal' to 1024x768"
```
