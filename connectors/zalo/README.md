# Zalo OA Connector

Bridges Zalo Official Account messages to the Sentient brain via Redis using the [Zalo OA API v3](https://developers.zalo.me/docs/official-account).

This connector runs as a separate Node.js process alongside the Sentient core. It communicates with the brain exclusively through Redis pub/sub. Sentient's `start.sh` handles launching it automatically.

## Prerequisites

1. Create a Zalo Official Account at [oa.zalo.me](https://oa.zalo.me)
2. Register an app at [developers.zalo.me](https://developers.zalo.me) and link it to your OA
3. Obtain your `app_id`, `secret_key`, `access_token`, and `refresh_token`
4. Configure the webhook URL in the Zalo developer portal to point at your server's `/webhook` endpoint

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `access_token` | Yes | Zalo OA access token |
| `refresh_token` | Yes | Zalo OA refresh token (auto-renewed) |
| `app_id` | Yes | Zalo app ID |
| `secret_key` | Yes | Zalo app secret key |
| `webhook_port` | No | Port for webhook callbacks (default: 3200) |
| `bot_name` | No | Bot display name (default: "Sentient") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Zalo user IDs allowed to interact (empty = all) |

## Token Auto-Renewal

Zalo OA access tokens expire after 24 hours. The connector automatically refreshes the token using the refresh token and persists updated tokens to `.zalo_tokens.json` so restarts are seamless.

## Access Control

1. User whitelist: only listed Zalo user IDs can trigger the bot (if set)
2. All conversations are 1:1 (Zalo OA API has no group concept)

## Supported Message Types

**Incoming**: text, image, document/file

**Outgoing**: text, image (upload then send), document (upload then send)

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
