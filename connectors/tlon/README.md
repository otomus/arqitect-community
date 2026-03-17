# Tlon Messenger Connector

Bridges Tlon peer-to-peer chat messages to the Sentient brain via Redis using the [@urbit/http-api](https://www.npmjs.com/package/@urbit/http-api).

This connector runs as a separate Node.js process alongside the Sentient core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency. Sentient's `start.sh` handles launching it automatically.

## Prerequisites

You need a running Urbit ship (e.g. a planet or fakezod) with Tlon installed. Get your ship's access code by running `+code` in the Dojo.

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `ship_url` | Yes | Urbit ship URL (e.g. `http://localhost:8080`) |
| `ship_code` | Yes | Ship access code from `+code` |
| `bot_name` | No | Bot display name (default: "Sentient") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Urbit ship names allowed to interact (empty = all) |
| `whitelisted_groups` | No | Tlon group/channel paths to process (empty = all) |
| `monitor_groups` | No | Group/channel paths to observe read-only |

## Access Control

1. Monitor groups: messages collected but never responded to
2. Group whitelist: only listed groups are processed (if set)
3. User whitelist: only listed ship names can trigger the bot (if set)
4. In groups, messages must address the bot by name prefix

## Supported Message Types

**Incoming**: text

**Outgoing**: text

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `tlon:monitor` | Forward monitor group messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
