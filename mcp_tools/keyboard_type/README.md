# keyboard_type

Type a text string using keyboard simulation.

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| text | string | yes | - | Text string to type |
| interval | number | no | 0.0 | Seconds between each keystroke |

## Usage

```python
result = run("hello world")
# Returns: "Typed 11 character(s)"

result = run("abc", interval=0.05)
# Returns: "Typed 3 character(s)"
```
