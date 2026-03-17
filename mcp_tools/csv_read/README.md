# csv_read

Read data from a CSV file using the Python standard library.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | yes | Path to the CSV file to read |
| delimiter | string | no | Column delimiter character (default: ",") |

## Usage

```python
data = run("/path/to/data.csv")
data = run("/path/to/data.tsv", delimiter="\t")
```

## Dependencies

None (uses Python standard library).
