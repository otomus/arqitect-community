/**
 * iMessage Connector (BlueBubbles) — bridges iMessage to Sentient brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles BlueBubbles-specific integration via:
 *   - WebSocket (Socket.IO) for real-time incoming messages
 *   - REST API for sending messages and downloading attachments
 *
 * Requirements:
 *   - BlueBubbles server running and accessible (https://bluebubbles.app)
 *   - Server URL and password configured in config.json
 */

const { io } = require("socket.io-client");
const https = require("https");
const http = require("http");
const path = require("path");
const fs = require("fs");
const os = require("os");
const ConnectorBase = require("../lib/connector-base");

const connector = new ConnectorBase("imessage-bluebubbles", __dirname);

/** @type {import('socket.io-client').Socket | null} */
let socket = null;

/** @type {Map<string, boolean>} chatGuid -> isGroup cache */
const groupCache = new Map();

connector.setGroupDetector((chatId) => groupCache.get(String(chatId)) === true);

// ---------------------------------------------------------------------------
// BlueBubbles REST API helpers
// ---------------------------------------------------------------------------

/**
 * Build a full API URL with the server password as a query parameter.
 *
 * @param {string} endpoint - API path (e.g. "/api/v1/message/text").
 * @param {Record<string, string>} [extraParams] - Additional query parameters.
 * @returns {string} Full URL with password.
 */
function buildApiUrl(endpoint, extraParams = {}) {
  const base = connector.config.server_url.replace(/\/+$/, "");
  const url = new URL(`${base}${endpoint}`);
  url.searchParams.set("password", connector.config.password);
  for (const [key, value] of Object.entries(extraParams)) {
    url.searchParams.set(key, value);
  }
  return url.toString();
}

/**
 * Make an HTTP request to the BlueBubbles REST API.
 *
 * @param {string} endpoint - API path.
 * @param {{ method?: string, body?: object, extraParams?: Record<string, string> }} options
 * @returns {Promise<object>} Parsed JSON response.
 */
function apiRequest(endpoint, { method = "GET", body = null, extraParams = {} } = {}) {
  return new Promise((resolve, reject) => {
    const fullUrl = buildApiUrl(endpoint, extraParams);
    const parsed = new URL(fullUrl);
    const isHttps = parsed.protocol === "https:";

    const reqOptions = {
      hostname: parsed.hostname,
      port: parsed.port,
      path: `${parsed.pathname}${parsed.search}`,
      method,
      headers: { "Content-Type": "application/json" },
    };

    const transport = isHttps ? https : http;
    const req = transport.request(reqOptions, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        const raw = Buffer.concat(chunks).toString("utf8");
        try {
          resolve(JSON.parse(raw));
        } catch {
          resolve({ status: res.statusCode, raw });
        }
      });
      res.on("error", reject);
    });
    req.on("error", reject);

    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

/**
 * Download a raw binary buffer from a URL.
 *
 * @param {string} url
 * @returns {Promise<Buffer>}
 */
function downloadBuffer(url) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const transport = parsed.protocol === "https:" ? https : http;
    transport.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        downloadBuffer(res.headers.location).then(resolve).catch(reject);
        return;
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks)));
      res.on("error", reject);
    }).on("error", reject);
  });
}

// ---------------------------------------------------------------------------
// Attachment handling
// ---------------------------------------------------------------------------

/**
 * Download an attachment from the BlueBubbles server by its GUID.
 *
 * @param {string} attachmentGuid
 * @returns {Promise<Buffer>}
 */
async function downloadAttachment(attachmentGuid) {
  const url = buildApiUrl(`/api/v1/attachment/${attachmentGuid}/download`);
  return downloadBuffer(url);
}

/**
 * Classify an attachment MIME type into brain media categories.
 *
 * @param {string} mime
 * @returns {'image' | 'audio' | 'video' | 'document'}
 */
function classifyMime(mime) {
  if (!mime) return "document";
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("audio/")) return "audio";
  if (mime.startsWith("video/")) return "video";
  return "document";
}

/**
 * Download and save an attachment, returning normalized media metadata.
 *
 * @param {{ guid: string, mimeType: string, totalBytes: number }} attachment
 * @returns {Promise<{ type: string, path: string, mime: string, size: number, buffer: Buffer } | null>}
 */
