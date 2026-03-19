/**
 * Signal Connector — bridges Signal messages to the Arqitect brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Signal-specific integration via the signal-cli REST API.
 *
 * Requires a running signal-cli-rest-api instance (Docker recommended).
 * See README.md for setup instructions.
 */

const ConnectorBase = require("../lib/connector-base");
const http = require("http");
const https = require("https");
const path = require("path");
const fs = require("fs");

const TAG = "[SIGNAL]";
const POLL_INTERVAL_MS = 2000;

const connector = new ConnectorBase("signal", __dirname);

// --- Config ---

const configFile = path.join(__dirname, "config.json");
let signalCliUrl = "";
let phoneNumber = "";

if (fs.existsSync(configFile)) {
  try {
    const loaded = JSON.parse(fs.readFileSync(configFile, "utf8"));
    signalCliUrl = loaded.signal_cli_url || "";
    phoneNumber = loaded.phone_number || "";
  } catch (_) {}
}

if (!signalCliUrl || !phoneNumber) {
  console.error(`${TAG} FATAL: signal_cli_url and phone_number are required in config.json.`);
  process.exit(1);
}

// Strip trailing slash for consistent URL building
signalCliUrl = signalCliUrl.replace(/\/+$/, "");

// --- HTTP helpers ---

/**
 * Make an HTTP request to the signal-cli REST API.
 *
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {string} urlPath - API path (e.g. /v1/receive/+1234567890)
 * @param {object|null} body - JSON body for POST/PUT requests
 * @returns {Promise<{status: number, data: any}>} Parsed response
 */
function apiRequest(method, urlPath, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlPath, signalCliUrl);
    const isHttps = url.protocol === "https:";
    const transport = isHttps ? https : http;

    const options = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method,
      headers: { "Content-Type": "application/json" },
    };

    const req = transport.request(options, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        const raw = Buffer.concat(chunks).toString("utf8");
        let data = null;
        try {
          data = JSON.parse(raw);
        } catch (_) {
          data = raw;
        }
        resolve({ status: res.statusCode, data });
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
 * Download a Signal attachment by its ID from the signal-cli REST API.
 *
 * @param {string} attachmentId - Attachment identifier from the message envelope
 * @returns {Promise<Buffer|null>} Raw attachment bytes, or null on failure
 */
function downloadAttachment(attachmentId) {
  return new Promise((resolve, reject) => {
    const url = new URL(`/v1/attachments/${attachmentId}`, signalCliUrl);
    const isHttps = url.protocol === "https:";
    const transport = isHttps ? https : http;

    transport.get(url.href, (res) => {
      if (res.statusCode !== 200) {
        console.warn(`${TAG} Attachment download returned ${res.statusCode}`);
        resolve(null);
        return;
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks)));
      res.on("error", (err) => {
        console.warn(`${TAG} Attachment download error: ${err.message}`);
        resolve(null);
      });
    }).on("error", (err) => {
      console.warn(`${TAG} Attachment download failed: ${err.message}`);
      resolve(null);
    });
  });
}

// --- Group detection ---

/**
 * Signal group messages include a groupInfo field with the group ID.
 * We track known group IDs to use in the group detector.
 */
const knownGroupIds = new Set();

connector.setGroupDetector((chatId) => knownGroupIds.has(String(chatId)));

// --- Bot addressing ---

/**
 * In Signal groups there are no @mentions or /commands, so we rely on
 * name prefix matching from the base class. No override needed.
 */

// --- Media type mapping ---

const MIME_TO_MEDIA_TYPE = {
  "image/jpeg": "image",
  "image/png": "image",
  "image/gif": "image",
  "image/webp": "sticker",
  "video/mp4": "video",
  "video/3gpp": "video",
  "audio/aac": "audio",
  "audio/mp4": "audio",
  "audio/mpeg": "audio",
  "audio/ogg": "audio",
  "application/pdf": "document",
  "application/zip": "document",
};

/**
 * Derive the logical media type from a MIME string.
 *
 * @param {string} contentType - MIME type (e.g. "image/jpeg")
 * @returns {string} Normalized media type for the brain
 */
function mediaTypeFromMime(contentType) {
  if (!contentType) return "document";
  const lower = contentType.toLowerCase();
  if (MIME_TO_MEDIA_TYPE[lower]) return MIME_TO_MEDIA_TYPE[lower];
  if (lower.startsWith("image/")) return "image";
  if (lower.startsWith("video/")) return "video";
  if (lower.startsWith("audio/")) return "audio";
  return "document";
}

// --- Send hooks ---

