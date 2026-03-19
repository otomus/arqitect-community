/**
 * Zalo OA Connector — bridges Zalo Official Account messages to the Arqitect brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Zalo OA-specific webhook receiving and REST API sending.
 *
 * Auth: Zalo OA access_token + refresh_token from the Zalo Developer portal.
 * The connector auto-refreshes the access token when it expires.
 *
 * All Zalo OA conversations are 1:1 (no group concept).
 */

const express = require("express");
const crypto = require("crypto");
const https = require("https");
const path = require("path");
const fs = require("fs");
const ConnectorBase = require("../lib/connector-base");

const connector = new ConnectorBase("zalo", __dirname);

// Zalo OA has no group concept — all chats are direct messages
connector.setGroupDetector(() => false);

const ZALO_OA_API_BASE = "https://openapi.zalo.me/v3.0/oa";
const ZALO_AUTH_URL = "https://oauth.zaloapp.com/v4/oa/access_token";
const TOKEN_FILE = path.join(__dirname, ".zalo_tokens.json");

let accessToken = "";
let refreshToken = "";
let appId = "";
let secretKey = "";
let tokenExpiresAt = 0;

// --- Token persistence ---

/**
 * Save current tokens to disk so the connector survives restarts
 * without requiring manual token re-entry.
 */
function persistTokens() {
  try {
    fs.writeFileSync(TOKEN_FILE, JSON.stringify({
      access_token: accessToken,
      refresh_token: refreshToken,
      expires_at: tokenExpiresAt,
    }));
  } catch (err) {
    console.warn("[ZALO] Failed to persist tokens:", err.message);
  }
}

/**
 * Load previously saved tokens from disk.
 */
function loadPersistedTokens() {
  try {
    if (fs.existsSync(TOKEN_FILE)) {
      const saved = JSON.parse(fs.readFileSync(TOKEN_FILE, "utf8"));
      if (saved.access_token) accessToken = saved.access_token;
      if (saved.refresh_token) refreshToken = saved.refresh_token;
      if (saved.expires_at) tokenExpiresAt = saved.expires_at;
      console.log("[ZALO] Loaded persisted tokens");
    }
  } catch (err) {
    console.warn("[ZALO] Failed to load persisted tokens:", err.message);
  }
}

// --- HTTP helpers ---

/**
 * Make an HTTPS request and return the parsed JSON response.
 *
 * @param {string} url - Full URL to request
 * @param {object} options - Node https.request options (method, headers)
 * @param {string|Buffer|null} body - Request body
 * @returns {Promise<object>} Parsed JSON response
 */
function httpsRequest(url, options, body = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => {
        const raw = Buffer.concat(chunks).toString();
        try {
          resolve(JSON.parse(raw));
        } catch {
          resolve({ error: -1, message: raw });
        }
      });
      res.on("error", reject);
    });
    req.on("error", reject);
    if (body) req.write(body);
    req.end();
  });
}

/**
 * Download a file from a URL into a Buffer.
 *
 * @param {string} url - URL to download
 * @returns {Promise<Buffer>} File contents
 */
function downloadBuffer(url) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith("https") ? https : require("http");
    protocol.get(url, (res) => {
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

// --- Token management ---

/**
 * Refresh the OA access token using the stored refresh token.
 * Zalo OA tokens expire after ~24 hours and must be renewed via the refresh grant.
 */
async function refreshAccessToken() {
  console.log("[ZALO] Refreshing access token...");

  const params = new URLSearchParams({
    refresh_token: refreshToken,
    app_id: appId,
    grant_type: "refresh_token",
  });

  const result = await httpsRequest(ZALO_AUTH_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "secret_key": secretKey,
    },
  }, params.toString());

  if (result.access_token) {
    accessToken = result.access_token;
    if (result.refresh_token) refreshToken = result.refresh_token;
    // Zalo tokens typically expire in 86400 seconds (24 hours);
    // refresh 10 minutes early to avoid edge-case failures
    const expiresIn = result.expires_in || 86400;
    tokenExpiresAt = Date.now() + (expiresIn - 600) * 1000;
    persistTokens();
    console.log("[ZALO] Access token refreshed successfully");
  } else {
    console.error("[ZALO] Token refresh failed:", JSON.stringify(result));
    throw new Error(`Token refresh failed: ${result.message || "unknown error"}`);
  }
}

