# xlsx_create

Create an Excel XLSX file from JSON data using openpyxl.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | yes | Output path for the Excel file |
| data | string | yes | JSON array of arrays representing rows and cells |

## Usage

```python
result = run("/path/to/output.xlsx", '[["Name", "Age"], ["Alice", 30]]')
```

## Dependencies

- `openpyxl` — install with `pip install openpyxl`