connector.setSendHooks({
  /**
   * Send a plain text message to a Signal recipient or group.
   *
   * @param {string} chatId - Phone number or base64 group ID
   * @param {string} text - Message body
   */
  async sendText(chatId, text) {
    const body = buildSendPayload(chatId, text);
    const { status, data } = await apiRequest("POST", "/v2/send", body);
    if (status >= 400) {
      console.warn(`${TAG} sendText failed (${status}):`, JSON.stringify(data));
    }
  },

  /**
   * Send an image as a base64-encoded attachment.
   *
   * @param {string} chatId - Recipient identifier
   * @param {string} caption - Image caption
   * @param {Buffer} imageBuffer - Raw image bytes
   * @param {string} mime - MIME type (e.g. "image/png")
   */
  async sendImage(chatId, caption, imageBuffer, mime) {
    const base64Data = imageBuffer.toString("base64");
    const body = buildSendPayload(chatId, caption, [{
      contentType: mime || "image/png",
      filename: `image_${Date.now()}.${mimeToExtension(mime)}`,
      base64: base64Data,
    }]);
    const { status, data } = await apiRequest("POST", "/v2/send", body);
    if (status >= 400) {
      console.warn(`${TAG} sendImage failed (${status}):`, JSON.stringify(data));
    }
  },

  /**
   * Send an audio file as a base64-encoded attachment.
   *
   * @param {string} chatId - Recipient identifier
   * @param {string} text - Accompanying text message
   * @param {Buffer} audioBuffer - Raw audio bytes
   * @param {string} mime - MIME type (e.g. "audio/mp4")
   */
  async sendAudio(chatId, text, audioBuffer, mime) {
    const base64Data = audioBuffer.toString("base64");
    const body = buildSendPayload(chatId, text, [{
      contentType: mime || "audio/mp4",
      filename: `audio_${Date.now()}.${mimeToExtension(mime)}`,
      base64: base64Data,
    }]);
    const { status, data } = await apiRequest("POST", "/v2/send", body);
    if (status >= 400) {
      console.warn(`${TAG} sendAudio failed (${status}):`, JSON.stringify(data));
    }
  },

  /**
   * Send a document as a base64-encoded attachment.
   *
   * @param {string} chatId - Recipient identifier
   * @param {object} doc - Document descriptor
   * @param {Buffer} doc.buffer - Raw file bytes
   * @param {string} doc.fileName - Original file name
   * @param {string} doc.mime - MIME type
   * @param {string} doc.caption - Caption text
   */
  async sendDocument(chatId, { buffer, fileName, mime, caption }) {
    const base64Data = buffer.toString("base64");
    const body = buildSendPayload(chatId, caption, [{
      contentType: mime || "application/octet-stream",
      filename: fileName || `document_${Date.now()}`,
      base64: base64Data,
    }]);
    const { status, data } = await apiRequest("POST", "/v2/send", body);
    if (status >= 400) {
      console.warn(`${TAG} sendDocument failed (${status}):`, JSON.stringify(data));
    }
  },

  /**
   * Send a sticker as a base64-encoded WebP attachment.
   *
   * @param {string} chatId - Recipient identifier
   * @param {Buffer} stickerBuffer - Raw sticker bytes (WebP)
   * @param {string} text - Accompanying text
   */
  async sendSticker(chatId, stickerBuffer, text) {
    const base64Data = stickerBuffer.toString("base64");
    const body = buildSendPayload(chatId, text, [{
      contentType: "image/webp",
      filename: `sticker_${Date.now()}.webp`,
      base64: base64Data,
    }]);
    const { status, data } = await apiRequest("POST", "/v2/send", body);
    if (status >= 400) {
      console.warn(`${TAG} sendSticker failed (${status}):`, JSON.stringify(data));
    }
  },

  /**
   * Send a reaction emoji to a specific message.
   *
   * @param {string} chatId - Recipient identifier
   * @param {string} emoji - Reaction emoji character
   * @param {object} msgKey - Original message reference { targetAuthor, timestamp }
   */
  async sendReaction(chatId, emoji, msgKey) {
    if (!msgKey || !msgKey.targetAuthor || !msgKey.timestamp) return;

    const body = {
      recipient: knownGroupIds.has(chatId) ? undefined : chatId,
      reaction: emoji,
      target_author: msgKey.targetAuthor,
      timestamp: msgKey.timestamp,
      number: phoneNumber,
    };

    if (knownGroupIds.has(chatId)) {
      body.recipients = [chatId];
    }

    const { status, data } = await apiRequest(
      "POST",
      `/v1/reactions/${encodeURIComponent(phoneNumber)}`,
      body
    );
    if (status >= 400) {
      console.warn(`${TAG} sendReaction failed (${status}):`, JSON.stringify(data));
    }
  },
});

// --- Send payload builder ---

/**
 * Build a signal-cli v2/send JSON payload, handling both direct messages
 * and group messages.
 *
 * @param {string} chatId - Phone number (direct) or base64 group ID (group)
 * @param {string} message - Text body
 * @param {Array|null} attachments - Optional array of base64-encoded attachments
 * @returns {object} Request body for POST /v2/send
 */
