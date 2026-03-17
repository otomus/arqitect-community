# social_like

Like a social media post on a specified platform (Twitter, Mastodon).

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| platform | string | Yes | Social media platform (twitter, mastodon) |
| post_id | string | Yes | Unique identifier of the post to like |

## Environment Variables

- `TWITTER_API_KEY` - Bearer token for Twitter API
- `MASTODON_API_KEY` - Access token for Mastodon
- `MASTODON_INSTANCE` - Mastodon instance URL (default: mastodon.social)

## Usage

```python
result = run("twitter", "1234567890")
```
