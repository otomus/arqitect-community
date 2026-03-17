# mouse_move

Move the mouse cursor to specified screen coordinates.

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| x | integer | yes | - | X coordinate to move to |
| y | integer | yes | - | Y coordinate to move to |
| duration | number | no | 0.0 | Duration of movement in seconds |

## Usage

```python
result = run(400, 300)
# Returns: "Mouse moved to (400, 300)"

result = run(800, 600, duration=0.5)
# Returns: "Mouse moved to (800, 600)"
```