function buildSendPayload(chatId, message, attachments = null) {
  const body = {
    number: phoneNumber,
    message: message || "",
  };

  if (knownGroupIds.has(chatId)) {
    body.recipients = [chatId];
  } else {
    body.recipients = [chatId];
  }

  if (attachments && attachments.length > 0) {
    body.base64_attachments = attachments;
  }

  return body;
}

/**
 * Map a MIME type to a file extension for attachment filenames.
 *
 * @param {string} mime - MIME type string
 * @returns {string} File extension without the dot
 */
function mimeToExtension(mime) {
  const map = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
    "audio/ogg": "ogg",
    "audio/aac": "aac",
    "application/pdf": "pdf",
    "application/zip": "zip",
  };
  return map[mime] || "bin";
}

// --- Incoming message processing ---

/**
 * Process a single envelope from the signal-cli receive endpoint.
 * Extracts text, media, contacts, and group info, then hands off
 * to ConnectorBase.handleIncoming().
 *
 * @param {object} envelope - Signal message envelope from the REST API
 */
async function processEnvelope(envelope) {
  if (!envelope) return;

  const dataMessage = envelope.dataMessage;
  if (!dataMessage) return;

  const senderId = envelope.sourceNumber || envelope.source || "";
  const senderName = envelope.sourceName || senderId;
  const timestamp = dataMessage.timestamp || envelope.timestamp || Date.now();

  // Determine chat context (group vs. direct)
  const groupInfo = dataMessage.groupInfo;
  let chatId;

  if (groupInfo && groupInfo.groupId) {
    chatId = groupInfo.groupId;
    knownGroupIds.add(chatId);
  } else {
    chatId = senderId;
  }

  const text = dataMessage.message || "";

  const normalized = {
    chatId: String(chatId),
    senderId: String(senderId),
    senderName,
    text,
    msgKey: { targetAuthor: senderId, timestamp },
    extra: {
      timestamp,
    },
  };

  // Process attachments
  const attachments = dataMessage.attachments || [];
  if (attachments.length > 0) {
    const attachment = attachments[0];
    const contentType = attachment.contentType || "";
    const attachmentId = attachment.id;
    const mediaType = mediaTypeFromMime(contentType);

    let buffer = null;
    let mediaPath = null;

    if (attachmentId) {
      buffer = await downloadAttachment(attachmentId);
      if (buffer) {
        mediaPath = await connector.saveMediaBuffer(buffer, mediaType);
      }
    }

    normalized.media = {
      type: mediaType,
      path: mediaPath || "",
      mime: contentType,
      size: attachment.size || (buffer ? buffer.length : 0),
      buffer,
    };
  }

  // Process shared contacts
  const contacts = dataMessage.contacts || [];
  if (contacts.length > 0) {
    normalized.contacts = contacts.map((c) => ({
      name: c.name
        ? `${c.name.givenName || ""} ${c.name.familyName || ""}`.trim()
        : "",
      phone: c.number || "",
    }));
  }

  await connector.handleIncoming(normalized);
}

// --- Polling loop ---

let pollTimer = null;

/**
 * Poll the signal-cli REST API for new messages and process each envelope.
 * Runs on a fixed interval defined by POLL_INTERVAL_MS.
 */
async function pollMessages() {
  try {
    const encodedNumber = encodeURIComponent(phoneNumber);
    const { status, data } = await apiRequest("GET", `/v1/receive/${encodedNumber}`);

    if (status >= 400) {
      console.warn(`${TAG} Poll failed (${status}):`, JSON.stringify(data));
      return;
    }

    if (!Array.isArray(data)) return;

    for (const item of data) {
      const envelope = item.envelope || item;
      try {
        await processEnvelope(envelope);
      } catch (err) {
        console.error(`${TAG} Error processing envelope:`, err.message);
      }
    }
  } catch (err) {
    console.error(`${TAG} Poll error:`, err.message);
  }
}

/**
 * Start the polling loop that fetches messages from signal-cli on a timer.
 */
function startPolling() {
  console.log(`${TAG} Polling signal-cli at ${signalCliUrl} every ${POLL_INTERVAL_MS}ms`);
  pollMessages();
  pollTimer = setInterval(pollMessages, POLL_INTERVAL_MS);
}

// --- Main ---

async function main() {
  await connector.start();
  startPolling();
  console.log(`${TAG} Signal connector running for ${phoneNumber}. Listening for messages...`);

  process.once("SIGINT", () => {
    console.log(`${TAG} Shutting down...`);
    clearInterval(pollTimer);
    process.exit(0);
  });
  process.once("SIGTERM", () => {
    console.log(`${TAG} Shutting down...`);
    clearInterval(pollTimer);
    process.exit(0);
  });
}

main().catch((err) => {
  console.error(`${TAG} Fatal:`, err);
  process.exit(1);
});
