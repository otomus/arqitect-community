# youtube_search

Search YouTube videos by query using the YouTube Data API v3.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | string | Yes | Search query |
| max_results | int | No | Maximum results to return (default 5) |

## Environment Variables

- `YOUTUBE_API_KEY` - Google API key with YouTube Data API enabled

## Usage

```python
result = run("python tutorial", max_results=3)
```
