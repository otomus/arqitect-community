# iMessage Connector (BlueBubbles)

Bridges iMessage to the Arqitect brain via Redis using a [BlueBubbles](https://bluebubbles.app) server.

This connector runs as a separate Node.js process alongside the Arqitect core. It communicates with the brain exclusively through Redis pub/sub.

## Requirements

- **BlueBubbles server** running on a Mac with Messages.app configured
- Server URL and password from your BlueBubbles setup

## How It Works

1. **Incoming**: Connects to BlueBubbles via WebSocket (Socket.IO) for real-time message delivery
2. **Outgoing**: Uses BlueBubbles REST API to send messages, attachments, and reactions
3. **Attachments**: Downloads media from BlueBubbles server, forwards to brain as base64

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `server_url` | Yes | BlueBubbles server URL (e.g. `http://localhost:1234`) |
| `password` | Yes | BlueBubbles server password |
| `bot_name` | No | Bot display name (default: "Arqitect") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Phone numbers or iMessage addresses allowed (empty = all) |
| `whitelisted_groups` | No | Group chat GUIDs to process (empty = all) |
| `monitor_groups` | No | Group chat GUIDs to observe read-only |

## Access Control

1. Own outgoing messages are always ignored
2. Monitor groups: messages collected but never responded to
3. Group whitelist: only listed groups are processed (if set)
4. User whitelist: only listed phone numbers / addresses can trigger the bot (if set)
5. In groups, messages must address the bot by name or alias

## Supported Message Types

**Incoming**: text, image, video, audio, document (via BlueBubbles attachment API)

**Outgoing**: text, image, document, reaction (tapback)

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `imessage-bluebubbles:monitor` | Forward monitor group messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |

## Troubleshooting

- **"Cannot reach server"**: Verify BlueBubbles is running and the URL/password are correct
- **No incoming messages**: Check that the WebSocket connection is established (look for "WebSocket connected" log)
- **Reactions not working**: BlueBubbles maps emoji to iMessage tapbacks; only standard tapback types are supported
