# keyboard_press

Press a key or key combination on the keyboard.

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| key | string | yes | - | Key to press (e.g. enter, tab, a, f1) |
| modifiers | string | no | "" | Comma-separated modifier keys (e.g. ctrl,shift) |

## Usage

```python
result = run("enter")
# Returns: "Pressed key: enter"

result = run("c", modifiers="ctrl")
# Returns: "Pressed key combination: ctrl+c"

result = run("s", modifiers="ctrl,shift")
# Returns: "Pressed key combination: ctrl+shift+s"
```