/**
 * Ensure we have a valid access token, refreshing if expired.
 *
 * @returns {Promise<string>} Current valid access token
 */
async function ensureValidToken() {
  if (Date.now() >= tokenExpiresAt) {
    await refreshAccessToken();
  }
  return accessToken;
}

// --- Zalo OA API helpers ---

/**
 * Call the Zalo OA Send Message API.
 *
 * @param {object} payload - JSON body per Zalo OA v3 send-message spec
 * @returns {Promise<object>} API response
 */
async function sendZaloMessage(payload) {
  const token = await ensureValidToken();
  const body = JSON.stringify(payload);

  return httpsRequest(`${ZALO_OA_API_BASE}/message/cs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "access_token": token,
    },
  }, body);
}

/**
 * Upload an image to Zalo OA and return the attachment_id.
 * Zalo requires images to be uploaded first, then referenced by ID in messages.
 *
 * @param {Buffer} imageBuffer - Raw image bytes
 * @param {string} mime - MIME type (e.g. "image/jpeg")
 * @returns {Promise<string|null>} Attachment ID or null on failure
 */
async function uploadImage(imageBuffer, mime) {
  const token = await ensureValidToken();
  const boundary = `----FormBoundary${crypto.randomBytes(8).toString("hex")}`;
  const ext = mime === "image/png" ? "png" : "jpg";
  const filename = `image_${Date.now()}.${ext}`;

  const header = Buffer.from(
    `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${filename}"\r\nContent-Type: ${mime}\r\n\r\n`
  );
  const footer = Buffer.from(`\r\n--${boundary}--\r\n`);
  const body = Buffer.concat([header, imageBuffer, footer]);

  const result = await httpsRequest(`${ZALO_OA_API_BASE}/upload/image`, {
    method: "POST",
    headers: {
      "Content-Type": `multipart/form-data; boundary=${boundary}`,
      "access_token": token,
    },
  }, body);

  if (result.data?.attachment_id) {
    return result.data.attachment_id;
  }
  console.warn("[ZALO] Image upload failed:", JSON.stringify(result));
  return null;
}

/**
 * Upload a file to Zalo OA and return the token for attachment.
 *
 * @param {Buffer} fileBuffer - Raw file bytes
 * @param {string} fileName - Original file name
 * @param {string} mime - MIME type
 * @returns {Promise<string|null>} File token or null on failure
 */
async function uploadFile(fileBuffer, fileName, mime) {
  const token = await ensureValidToken();
  const boundary = `----FormBoundary${crypto.randomBytes(8).toString("hex")}`;

  const header = Buffer.from(
    `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${fileName}"\r\nContent-Type: ${mime}\r\n\r\n`
  );
  const footer = Buffer.from(`\r\n--${boundary}--\r\n`);
  const body = Buffer.concat([header, fileBuffer, footer]);

  const result = await httpsRequest(`${ZALO_OA_API_BASE}/upload/file`, {
    method: "POST",
    headers: {
      "Content-Type": `multipart/form-data; boundary=${boundary}`,
      "access_token": token,
    },
  }, body);

  if (result.data?.token) {
    return result.data.token;
  }
  console.warn("[ZALO] File upload failed:", JSON.stringify(result));
  return null;
}

// --- Webhook signature verification ---

/**
 * Verify the Zalo webhook signature to ensure the request is authentic.
 * Zalo signs webhooks with HMAC-SHA256 using the OA secret key.
 *
 * @param {string} rawBody - Raw request body string
 * @param {string} signature - Value of the X-ZEvent-Signature header
 * @returns {boolean} True if signature is valid
 */
function verifyWebhookSignature(rawBody, signature) {
  if (!secretKey || !signature) return false;
  const expected = "mac=" + crypto
    .createHmac("sha256", secretKey)
    .update(rawBody)
    .digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(expected, "utf8"),
    Buffer.from(signature, "utf8")
  );
}

// --- Send hooks ---

