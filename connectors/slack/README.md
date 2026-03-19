# Slack Connector

Bridges Slack workspace messages to the Arqitect brain via Redis, using [Bolt for JavaScript](https://slack.dev/bolt-js/) in **Socket Mode**.

## Prerequisites

- Node.js >= 18
- Redis running locally (default `localhost:6379`)
- A Slack workspace where you can create apps

## 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App** > **From scratch**.
2. Name the app (e.g. "Arqitect") and select your workspace.

## 2. Enable Socket Mode

1. In the app settings, go to **Socket Mode** and toggle it **on**.
2. Generate an **App-Level Token** with the `connections:write` scope. Copy it — this is your `app_token` (starts with `xapp-`).

## 3. Set Bot Token Scopes

Go to **OAuth & Permissions** > **Scopes** > **Bot Token Scopes** and add:

| Scope | Purpose |
|---|---|
| `app_mentions:read` | Detect @mentions of the bot |
| `channels:history` | Read messages in public channels |
| `channels:read` | List public channels |
| `chat:write` | Send messages |
| `files:read` | Download shared files |
| `files:write` | Upload files (images, audio, docs) |
| `groups:history` | Read messages in private channels |
| `groups:read` | List private channels |
| `im:history` | Read direct messages |
| `im:read` | List DM conversations |
| `mpim:history` | Read multi-party DMs |
| `reactions:write` | Add emoji reactions |
| `users:read` | Resolve display names |

## 4. Enable Events

Go to **Event Subscriptions** and toggle **on**. Under **Subscribe to bot events**, add:

- `message.channels`
- `message.groups`
- `message.im`
- `message.mpim`

## 5. Install the App

Go to **Install App** and click **Install to Workspace**. Copy the **Bot User OAuth Token** (starts with `xoxb-`).

Also copy the **Signing Secret** from **Basic Information** > **App Credentials**.

## 6. Configure the Connector

```bash
cp config-template.json config.json
```

Fill in `config.json`:

```json
{
  "bot_token": "xoxb-...",
  "app_token": "xapp-...",
  "signing_secret": "your-signing-secret",
  "bot_name": "Arqitect",
  "bot_aliases": [],
  "whitelisted_users": [],
  "whitelisted_groups": [],
  "monitor_groups": []
}
```

- **bot_token** — Bot User OAuth Token from step 5.
- **app_token** — App-Level Token from step 2.
- **signing_secret** — Signing Secret from step 5.
- **whitelisted_users** — Leave empty to allow all users, or provide Slack user IDs (e.g. `["U01ABC123"]`).
- **whitelisted_groups** — Leave empty to allow all channels, or provide channel IDs.
- **monitor_groups** — Channel IDs to observe (messages logged to Redis but not responded to).

## 7. Install and Run

```bash
npm install
npm start
```

## How It Works

- The bot connects via **Socket Mode** (WebSocket), so no public URL or ngrok is needed.
- In **channels/groups**, the bot only responds when @mentioned or when the message starts with the bot name.
- In **DMs**, the bot responds to every message.
- Incoming files (images, audio, video, documents) are downloaded and forwarded to the brain.
- Outgoing media is uploaded via `files.uploadV2`.

## Invite the Bot

After starting, invite the bot to channels where it should listen:

```
/invite @Arqitect
```
