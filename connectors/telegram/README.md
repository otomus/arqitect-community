# Telegram Connector

Bridges Telegram bot messages to the Sentient brain via Redis using [Telegraf](https://telegraf.js.org/).

This connector runs as a separate Node.js process alongside the Sentient core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency. Sentient's `start.sh` handles launching it automatically.

## Prerequisites

Create a bot with [@BotFather](https://t.me/BotFather) on Telegram and get your bot token. Add it to `config.json`.

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `bot_token` | Yes | Bot token from @BotFather |
| `bot_name` | No | Bot display name (default: "Sentient") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Telegram user IDs allowed to interact (empty = all) |
| `whitelisted_groups` | No | Telegram group IDs to process (empty = all) |
| `monitor_groups` | No | Group IDs to observe read-only |

## Access Control

1. Monitor groups: messages collected but never responded to
2. Group whitelist: only listed groups are processed (if set)
3. User whitelist: only listed user IDs can trigger the bot (if set)
4. In groups, messages must address the bot by name, @mention, or /command

## Supported Message Types

**Incoming**: text, photo, video, audio, voice, sticker, animation, document, location, contact, poll

**Outgoing**: text, photo, animation/GIF, audio/voice, sticker, document, location, contact, poll, card

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `telegram:monitor` | Forward monitor group messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
