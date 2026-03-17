# Nostr Connector

Bridges Nostr NIP-04 encrypted direct messages to the Sentient brain via Redis using [nostr-tools](https://github.com/nbd-wtf/nostr-tools).

This connector runs as a separate Node.js process alongside the Sentient core. It communicates with the brain exclusively through Redis pub/sub — no shared code, no language dependency. Sentient's `start.sh` handles launching it automatically.

## Prerequisites

You need a Nostr keypair for the bot. You can generate one using nostr-tools or any Nostr key generator. The private key can be in hex or nsec (bech32) format.

## Configuration

Copy `config-template.json` to `config.json` and fill in your values.

| Field | Required | Description |
|-------|----------|-------------|
| `private_key` | Yes | Bot private key in hex or nsec format |
| `relays` | Yes | Array of relay WebSocket URLs (e.g. `wss://relay.damus.io`) |
| `bot_name` | No | Bot display name (default: "Sentient") |
| `bot_aliases` | No | Alternative names the bot responds to |
| `whitelisted_users` | No | Nostr public keys (npub or hex) allowed to interact (empty = all) |

## Access Control

1. User whitelist: only listed public keys can trigger the bot (if set; empty = allow all)
2. All messages are treated as DMs — there is no group concept in this connector

## How It Works

The connector subscribes to NIP-04 encrypted DM events (kind 4) on the configured relays. When a DM addressed to the bot's public key arrives:

1. The event is decrypted using NIP-04
2. The decrypted text is forwarded to the brain via Redis
3. The brain's response is encrypted with NIP-04 and published back to the relays

Events are deduplicated across relays to prevent processing the same message multiple times.

## Supported Message Types

**Incoming**: text (NIP-04 encrypted DMs are text-only)

**Outgoing**: text (NIP-04 encrypted DMs are text-only)

## Redis Channels

| Direction | Channel | Purpose |
|-----------|---------|---------|
| Publish | `brain:task` | Send user messages to brain |
| Subscribe | `brain:response` | Receive brain responses |
| Subscribe | `brain:audio` | Receive TTS audio (text fallback only) |
