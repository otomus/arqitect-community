/**
 * Tlon Messenger Connector — bridges Tlon peer-to-peer chat messages to the
 * Sentient brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Tlon-specific Urbit HTTP API integration.
 *
 * Auth: ship +code from the Urbit ship (no OAuth, no bot token)
 */

const { Urbit } = require("@urbit/http-api");
const ConnectorBase = require("../lib/connector-base");
const path = require("path");
const fs = require("fs");

const connector = new ConnectorBase("tlon", __dirname);

// --- Config ---

const configFile = path.join(__dirname, "config.json");
let shipUrl = "";
let shipCode = "";

if (fs.existsSync(configFile)) {
  try {
    const loaded = JSON.parse(fs.readFileSync(configFile, "utf8"));
    shipUrl = loaded.ship_url || "";
    shipCode = loaded.ship_code || "";
  } catch (_) {}
}

if (!shipUrl || !shipCode) {
  console.error("[TLON] FATAL: ship_url and ship_code are required in config.json.");
  process.exit(1);
}

/** @type {Urbit | null} */
let urbit = null;

/** Our ship name (e.g. "~zod"), populated after authentication. */
let ourShip = "";

// --- Tlon-specific: group detection via channel path ---

/**
 * Channel paths containing "/channels/" or starting with a group sigil
 * indicate group conversations. DMs are direct ship-to-ship.
 */
connector.setGroupDetector((chatId) => {
  const id = String(chatId);
  return id.includes("/channels/") || id.includes("/groups/");
});

/**
 * Override addressesBot for Tlon — checks for bot name prefix in message text.
 * Tlon has no native @mention syntax, so we rely on name-based addressing.
 * @param {string} text - Raw message text
 * @returns {boolean} Whether the message is addressed to the bot
 */
connector.addressesBot = function (text) {
  const lower = text.toLowerCase().trim();
  for (const name of connector.botNames) {
    if (lower.startsWith(name)) {
      const after = lower[name.length];
      if (!after || ",: .!?\n".includes(after)) return true;
    }
  }
  return false;
};

/**
 * Override stripBotPrefix for Tlon — removes bot name prefix from text.
 * @param {string} text - Raw message text
 * @returns {string} Text with bot prefix removed
 */
connector.stripBotPrefix = function (text) {
  const lower = text.toLowerCase().trim();
  for (const name of connector.botNames) {
    if (lower.startsWith(name)) {
      const after = lower[name.length];
      if (!after || ",: .!?\n".includes(after)) {
        let stripped = text.trim().substring(name.length);
        stripped = stripped.replace(/^[,:\s.!?]+/, "").trim();
        return stripped || text;
      }
    }
  }
  return text;
};

// --- Urbit helpers ---

/**
 * Extract plain text from a Tlon message content structure.
 * Tlon messages use a nested inline content format where text lives
 * in "inline" arrays containing strings and styled objects.
 * @param {object} content - Tlon message content object
 * @returns {string} Extracted plain text
 */
function extractTextFromContent(content) {
  if (!content) return "";

  // Handle the "story" format used in Tlon chat messages
  if (content.story) {
    return extractTextFromStory(content.story);
  }

  // Handle direct inline content
  if (content.inline) {
    return extractTextFromInlines(content.inline);
  }

  // Handle plain string content
  if (typeof content === "string") return content;

  return "";
}

/**
 * Extract text from a Tlon "story" structure (array of verse blocks).
 * @param {Array} story - Array of verse objects
 * @returns {string} Concatenated plain text
 */
function extractTextFromStory(story) {
  if (!Array.isArray(story)) return "";

  const parts = [];
  for (const verse of story) {
    if (verse.inline) {
      parts.push(extractTextFromInlines(verse.inline));
    } else if (verse.block) {
      // Block elements like code blocks or images
      if (verse.block.cite) {
        parts.push(`[cite: ${verse.block.cite}]`);
      }
    }
  }
  return parts.join("\n").trim();
}

/**
 * Extract text from an array of Tlon inline elements.
 * Inline elements can be plain strings, bold/italic wrappers, links, etc.
 * @param {Array} inlines - Array of inline content elements
 * @returns {string} Concatenated plain text
 */
function extractTextFromInlines(inlines) {
  if (!Array.isArray(inlines)) return "";

  const parts = [];
  for (const inline of inlines) {
    if (typeof inline === "string") {
      parts.push(inline);
    } else if (inline.bold) {
      parts.push(extractTextFromInlines(inline.bold));
    } else if (inline.italics) {
      parts.push(extractTextFromInlines(inline.italics));
    } else if (inline.strike) {
      parts.push(extractTextFromInlines(inline.strike));
    } else if (inline.blockquote) {
      parts.push(extractTextFromInlines(inline.blockquote));
    } else if (inline["inline-code"]) {
      parts.push(inline["inline-code"]);
    } else if (inline.link) {
      parts.push(inline.link.content || inline.link.href || "");
    } else if (inline.break) {
      parts.push("\n");
    } else if (inline.ship) {
      parts.push(inline.ship);
    }
  }
  return parts.join("");
}

/**
 * Build a Tlon chat message content structure from plain text.
 * @param {string} text - Plain text to send
 * @returns {object} Tlon-formatted message content
 */