async function processAttachment(attachment) {
  try {
    const buffer = await downloadAttachment(attachment.guid);
    const mediaType = classifyMime(attachment.mimeType);
    const savedPath = await connector.saveMediaBuffer(buffer, mediaType);
    return {
      type: mediaType,
      path: savedPath,
      mime: attachment.mimeType || "application/octet-stream",
      size: buffer.length,
      buffer,
    };
  } catch (err) {
    console.warn(`[BB] Failed to download attachment ${attachment.guid}: ${err.message}`);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Message handling
// ---------------------------------------------------------------------------

/**
 * Extract the sender identifier from a BlueBubbles message object.
 * For incoming messages, this is the handle address (phone/email).
 *
 * @param {object} message - BlueBubbles message payload.
 * @returns {string}
 */
function extractSenderId(message) {
  if (message.handle?.address) return message.handle.address;
  if (message.handleId) return String(message.handleId);
  return "unknown";
}

/**
 * Process a new incoming message from BlueBubbles WebSocket.
 *
 * @param {object} message - BlueBubbles message payload.
 */
async function handleNewMessage(message) {
  // Skip outgoing (from-me) messages
  if (message.isFromMe) return;

  const chatGuid = message.chats?.[0]?.guid || message.chatGuid || "";
  if (!chatGuid) return;

  // Determine if this is a group chat
  const chat = message.chats?.[0];
  const isGroup = chat?.style === 43 || (chat?.participants?.length ?? 0) > 1;
  groupCache.set(chatGuid, isGroup);

  const senderId = extractSenderId(message);
  const senderName = message.handle?.firstName
    ? `${message.handle.firstName} ${message.handle.lastName || ""}`.trim()
    : senderId;

  const text = message.text || "";

  const normalized = {
    chatId: chatGuid,
    senderId,
    senderName,
    text,
    extra: {
      bb_guid: message.guid,
      chat_display_name: chat?.displayName || chatGuid,
    },
  };

  // Process attachments (take the first one)
  if (message.attachments?.length > 0) {
    const attachment = message.attachments[0];
    const media = await processAttachment(attachment);
    if (media) {
      normalized.media = media;
    }
  }

  await connector.handleIncoming(normalized);
}

// ---------------------------------------------------------------------------
// Send hooks
// ---------------------------------------------------------------------------

/**
 * Send a text message via the BlueBubbles REST API.
 *
 * @param {string} chatGuid - Chat GUID to send to.
 * @param {string} text - Message text.
 */
async function sendText(chatGuid, text) {
  await apiRequest("/api/v1/message/text", {
    method: "POST",
    body: {
      chatGuid,
      message: text,
      method: "apple-script",
    },
  });
}

/**
 * Send an image attachment via the BlueBubbles REST API.
 * Writes the buffer to a temp file, then sends via the attachment endpoint.
 *
 * @param {string} chatGuid - Chat GUID.
 * @param {string} caption - Text caption.
 * @param {Buffer} imageBuffer - Raw image bytes.
 * @param {string} mime - MIME type.
 */
async function sendImage(chatGuid, caption, imageBuffer, mime) {
  const ext = mime === "image/png" ? ".png" : ".jpg";
  const tmpName = `sentient_img_${Date.now()}${ext}`;
  const tmpPath = path.join(os.tmpdir(), tmpName);
  fs.writeFileSync(tmpPath, imageBuffer);

  try {
    // BlueBubbles attachment send uses multipart, but we can also use the
    // base64 approach via the REST API
    await apiRequest("/api/v1/message/attachment", {
      method: "POST",
      body: {
        chatGuid,
        name: tmpName,
        attachment: imageBuffer.toString("base64"),
      },
    });
    if (caption) {
      await sendText(chatGuid, caption);
    }
  } finally {
    try { fs.unlinkSync(tmpPath); } catch (_) { /* best effort */ }
  }
}

/**
 * Send a document attachment via the BlueBubbles REST API.
 *
 * @param {string} chatGuid - Chat GUID.
 * @param {{ buffer: Buffer, fileName: string, mime: string, caption: string }} doc
 */
async function sendDocument(chatGuid, { buffer, fileName, mime, caption }) {
  await apiRequest("/api/v1/message/attachment", {
    method: "POST",
    body: {
      chatGuid,
      name: fileName,
      attachment: buffer.toString("base64"),
    },
  });
  if (caption) {
    await sendText(chatGuid, caption);
  }
}

/**
 * Send a tapback reaction via the BlueBubbles REST API.
 * BlueBubbles maps emoji reactions to tapback types.
 *
 * @param {string} chatGuid - Chat GUID.
 * @param {string} emoji - Reaction emoji.
 * @param {string} messageGuid - GUID of the message to react to.
 */
async function sendReaction(chatGuid, emoji, messageGuid) {
  // Map common emoji to BlueBubbles tapback names
  const tapbackMap = {
    "\u2764\uFE0F": "love",
    "\uD83D\uDC4D": "like",
    "\uD83D\uDC4E": "dislike",
    "\uD83D\uDE02": "laugh",
    "\u2757": "emphasize",
    "\u2753": "question",
  };
  const tapback = tapbackMap[emoji] || "love";

  await apiRequest("/api/v1/message/react", {
    method: "POST",
    body: {
      chatGuid,
      selectedMessageGuid: messageGuid,
      reaction: tapback,
    },
  });
}

connector.setSendHooks({
  sendText,
  sendImage,
  sendDocument,
  sendReaction,
});

// ---------------------------------------------------------------------------
// WebSocket connection to BlueBubbles
// ---------------------------------------------------------------------------

/**
 * Establish a Socket.IO connection to the BlueBubbles server for real-time
 * message delivery. Handles reconnection automatically.
 */
function connectWebSocket() {
  const serverUrl = connector.config.server_url.replace(/\/+$/, "");
  console.log(`[BB] Connecting WebSocket to ${serverUrl}`);

  socket = io(serverUrl, {
    query: { password: connector.config.password },
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionDelay: 3000,
    reconnectionAttempts: Infinity,
  });

  socket.on("connect", () => {
    console.log("[BB] WebSocket connected");
  });

  socket.on("disconnect", (reason) => {
    console.warn(`[BB] WebSocket disconnected: ${reason}`);
  });

  socket.on("connect_error", (err) => {
    console.error(`[BB] WebSocket connection error: ${err.message}`);
  });

  // BlueBubbles emits "new-message" for incoming messages
  socket.on("new-message", async (data) => {
    try {
      await handleNewMessage(data);
    } catch (err) {
      console.error(`[BB] Error handling new message: ${err.message}`);
    }
  });

  // BlueBubbles also emits "updated-message" for delivery receipts, reactions, etc.
  socket.on("updated-message", async (data) => {
    // Log reactions from others for observability
    if (data.associatedMessageType) {
      const senderId = extractSenderId(data);
      console.log(`[BB] ${senderId}: tapback ${data.associatedMessageType} on ${data.associatedMessageGuid}`);
    }
  });

  // Group chat events
  socket.on("group-name-change", (data) => {
    console.log(`[BB] Group renamed: ${data.chatGuid} -> ${data.newName}`);
  });

  socket.on("participant-added", (data) => {
    console.log(`[BB] Participant added to ${data.chatGuid}`);
  });

  socket.on("participant-removed", (data) => {
    console.log(`[BB] Participant removed from ${data.chatGuid}`);
  });
}

// ---------------------------------------------------------------------------
// Server health check
// ---------------------------------------------------------------------------

/**
 * Verify that the BlueBubbles server is reachable and the password is correct.
 *
 * @returns {Promise<boolean>}
 */
async function verifyServer() {
  try {
    const result = await apiRequest("/api/v1/server/info");
    if (result.status === 200 || result.data) {
      const info = result.data || result;
      console.log(`[BB] Server info: BlueBubbles v${info.os_version || "unknown"}, macOS ${info.platform || "unknown"}`);
      return true;
    }
    console.error("[BB] Unexpected server response:", JSON.stringify(result).substring(0, 200));
    return false;
  } catch (err) {
    console.error(`[BB] Cannot reach server at ${connector.config.server_url}: ${err.message}`);
    return false;
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

/**
 * Entry point — start the connector, verify the server, and connect WebSocket.
 */
async function main() {
  await connector.start();

  // Validate required config
  if (!connector.config.server_url) {
    console.error("[BB] server_url is required in config.json");
    process.exit(1);
  }
  if (!connector.config.password) {
    console.error("[BB] password is required in config.json");
    process.exit(1);
  }

  // Verify server connectivity
  const serverOk = await verifyServer();
  if (!serverOk) {
    console.error("[BB] Failed to connect to BlueBubbles server. Check server_url and password.");
    process.exit(1);
  }

  // Connect WebSocket for real-time messages
  connectWebSocket();

  console.log("[BB] Connector running. Send an iMessage to interact with the brain.");

  // Graceful shutdown
  const shutdown = () => {
    console.log("[BB] Shutting down...");
    if (socket) socket.disconnect();
    process.exit(0);
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main().catch((err) => {
  console.error("[BB] Fatal:", err);
  process.exit(1);
});
