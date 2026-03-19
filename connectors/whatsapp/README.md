# WhatsApp Connector

Bridges WhatsApp messages to the Arqitect brain via Redis using [Baileys](https://github.com/WhiskeySockets/Baileys).

This connector runs as a separate Node.js process alongside the Arqitect core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency. Arqitect's `start.sh` handles launching it automatically.

## First Run

On first launch, a QR code is displayed in the terminal. Scan it with WhatsApp (Linked Devices > Link a Device). The session persists in `auth_store/` so subsequent runs reconnect automatically.

## Configuration

Copy `config-template.json` to `config.json` and adjust as needed.

| Field | Required | Description |
|-------|----------|-------------|
| `bot_name` | No | Bot display name (default: "Arqitect") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Phone numbers allowed to interact (empty = all) |
| `whitelisted_groups` | No | Group IDs to process (empty = all) |
| `monitor_groups` | No | Group IDs to observe read-only |

## Access Control

1. Status broadcasts are always ignored
2. Monitor groups: messages collected but never responded to
3. Group whitelist: only listed groups are processed (if set)
4. User whitelist: only listed phone numbers can trigger the bot (if set)
5. In groups, messages must address the bot by name or alias

## Supported Message Types

**Incoming**: text, image, video, audio, sticker, document, location, contact, poll

**Outgoing**: text, image, GIF, audio/voice note, sticker, document, location, contact, poll, reaction, card

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `whatsapp:monitor` | Forward monitor group messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
