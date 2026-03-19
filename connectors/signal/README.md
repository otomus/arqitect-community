# Signal Connector

Bridges Signal messages to the Arqitect brain via Redis using the [signal-cli REST API](https://github.com/bbernhard/signal-cli-rest-api).

This connector runs as a separate Node.js process alongside the Arqitect core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency.

## Prerequisites

You need a running instance of `signal-cli-rest-api`. The recommended approach is Docker:

```bash
docker run -d \
  --name signal-cli-rest-api \
  -p 8080:8080 \
  -v $HOME/.local/share/signal-cli:/home/.local/share/signal-cli \
  -e MODE=normal \
  bbernhard/signal-cli-rest-api:latest
```

### Register or Link a Phone Number

**Option A: Register a new number**

```bash
# Request verification code via SMS
curl -X POST "http://localhost:8080/v1/register/+1234567890"

# Verify with the code you received
curl -X POST "http://localhost:8080/v1/register/+1234567890/verify/123456"
```

**Option B: Link to an existing Signal account**

```bash
# Get a QR code link URI
curl "http://localhost:8080/v1/qrcodelink?device_name=arqitect-bot"
```

Scan the QR code from your Signal app (Settings > Linked Devices > Link New Device).

### Verify the API is Running

```bash
curl "http://localhost:8080/v1/about"
```

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `signal_cli_url` | Yes | URL of the signal-cli REST API (e.g. `http://localhost:8080`) |
| `phone_number` | Yes | Registered Signal phone number (e.g. `+1234567890`) |
| `bot_name` | No | Bot display name (default: "Arqitect") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Phone numbers allowed to interact (empty = all) |
| `whitelisted_groups` | No | Signal group IDs to process (empty = all) |
| `monitor_groups` | No | Group IDs to observe read-only |

## Access Control

1. Monitor groups: messages collected but never responded to
2. Group whitelist: only listed groups are processed (if set)
3. User whitelist: only listed phone numbers can trigger the bot (if set)
4. In groups, messages must address the bot by name prefix

## Supported Message Types

**Incoming**: text, image, video, audio, document, sticker, contact

**Outgoing**: text, image, audio, document, sticker, reaction

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Publish | `signal:monitor` | Forward monitor group messages |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |

## How It Works

The connector polls the signal-cli REST API (`GET /v1/receive/{number}`) on a 2-second interval for new messages. Outgoing messages are sent via `POST /v2/send` with optional base64-encoded attachments. No additional npm dependencies beyond `redis` are needed since all signal-cli communication uses plain HTTP.
