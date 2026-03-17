# pptx_create

Create a PowerPoint PPTX file from JSON slide data using python-pptx.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | yes | Output path for the PowerPoint file |
| slides | string | yes | JSON array of slide objects with 'title' and 'content' fields |

## Usage

```python
slides_json = '[{"title": "Intro", "content": "Welcome to the presentation"}]'
result = run("/path/to/output.pptx", slides_json)
```

## Dependencies

- `python-pptx` — install with `pip install python-pptx`