connector.setSendHooks({
  /**
   * Send a plain text message to a Zalo user.
   *
   * @param {string} chatId - Zalo user ID
   * @param {string} text - Message text
   */
  async sendText(chatId, text) {
    const result = await sendZaloMessage({
      recipient: { user_id: chatId },
      message: { text },
    });
    if (result.error && result.error !== 0) {
      console.warn("[ZALO] sendText error:", JSON.stringify(result));
    }
  },

  /**
   * Upload an image and send it with an optional caption.
   *
   * @param {string} chatId - Zalo user ID
   * @param {string} caption - Optional caption text
   * @param {Buffer} imageBuffer - Raw image bytes
   * @param {string} mime - Image MIME type
   */
  async sendImage(chatId, caption, imageBuffer, mime) {
    const attachmentId = await uploadImage(imageBuffer, mime);
    if (!attachmentId) {
      if (caption) await this.sendText(chatId, caption);
      return;
    }

    const result = await sendZaloMessage({
      recipient: { user_id: chatId },
      message: {
        attachment: {
          type: "template",
          payload: {
            template_type: "media",
            elements: [{
              media_type: "image",
              attachment_id: attachmentId,
            }],
          },
        },
      },
    });

    if (result.error && result.error !== 0) {
      console.warn("[ZALO] sendImage error:", JSON.stringify(result));
    }

    // Zalo OA image messages don't support inline captions; send separately
    if (caption) {
      await this.sendText(chatId, caption);
    }
  },

  /**
   * Upload a document and send it to the user.
   *
   * @param {string} chatId - Zalo user ID
   * @param {object} doc - Document details
   * @param {Buffer} doc.buffer - File bytes
   * @param {string} doc.fileName - Original filename
   * @param {string} doc.mime - MIME type
   * @param {string} doc.caption - Optional caption
   */
  async sendDocument(chatId, { buffer, fileName, mime, caption }) {
    const fileToken = await uploadFile(buffer, fileName, mime);
    if (!fileToken) {
      if (caption) await this.sendText(chatId, `[Document: ${fileName}] ${caption}`);
      return;
    }

    const result = await sendZaloMessage({
      recipient: { user_id: chatId },
      message: {
        attachment: {
          type: "file",
          payload: { token: fileToken },
        },
      },
    });

    if (result.error && result.error !== 0) {
      console.warn("[ZALO] sendDocument error:", JSON.stringify(result));
    }

    if (caption) {
      await this.sendText(chatId, caption);
    }
  },

  /**
   * Send typing indicator. Zalo OA API v3 supports typing actions.
   *
   * @param {string} chatId - Zalo user ID
   */
  async sendTyping(chatId) {
    const token = await ensureValidToken();
    await httpsRequest(`${ZALO_OA_API_BASE}/message/typing`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "access_token": token,
      },
    }, JSON.stringify({
      recipient: { user_id: chatId },
      sender_action: "typing",
    }));
  },
});

// --- Webhook server ---

/**
 * Start the Express server that receives Zalo webhook callbacks.
 * Zalo pushes events (user_send_text, user_send_image, etc.) to this endpoint.
 */
function startWebhookServer() {
  const app = express();
  const port = connector.config.webhook_port || 3200;

  // Parse raw body for signature verification, then JSON
  app.use(express.json({
    verify: (req, _res, buf) => {
      req.rawBody = buf.toString();
    },
  }));

  // Health check endpoint
  app.get("/", (_req, res) => {
    res.json({ status: "ok", connector: "zalo" });
  });

  // Zalo webhook endpoint
  app.post("/webhook", async (req, res) => {
    // Zalo expects a 200 response quickly to avoid retries
    res.status(200).json({ status: "ok" });

    const signature = req.headers["x-zevent-signature"] || "";
    if (secretKey && !verifyWebhookSignature(req.rawBody, signature)) {
      console.warn("[ZALO] Invalid webhook signature, ignoring event");
      return;
    }

    await handleWebhookEvent(req.body);
  });

  app.listen(port, () => {
    console.log(`[ZALO] Webhook server listening on port ${port}`);
  });
}

// --- Incoming message handling ---

/**
 * Extract the user-facing text from a Zalo webhook event body.
 *
 * @param {object} event - Zalo webhook event
 * @returns {string} Extracted text
 */
function extractText(event) {
  return event.message?.text || "";
}

/**
 * Route a Zalo webhook event to the appropriate handler.
 *
 * @param {object} event - Full Zalo webhook event payload
 */
