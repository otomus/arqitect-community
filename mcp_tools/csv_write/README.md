# csv_write

Write data to a CSV file using the Python standard library.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | yes | Output path for the CSV file |
| data | string | yes | JSON array of arrays representing rows and cells |
| delimiter | string | no | Column delimiter character (default: ",") |

## Usage

```python
result = run("/path/to/output.csv", '[["Name", "Age"], ["Alice", "30"]]')
result = run("/path/to/output.tsv", '[["Name", "Age"]]', delimiter="\t")
```

## Dependencies

None (uses Python standard library).
