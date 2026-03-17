/**
 * Nostr Connector — bridges Nostr NIP-04 encrypted direct messages to the Sentient brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Nostr-specific relay connections, event subscriptions,
 * and NIP-04 encryption/decryption.
 *
 * Auth: requires a Nostr private key (hex or nsec) and a list of relay URLs.
 */

require("websocket-polyfill");
const {
  SimplePool,
  nip04,
  nip19,
  getPublicKey,
  finalizeEvent,
  generateSecretKey,
} = require("nostr-tools");
const path = require("path");
const fs = require("fs");
const ConnectorBase = require("../lib/connector-base");

const connector = new ConnectorBase("nostr", __dirname);

// Nostr has no group concept — all messages are DMs
connector.setGroupDetector(() => false);

// --- Config loading ---

const configFile = path.join(__dirname, "config.json");
let privateKeyHex = "";
let relayUrls = [];

if (fs.existsSync(configFile)) {
  try {
    const loaded = JSON.parse(fs.readFileSync(configFile, "utf8"));
    privateKeyHex = loaded.private_key || "";
    relayUrls = loaded.relays || [];
  } catch (_) {}
}

if (!privateKeyHex) {
  console.error("[NOSTR] FATAL: private_key is required in config.json.");
  process.exit(1);
}

if (!relayUrls.length) {
  console.error("[NOSTR] FATAL: at least one relay URL is required in config.json.");
  process.exit(1);
}

// --- Key handling ---

/**
 * Decode the private key from nsec bech32 format or use raw hex.
 * @param {string} key - Private key in hex or nsec format
 * @returns {Uint8Array} 32-byte secret key
 */
function decodePrivateKey(key) {
  if (key.startsWith("nsec")) {
    const decoded = nip19.decode(key);
    return decoded.data;
  }
  // Hex string to Uint8Array
  return Uint8Array.from(Buffer.from(key, "hex"));
}

/**
 * Decode a public key from npub bech32 format or return raw hex.
 * @param {string} key - Public key in hex or npub format
 * @returns {string} Hex-encoded public key
 */
function decodePublicKey(key) {
  if (key.startsWith("npub")) {
    const decoded = nip19.decode(key);
    return decoded.data;
  }
  return key;
}

const secretKey = decodePrivateKey(privateKeyHex);
const publicKeyHex = getPublicKey(secretKey);
console.log(`[NOSTR] Bot public key: ${publicKeyHex}`);
console.log(`[NOSTR] Bot npub: ${nip19.npubEncode(publicKeyHex)}`);

// --- Relay pool ---

/** @type {SimplePool} */
const pool = new SimplePool();

/**
 * Set of event IDs already processed, to deduplicate across relays.
 * @type {Set<string>}
 */
const processedEvents = new Set();

/** Maximum size for the processed events set before pruning */
const MAX_PROCESSED_EVENTS = 10000;

/**
 * Prune the oldest entries from the processed events set
 * to prevent unbounded memory growth.
 */
function pruneProcessedEvents() {
  if (processedEvents.size <= MAX_PROCESSED_EVENTS) return;

  const excess = processedEvents.size - MAX_PROCESSED_EVENTS;
  const iterator = processedEvents.values();
  for (let i = 0; i < excess; i++) {
    processedEvents.delete(iterator.next().value);
  }
}

/**
 * Shorten a public key for display in logs.
 * @param {string} pubkey - Hex public key
 * @returns {string} Shortened key
 */
function shortenPubkey(pubkey) {
  return `${pubkey.slice(0, 8)}...${pubkey.slice(-4)}`;
}

// --- Message handling ---

/**
 * Handle an incoming NIP-04 encrypted DM event.
 * Decrypts the content, builds a normalized message, and
 * passes it to ConnectorBase.handleIncoming.
 * @param {object} event - Nostr event of kind 4
 */
