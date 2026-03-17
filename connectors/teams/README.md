# Microsoft Teams Connector

Bridges Microsoft Teams bot messages to the Sentient brain via Redis using the [Bot Framework SDK](https://github.com/microsoft/botframework-sdk).

This connector runs as a separate Node.js process alongside the Sentient core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency.

## Prerequisites

### 1. Register a Bot in Azure

1. Go to the [Azure Portal](https://portal.azure.com)
2. Create a new **Azure Bot** resource (or **Bot Channels Registration**)
3. Note the **Microsoft App ID** generated during creation
4. Under **Certificates & secrets**, create a new client secret — this is your **App Password**
5. Under **Channels**, enable the **Microsoft Teams** channel

### 2. Set the Messaging Endpoint

In the Azure Bot configuration, set the messaging endpoint to:

```
https://<your-public-domain>/api/messages
```

The connector listens on port 3978 by default. You need a publicly accessible URL — use a reverse proxy (nginx, Caddy) or a tunneling tool (ngrok) during development:

```bash
ngrok http 3978
```

Then set the ngrok HTTPS URL as your messaging endpoint in Azure.

### 3. Install the Bot in Teams

1. In Azure Portal, go to your Bot resource > Channels > Microsoft Teams
2. Click "Open in Teams" to add the bot to your Teams workspace
3. Alternatively, create a Teams App Package with your bot's App ID and sideload it

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `app_id` | Yes | Microsoft App ID from Azure Bot registration |
| `app_password` | Yes | Microsoft App password/client secret |
| `bot_name` | No | Bot display name (default: "Sentient") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Azure AD user IDs allowed to interact (empty = all) |
| `whitelisted_groups` | No | Teams channel IDs to process (empty = all) |
| `monitor_groups` | No | Channel IDs to observe read-only |
| `port` | No | HTTP port for incoming webhooks (default: 3978) |

## Access Control

1. Monitor groups: messages collected but never responded to
2. Group whitelist: only listed channels/group chats are processed (if set)
3. User whitelist: only listed Azure AD user IDs can trigger the bot (if set)
4. In channels/group chats, messages must @mention the bot or address it by name

## Supported Message Types

**Incoming**: text, image, document

**Outgoing**: text, image, document, Adaptive Card

## Architecture

- Uses `restify` to run an HTTP server that receives Bot Framework activities
- Stores conversation references for proactive messaging (sending brain responses back)
- The `/api/messages` endpoint processes all incoming activities
- The `/health` endpoint returns connector status

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `teams:monitor` | Forward monitor channel messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
