# pdf_create

Create a PDF file from text content using reportlab.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | yes | Output path for the PDF file |
| content | string | yes | Text content to write into the PDF |

## Usage

```python
result = run("/path/to/output.pdf", "Hello, World!\nSecond line here.")
```

## Dependencies

- `reportlab` — install with `pip install reportlab`
