# calendar_create_event

Create a new calendar event. On macOS, adds the event to the native Calendar app.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| title | string | Yes | Event title |
| start | string | Yes | Start datetime in ISO format |
| end | string | Yes | End datetime in ISO format |
| description | string | No | Event description or notes |

## Usage

```python
result = run("Team Standup", "2026-03-18T09:00:00", "2026-03-18T09:30:00")
```
