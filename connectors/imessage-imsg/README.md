# iMessage Connector (imsg)

Bridges iMessage on macOS to the Arqitect brain via Redis using the native Messages SQLite database and AppleScript.

This connector runs as a separate Node.js process alongside the Arqitect core. It communicates with the brain exclusively through Redis pub/sub.

## Requirements

- **macOS** with Messages.app signed in to iMessage
- **Full Disk Access** granted to the terminal or process running this connector (System Settings > Privacy & Security > Full Disk Access) — required to read `~/Library/Messages/chat.db`
- **Automation permission** for AppleScript to control Messages.app (granted on first send)

## How It Works

1. **Incoming**: Polls `~/Library/Messages/chat.db` (SQLite) for new message rows at a configurable interval
2. **Outgoing**: Uses `osascript` (AppleScript) to send messages through Messages.app

## Configuration

Copy `config-template.json` to `config.json` and adjust as needed.

| Field | Required | Description |
|-------|----------|-------------|
| `bot_name` | No | Bot display name (default: "Arqitect") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Phone numbers or iMessage addresses allowed (empty = all) |
| `whitelisted_groups` | No | Group chat names to process (empty = all) |
| `monitor_groups` | No | Group chat names to observe read-only |
| `poll_interval_ms` | No | Polling interval in milliseconds (default: 2000) |

## Access Control

1. Own outgoing messages are always ignored
2. Monitor groups: messages collected but never responded to
3. Group whitelist: only listed groups are processed (if set)
4. User whitelist: only listed phone numbers / addresses can trigger the bot (if set)
5. In groups, messages must address the bot by name or alias

## Supported Message Types

**Incoming**: text, image, audio, document (via chat.db attachments)

**Outgoing**: text, image (via AppleScript)

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `imessage-imsg:monitor` | Forward monitor group messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |

## Troubleshooting

- **"Cannot open chat.db"**: Grant Full Disk Access to your terminal app
- **Messages not sending**: Allow Automation access for osascript to Messages.app when prompted
- **Missed messages**: Reduce `poll_interval_ms` in config.json for faster polling
