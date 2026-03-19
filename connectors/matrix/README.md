# Matrix Connector

Bridges Matrix room messages to the Arqitect brain via Redis using [matrix-js-sdk](https://github.com/matrix-org/matrix-js-sdk).

This connector runs as a separate Node.js process alongside the Arqitect core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency. Arqitect's `start.sh` handles launching it automatically.

## Prerequisites

You need a Matrix bot account with an access token. You can create one by:

1. Registering a new user on your homeserver (e.g. via Element or the registration API)
2. Logging in and retrieving the access token from Settings > Help & About > Access Token, or via the login API

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `homeserver_url` | Yes | Matrix homeserver URL (e.g. `https://matrix.org`) |
| `access_token` | Yes | Bot user access token |
| `user_id` | Yes | Bot user ID (e.g. `@bot:matrix.org`) |
| `bot_name` | No | Bot display name (default: "Arqitect") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Matrix user IDs allowed to interact (empty = all) |
| `whitelisted_groups` | No | Matrix room IDs to process (empty = all) |
| `monitor_groups` | No | Room IDs to observe read-only |

## Access Control

1. Monitor groups: messages collected but never responded to
2. Group whitelist: only listed rooms are processed (if set)
3. User whitelist: only listed user IDs can trigger the bot (if set)
4. In group rooms, messages must address the bot by name

## Group vs DM Detection

The connector determines whether a room is a DM or group by checking the `m.direct` account data on the homeserver. All rooms listed in `m.direct` are treated as DMs; all others are treated as groups.

## Supported Message Types

**Incoming**: text, image, video, audio, document (m.file)

**Outgoing**: text, image, audio, document, reaction (m.annotation)

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `matrix:monitor` | Forward monitor group messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
