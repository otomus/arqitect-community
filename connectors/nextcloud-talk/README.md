# Nextcloud Talk Connector

Bridges Nextcloud Talk chat messages to the Sentient brain via Redis using the [Nextcloud Talk OCS API](https://nextcloud-talk.readthedocs.io/).

This connector runs as a separate Node.js process alongside the Sentient core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency.

## Prerequisites

### 1. Create a Bot User in Nextcloud

1. Log in to your Nextcloud instance as an admin
2. Create a new user account for the bot (e.g., `sentient-bot`)
3. Optionally, generate an **App Password** under the user's Security settings for better security than using the account password directly

### 2. Add the Bot to Conversations

Add the bot user to the Talk rooms (conversations) you want it to participate in. The bot will automatically discover all rooms it belongs to.

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `nextcloud_url` | Yes | Nextcloud server URL (e.g., `https://cloud.example.com`) |
| `username` | Yes | Nextcloud bot user account username |
| `password` | Yes | Nextcloud bot user password or app token |
| `bot_name` | No | Bot display name (default: "Sentient") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Nextcloud user IDs allowed to interact (empty = all) |
| `whitelisted_groups` | No | Talk room tokens to process (empty = all) |
| `monitor_groups` | No | Room tokens to observe read-only |
| `poll_interval_ms` | No | Polling interval in milliseconds (default: 3000) |

## Access Control

1. Monitor groups: messages collected but never responded to
2. Group whitelist: only listed rooms are processed (if set)
3. User whitelist: only listed user IDs can trigger the bot (if set)
4. In group/public rooms, messages must @mention the bot or address it by name

## How It Works

The connector polls the Nextcloud Talk API at regular intervals to check for new messages across all rooms the bot user participates in. On startup, it records the latest message ID per room to avoid replaying history.

- **Incoming messages**: Polled via `GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}`
- **Outgoing messages**: Sent via `POST /ocs/v2.php/apps/spreed/api/v1/chat/{token}`
- **File sharing**: Files are uploaded to the bot user's Nextcloud storage via WebDAV, then shared into the Talk room using the OCS Share API
- **File downloads**: Shared files are downloaded via WebDAV from the share owner's file tree

## Supported Message Types

**Incoming**: text, image, document (via file shares)

**Outgoing**: text, image, document (via file shares), audio

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `nextcloud-talk:monitor` | Forward monitor room messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
