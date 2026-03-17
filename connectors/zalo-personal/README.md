# Zalo Personal Connector

Bridges personal Zalo messages to the Sentient brain via Redis using [zca-js](https://github.com/nicksmd/zca-js) (Zalo Client API).

This connector runs as a separate Node.js process alongside the Sentient core. It communicates with the brain exclusively through Redis pub/sub. Sentient's `start.sh` handles launching it automatically.

## First Run

On first launch, a QR code URL is displayed in the terminal. Open it in your browser and scan with the Zalo mobile app. The session persists in `.zalo_credentials.json` so subsequent runs reconnect automatically.

## Configuration

Copy `config-template.json` to `config.json` and adjust as needed.

| Field | Required | Description |
|-------|----------|-------------|
| `bot_name` | No | Bot display name (default: "Sentient") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Zalo user IDs allowed to interact (empty = all) |
| `whitelisted_groups` | No | Zalo group IDs to process (empty = all) |
| `monitor_groups` | No | Group IDs to observe read-only |

## Access Control

1. Monitor groups: messages collected but never responded to
2. Group whitelist: only listed groups are processed (if set)
3. User whitelist: only listed Zalo user IDs can trigger the bot (if set)
4. In groups, messages must address the bot by name or alias

## Supported Message Types

**Incoming**: text, image, document/file

**Outgoing**: text, image

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `zalo-personal:monitor` | Forward monitor group messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
