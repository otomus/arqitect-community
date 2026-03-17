# news_fetch

Fetch news articles matching a search query using NewsAPI.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | string | Yes | Search query for news articles |
| count | int | No | Number of articles to return (default 5) |

## Environment Variables

- `NEWS_API_KEY` - API key for newsapi.org

## Usage

```python
result = run("artificial intelligence", count=3)
```
