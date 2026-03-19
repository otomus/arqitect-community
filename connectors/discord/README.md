# Discord Connector

Bridges Discord server and DM messages to the Arqitect brain via Redis using [discord.js](https://discord.js.org/).

This connector runs as a separate Node.js process alongside the Arqitect core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency. Arqitect's `start.sh` handles launching it automatically.

## Prerequisites

Create an application in the [Discord Developer Portal](https://discord.com/developers/applications), add a bot, and copy the bot token. Enable the **Message Content** privileged intent under Bot settings. Invite the bot to your server with the `bot` scope and `Send Messages`, `Read Message History`, `Add Reactions`, and `Attach Files` permissions.

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `bot_token` | Yes | Bot token from the Discord Developer Portal |
| `bot_name` | No | Bot display name (default: "Arqitect") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Discord user IDs allowed to interact (empty = all) |
| `whitelisted_groups` | No | Discord channel IDs to process (empty = all) |
| `monitor_groups` | No | Channel IDs to observe read-only |

## Access Control

1. Monitor groups: messages collected but never responded to
2. Group whitelist: only listed channels are processed (if set)
3. User whitelist: only listed user IDs can trigger the bot (if set)
4. In guild channels, messages must address the bot by name or @mention

## Supported Message Types

**Incoming**: text, image, video, audio, sticker, document (via attachments)

**Outgoing**: text, image, GIF, audio, sticker, document, reaction

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `discord:monitor` | Forward monitor channel messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
