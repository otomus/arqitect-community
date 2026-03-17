# mouse_scroll

Scroll the mouse wheel at an optional screen position.

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| clicks | integer | yes | - | Scroll clicks (positive=up, negative=down) |
| x | integer | no | - | X coordinate to scroll at |
| y | integer | no | - | Y coordinate to scroll at |

## Usage

```python
result = run(3)
# Returns: "Scrolled up 3 click(s)"

result = run(-5, x=400, y=300)
# Returns: "Scrolled down 5 click(s) at (400, 300)"
```
