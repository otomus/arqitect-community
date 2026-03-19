# WebChat Connector

Browser-based chat UI bridging to the Arqitect brain via Redis and WebSocket using [Express](https://expressjs.com/) and [ws](https://github.com/websockets/ws).

This connector runs as a separate Node.js process alongside the Arqitect core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency. Arqitect's `start.sh` handles launching it automatically.

## Prerequisites

No external accounts or tokens required. The connector starts an HTTP server with a built-in chat UI.

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `port` | No | HTTP/WebSocket server port (default: 3100) |
| `bot_name` | No | Bot display name (default: "Arqitect") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Session IDs or usernames allowed to interact (empty = all) |
| `cors_origins` | No | Allowed CORS origins (default: `*`) |

## Usage

Start the connector and open `http://localhost:3100` in a browser. Each browser tab opens a unique WebSocket connection with its own session/chat ID.

## Access Control

1. User whitelist: only listed session IDs can trigger the bot (if set)
2. No group concept — each WebSocket connection is a private 1:1 chat

## Supported Message Types

**Incoming**: text, image (base64 over WS), document (base64 over WS), binary file upload

**Outgoing**: text, image (base64 over WS), audio (base64 over WS), document (base64 over WS), card (JSON)

## WebSocket Protocol

Messages are exchanged as JSON over WebSocket:

**Client to server:**
```json
{ "type": "text", "text": "Hello!" }
{ "type": "file", "name": "photo.jpg", "mime": "image/jpeg", "data": "<base64>" }
```

**Server to client:**
```json
{ "type": "text", "text": "Hi there!" }
{ "type": "image", "data": "<base64>", "mime": "image/png", "caption": "" }
{ "type": "audio", "data": "<base64>", "mime": "audio/mp4", "text": "" }
{ "type": "document", "data": "<base64>", "fileName": "report.pdf", "mime": "application/pdf", "caption": "" }
{ "type": "card", "card": { "title": "...", "body": "...", "footer": "..." }, "text": "" }
{ "type": "typing", "active": true }
```

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio |
