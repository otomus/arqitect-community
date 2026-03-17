# table_format

Format data as a text table. Supports plain, grid, and pipe (Markdown) styles. Uses tabulate if available, with a built-in fallback.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | string | yes | JSON array of arrays (rows) |
| headers | string | no | JSON array of header strings |
| format | string | no | plain, grid, or pipe (default: grid) |

## Usage

```python
result = run(
    data='[["Alice", 30], ["Bob", 25]]',
    headers='["Name", "Age"]',
    format="grid"
)
```
