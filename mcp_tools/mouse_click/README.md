# mouse_click

Click the mouse at specified screen coordinates.

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| x | integer | yes | - | X coordinate on screen |
| y | integer | yes | - | Y coordinate on screen |
| button | string | no | "left" | Mouse button (left, right, middle) |
| clicks | integer | no | 1 | Number of clicks |

## Usage

```python
result = run(100, 200)
# Returns: "Clicked left button 1 time(s) at (100, 200)"

result = run(500, 300, button="right", clicks=2)
# Returns: "Clicked right button 2 time(s) at (500, 300)"
```