async function handleWebhookEvent(event) {
  const eventName = event.event_name || "";
  const senderId = event.sender?.id || event.user_id_by_app || "";
  const timestamp = event.timestamp || Date.now();

  if (!senderId) {
    console.warn("[ZALO] Event without sender ID:", eventName);
    return;
  }

  // Zalo OA is always 1:1, so chatId === senderId
  const chatId = String(senderId);

  switch (eventName) {
    case "user_send_text": {
      const text = extractText(event);
      if (!text) return;

      console.log(`[ZALO] ${chatId}: ${text.substring(0, 100)}`);
      await connector.handleIncoming({
        chatId,
        senderId: chatId,
        senderName: "",
        text,
        extra: { timestamp },
      });
      break;
    }

    case "user_send_image": {
      const text = extractText(event);
      const imageUrl = event.message?.attachments?.[0]?.payload?.url || "";

      let media = null;
      if (imageUrl) {
        try {
          const buffer = await downloadBuffer(imageUrl);
          const mediaPath = await connector.saveMediaBuffer(buffer, "image");
          media = {
            type: "image",
            path: mediaPath,
            mime: "image/jpeg",
            size: buffer.length,
            buffer,
          };
        } catch (err) {
          console.warn("[ZALO] Failed to download image:", err.message);
        }
      }

      await connector.handleIncoming({
        chatId,
        senderId: chatId,
        senderName: "",
        text,
        media,
        extra: { timestamp },
      });
      break;
    }

    case "user_send_file": {
      const text = extractText(event);
      const fileUrl = event.message?.attachments?.[0]?.payload?.url || "";
      const fileName = event.message?.attachments?.[0]?.payload?.name || "document";

      let media = null;
      if (fileUrl) {
        try {
          const buffer = await downloadBuffer(fileUrl);
          const mediaPath = await connector.saveMediaBuffer(buffer, "document");
          media = {
            type: "document",
            path: mediaPath,
            mime: "application/octet-stream",
            size: buffer.length,
            buffer,
          };
        } catch (err) {
          console.warn("[ZALO] Failed to download file:", err.message);
        }
      }

      await connector.handleIncoming({
        chatId,
        senderId: chatId,
        senderName: "",
        text: text || `[Document: ${fileName}]`,
        media,
        extra: { timestamp, file_name: fileName },
      });
      break;
    }

    case "follow":
    case "unfollow": {
      console.log(`[ZALO] User ${chatId} ${eventName}ed the OA`);
      break;
    }

    default: {
      console.log(`[ZALO] Unhandled event: ${eventName}`);
      break;
    }
  }
}

// --- Main ---

async function main() {
  const configFile = path.join(__dirname, "config.json");
  if (!fs.existsSync(configFile)) {
    console.error("[ZALO] FATAL: No config.json found. Copy config-template.json to config.json and fill in your values.");
    process.exit(1);
  }

  const rawConfig = JSON.parse(fs.readFileSync(configFile, "utf8"));
  appId = rawConfig.app_id || "";
  secretKey = rawConfig.secret_key || "";

  if (!appId || !secretKey) {
    console.error("[ZALO] FATAL: app_id and secret_key are required in config.json.");
    process.exit(1);
  }

  // Load tokens: prefer persisted tokens, fall back to config
  loadPersistedTokens();
  if (!accessToken) accessToken = rawConfig.access_token || "";
  if (!refreshToken) refreshToken = rawConfig.refresh_token || "";

  if (!accessToken && !refreshToken) {
    console.error("[ZALO] FATAL: At least one of access_token or refresh_token is required.");
    process.exit(1);
  }

  // If we have a refresh token but the access token is expired or missing, refresh now
  if (refreshToken && (!accessToken || Date.now() >= tokenExpiresAt)) {
    try {
      await refreshAccessToken();
    } catch (err) {
      if (!accessToken) {
        console.error("[ZALO] FATAL: Cannot obtain a valid access token:", err.message);
        process.exit(1);
      }
      // We have an access token from config; it might still be valid
      console.warn("[ZALO] Token refresh failed, using configured access token");
    }
  }

  await connector.start({ webhook_port: 3200 });
  startWebhookServer();
  console.log("[ZALO] Connector running. Send a Zalo message to the OA to interact with the brain.");
}

main().catch((err) => {
  console.error("[ZALO] Fatal:", err);
  process.exit(1);
});
