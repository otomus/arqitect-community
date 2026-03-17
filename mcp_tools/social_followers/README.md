# social_followers

Get follower count and information for a social media user.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| platform | string | Yes | Social media platform (twitter, mastodon) |
| username | string | Yes | Username to look up |

## Environment Variables

- `TWITTER_API_KEY` - Bearer token for Twitter API
- `MASTODON_API_KEY` - Access token for Mastodon
- `MASTODON_INSTANCE` - Mastodon instance URL (default: mastodon.social)

## Usage

```python
result = run("twitter", "elonmusk")
```
