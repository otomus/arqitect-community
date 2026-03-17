# markdown_to_pdf

Convert Markdown text to a PDF file using markdown and reportlab.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| markdown_text | string | yes | Markdown text to convert to PDF |
| output_path | string | yes | Output path for the generated PDF file |

## Usage

```python
result = run("# My Document\n\nSome content here.", "/path/to/output.pdf")
```

## Dependencies

- `reportlab` — install with `pip install reportlab`
