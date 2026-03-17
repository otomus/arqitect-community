# social_trending

Get trending topics on a social media platform.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| platform | string | Yes | Social media platform (twitter, mastodon) |
| region | string | No | Region code for localized trends (e.g. US, UK) |

## Environment Variables

- `TWITTER_API_KEY` - Bearer token for Twitter API
- `MASTODON_API_KEY` - Access token for Mastodon

## Usage

```python
result = run("twitter", region="US")
```
