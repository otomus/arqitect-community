# chart_create

Create chart images (bar, line, pie, scatter) from JSON data using matplotlib.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| chart_type | string | yes | Chart type: bar, line, pie, or scatter |
| data | string | yes | JSON with `labels` and `values` arrays |
| output_path | string | yes | File path for the output image |
| title | string | no | Optional chart title |

## Usage

```python
result = run(
    chart_type="bar",
    data='{"labels": ["Q1", "Q2", "Q3"], "values": [100, 150, 200]}',
    output_path="sales.png",
    title="Quarterly Sales"
)
```
