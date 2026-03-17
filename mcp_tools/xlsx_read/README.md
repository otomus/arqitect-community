# xlsx_read

Read data from an Excel XLSX file using openpyxl.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | yes | Path to the Excel file to read |
| sheet | string | no | Name of the sheet to read (defaults to active sheet) |

## Usage

```python
data = run("/path/to/spreadsheet.xlsx")
data = run("/path/to/spreadsheet.xlsx", sheet="Sheet2")
```

## Dependencies

- `openpyxl` — install with `pip install openpyxl`
