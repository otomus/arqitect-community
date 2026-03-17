# docx_create

Create a DOCX (Microsoft Word) file from text content using python-docx.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | yes | Output path for the DOCX file |
| content | string | yes | Text content to write into the DOCX file |

## Usage

```python
result = run("/path/to/output.docx", "First paragraph\nSecond paragraph")
```

## Dependencies

- `python-docx` — install with `pip install python-docx`