function buildChatContent(text) {
  return {
    story: [
      {
        inline: [text],
      },
    ],
  };
}

/**
 * Derive the sender ship name from a Tlon message update.
 * @param {object} update - The SSE update object
 * @returns {string} Ship name (e.g. "~zod") or empty string
 */
function extractSenderShip(update) {
  if (update.memo?.author) return update.memo.author;
  if (update.author) return update.author;
  return "";
}

/**
 * Derive the chat/channel identifier from an SSE path or update.
 * @param {string} ssePath - The SSE subscription path
 * @param {object} update - The SSE update object
 * @returns {string} Channel path used as chatId
 */
function extractChannelId(ssePath, update) {
  // The SSE path itself often serves as the channel identifier
  if (update.nest) return update.nest;
  return ssePath || "unknown";
}

// --- Send hooks ---

connector.setSendHooks({
  /**
   * Send a text message to a Tlon channel via poke.
   * @param {string} chatId - Tlon channel path (nest)
   * @param {string} text - Message text to send
   */
  async sendText(chatId, text) {
    if (!urbit) {
      console.warn("[TLON] Cannot send — urbit connection not established");
      return;
    }

    const content = buildChatContent(text);
    const memo = {
      content,
      author: ourShip,
      sent: Date.now(),
    };

    try {
      await urbit.poke({
        app: "channels",
        mark: "channel-action",
        json: {
          channel: {
            nest: chatId,
            action: {
              add: {
                memo,
                kind: null,
              },
            },
          },
        },
      });
    } catch (err) {
      console.error(`[TLON] Failed to send message to ${chatId}: ${err.message}`);
      throw err;
    }
  },

  /**
   * Show a typing indicator (no-op for Tlon — no typing support).
   * @param {string} _chatId - Unused
   */
  async sendTyping(_chatId) {
    // Tlon does not support typing indicators
  },
});

// --- SSE subscription handler ---

/**
 * Subscribe to Tlon chat channels via the Urbit SSE event stream.
 * Listens for new messages on all chat channels the ship has access to.
 */
async function subscribeToChats() {
  if (!urbit) return;

  try {
    await urbit.subscribe({
      app: "channels",
      path: "/v1",
      event: handleChannelEvent,
      err: (err) => {
        console.error("[TLON] SSE subscription error:", err);
      },
      quit: () => {
        console.warn("[TLON] SSE subscription quit — attempting reconnect...");
        setTimeout(subscribeToChats, 5000);
      },
    });
    console.log("[TLON] Subscribed to channels/v1 for chat events");
  } catch (err) {
    console.error("[TLON] Failed to subscribe:", err.message);
    // Retry after delay — the ship may not be fully ready
    setTimeout(subscribeToChats, 5000);
  }
}

/**
 * Handle a channel event from the Tlon SSE stream.
 * Filters for new chat messages and forwards them to ConnectorBase.
 * @param {object} event - Tlon channel event
 */
async function handleChannelEvent(event) {
  try {
    // Channel events arrive in a nested structure
    // { nest: "chat/~ship/channel", response: { ... } }
    if (!event || !event.nest) return;

    const nest = event.nest;
    const response = event.response;
    if (!response) return;

    // We only care about new posts (adds)
    const post = response.post?.add || response.add;
    if (!post) return;

    const senderShip = extractSenderShip(post);

    // Ignore our own messages to prevent echo loops
    if (senderShip === ourShip) return;

    const content = post.memo?.content || post.content;
    const text = extractTextFromContent(content);
    const chatId = nest;
    const messageId = post.seal?.id || post.id || String(Date.now());

    const normalized = {
      chatId: String(chatId),
      senderId: String(senderShip),
      senderName: senderShip,
      text,
      extra: {
        msg_id: messageId,
        nest,
      },
    };

    await connector.handleIncoming(normalized);
  } catch (err) {
    console.error("[TLON] Error handling channel event:", err.message);
  }
}

// --- Main ---

/**
 * Boot the Tlon connector: authenticate with the Urbit ship,
 * start ConnectorBase (Redis, config), and subscribe to chat channels.
 */
async function main() {
  await connector.start();

  console.log(`[TLON] Connecting to ship at ${shipUrl}...`);

  urbit = await Urbit.authenticate({
    ship: "",
    url: shipUrl,
    code: shipCode,
    verbose: false,
  });

  ourShip = urbit.ship ? `~${urbit.ship}` : "";
  console.log(`[TLON] Authenticated as ${ourShip}`);

  urbit.onOpen = () => {
    console.log("[TLON] SSE channel opened");
  };

  urbit.onRetry = () => {
    console.warn("[TLON] SSE channel retrying...");
  };

  urbit.onError = (err) => {
    console.error("[TLON] SSE channel error:", err);
  };

  await subscribeToChats();
  console.log("[TLON] Bot launched. Listening for messages...");

  process.once("SIGINT", () => {
    console.log("[TLON] Shutting down...");
    if (urbit) urbit.delete();
    process.exit(0);
  });
  process.once("SIGTERM", () => {
    console.log("[TLON] Shutting down...");
    if (urbit) urbit.delete();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("[TLON] Fatal:", err);
  process.exit(1);
});