async function handleEncryptedDM(event) {
  // Deduplicate events received from multiple relays
  if (processedEvents.has(event.id)) return;
  processedEvents.add(event.id);
  pruneProcessedEvents();

  // Ignore our own outgoing messages
  if (event.pubkey === publicKeyHex) return;

  // Only process DMs addressed to us
  const recipientTag = event.tags.find((t) => t[0] === "p");
  if (!recipientTag || recipientTag[1] !== publicKeyHex) return;

  // Ignore events from before startup to avoid replaying history
  const eventTimestamp = event.created_at * 1000;
  if (eventTimestamp < startTimestamp - 30000) return;

  let decryptedText;
  try {
    decryptedText = await nip04.decrypt(secretKey, event.pubkey, event.content);
  } catch (err) {
    console.warn(`[NOSTR] Failed to decrypt DM from ${shortenPubkey(event.pubkey)}: ${err.message}`);
    return;
  }

  if (!decryptedText || !decryptedText.trim()) return;

  console.log(`[NOSTR] DM from ${shortenPubkey(event.pubkey)}: ${decryptedText.substring(0, 80)}`);

  const normalized = {
    chatId: event.pubkey,
    senderId: event.pubkey,
    senderName: shortenPubkey(event.pubkey),
    text: decryptedText,
    msgKey: event.id,
  };

  await connector.handleIncoming(normalized);
}

// --- Send hooks ---

connector.setSendHooks({
  /**
   * Encrypt and send a NIP-04 DM to a Nostr user.
   * The chatId is the recipient's hex public key.
   * @param {string} chatId - Recipient hex public key
   * @param {string} text - Message text to encrypt and send
   */
  async sendText(chatId, text) {
    const recipientPubkey = chatId;

    let encryptedContent;
    try {
      encryptedContent = await nip04.encrypt(secretKey, recipientPubkey, text);
    } catch (err) {
      console.error(`[NOSTR] Failed to encrypt reply to ${shortenPubkey(recipientPubkey)}: ${err.message}`);
      return;
    }

    const eventTemplate = {
      kind: 4,
      created_at: Math.floor(Date.now() / 1000),
      tags: [["p", recipientPubkey]],
      content: encryptedContent,
    };

    const signedEvent = finalizeEvent(eventTemplate, secretKey);

    try {
      await Promise.any(pool.publish(relayUrls, signedEvent));
      console.log(`[NOSTR] Reply sent to ${shortenPubkey(recipientPubkey)}`);
    } catch (err) {
      console.error(`[NOSTR] Failed to publish reply: ${err.message}`);
    }
  },
});

// --- Subscription setup ---

/** Timestamp recorded at startup to filter out historical events */
let startTimestamp = 0;

/**
 * Connect to relays and subscribe to NIP-04 encrypted DMs (kind 4)
 * addressed to this bot's public key.
 */
async function startNostr() {
  startTimestamp = Date.now();

  // Subscribe to kind 4 (encrypted DM) events tagged with our pubkey
  const sinceTimestamp = Math.floor(startTimestamp / 1000) - 30;

  const sub = pool.subscribeMany(
    relayUrls,
    [
      {
        kinds: [4],
        "#p": [publicKeyHex],
        since: sinceTimestamp,
      },
    ],
    {
      onevent(event) {
        handleEncryptedDM(event).catch((err) => {
          console.error(`[NOSTR] Error handling DM: ${err.message}`);
        });
      },
      oneose() {
        console.log("[NOSTR] Subscription caught up with relay history.");
      },
    },
  );

  console.log(`[NOSTR] Subscribed to ${relayUrls.length} relay(s) for encrypted DMs.`);

  return sub;
}

// --- Main ---

async function main() {
  await connector.start();
  const sub = await startNostr();
  console.log("[NOSTR] Connector running. Listening for Nostr DMs...");

  process.once("SIGINT", () => {
    sub.close();
    pool.close(relayUrls);
    process.exit(0);
  });
  process.once("SIGTERM", () => {
    sub.close();
    pool.close(relayUrls);
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("[NOSTR] Fatal:", err);
  process.exit(1);
});
