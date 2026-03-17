# calendar_events

List calendar events for a given date range. On macOS, reads from the native Calendar app.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| date | string | No | Start date in ISO format (defaults to today) |
| days | int | No | Number of days to look ahead (default 7) |

## Usage

```python
result = run(date="2026-03-17", days=3)
```
