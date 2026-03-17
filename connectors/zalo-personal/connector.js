/**
 * Zalo Personal Connector — bridges personal Zalo messages to the Sentient brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Zalo personal account integration via zca-js (Zalo Client API).
 *
 * First run: displays QR code URL in terminal for Zalo mobile app scanning.
 * Session persists in ./auth_store/ so subsequent runs reconnect automatically.
 *
 * Supports both 1:1 and group conversations.
 */

const { Zalo, MessageType, ThreadType } = require("zca-js");
const ConnectorBase = require("../lib/connector-base");
const path = require("path");
const fs = require("fs");
const https = require("https");

const AUTH_DIR = path.join(__dirname, "auth_store");
const CREDENTIALS_FILE = path.join(__dirname, ".zalo_credentials.json");

const connector = new ConnectorBase("zalo-personal", __dirname);

// Group detection: zca-js group threads have a numeric ID that differs from user IDs.
// We track known group IDs discovered at runtime.
const knownGroupIds = new Set();

connector.setGroupDetector((chatId) => knownGroupIds.has(String(chatId)));

let zaloApi = null;

// --- Credential persistence ---

/**
 * Save Zalo login credentials (cookies + IMEI) to disk so the session
 * survives restarts without re-scanning the QR code.
 *
 * @param {object} credentials - Credentials object from zca-js login
 */
function persistCredentials(credentials) {
  try {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
    fs.writeFileSync(CREDENTIALS_FILE, JSON.stringify(credentials, null, 2));
    console.log("[ZALO-P] Credentials saved");
  } catch (err) {
    console.warn("[ZALO-P] Failed to save credentials:", err.message);
  }
}

/**
 * Load previously saved credentials from disk.
 *
 * @returns {object|null} Saved credentials or null
 */
function loadCredentials() {
  try {
    if (fs.existsSync(CREDENTIALS_FILE)) {
      const data = JSON.parse(fs.readFileSync(CREDENTIALS_FILE, "utf8"));
      console.log("[ZALO-P] Loaded saved credentials");
      return data;
    }
  } catch (err) {
    console.warn("[ZALO-P] Failed to load credentials:", err.message);
  }
  return null;
}

// --- HTTP helper ---

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

// --- Send hooks ---

connector.setSendHooks({
  /**
   * Send a plain text message to a Zalo user or group.
   *
   * @param {string} chatId - Thread ID (user or group)
   * @param {string} text - Message text
   */
  async sendText(chatId, text) {
    if (!zaloApi) return;

    const threadType = knownGroupIds.has(chatId)
      ? ThreadType.Group
      : ThreadType.User;

    try {
      await zaloApi.sendMessage(
        { msg: text, mentions: [] },
        chatId,
        threadType
      );
    } catch (err) {
      console.error("[ZALO-P] sendText error:", err.message);
      throw err;
    }
  },

  /**
   * Send an image to a Zalo user or group.
   * zca-js supports sending images as file paths or base64-encoded data.
   *
   * @param {string} chatId - Thread ID
   * @param {string} caption - Optional caption
   * @param {Buffer} imageBuffer - Raw image bytes
   * @param {string} mime - Image MIME type
   */
  async sendImage(chatId, caption, imageBuffer, mime) {
    if (!zaloApi) return;

    const threadType = knownGroupIds.has(chatId)
      ? ThreadType.Group
      : ThreadType.User;

    // Save image to a temp file for zca-js (it prefers file paths)
    const ext = mime === "image/png" ? "png" : "jpg";
    const tempPath = path.join(AUTH_DIR, `send_${Date.now()}.${ext}`);

    try {
      fs.mkdirSync(AUTH_DIR, { recursive: true });
      fs.writeFileSync(tempPath, imageBuffer);

      await zaloApi.sendMessage(
        {
          msg: caption || "",
          attachments: [tempPath],
        },
        chatId,
        threadType
      );
    } catch (err) {
      console.error("[ZALO-P] sendImage error:", err.message);
      // Fall back to sending caption as text if image fails
      if (caption) {
        try { await this.sendText(chatId, caption); } catch (_) {}
      }
    } finally {
      // Clean up temp file
      try { fs.unlinkSync(tempPath); } catch (_) {}
    }
  },

  /**
   * Send typing indicator in a Zalo conversation.
   *
   * @param {string} chatId - Thread ID
   */
  async sendTyping(chatId) {
    // zca-js does not expose a public typing indicator API;
    // this is a no-op placeholder for interface compatibility
  },
});

// --- QR Login ---

/**
 * Perform QR code login for Zalo personal account.
 * Displays a URL that the user opens/scans with their Zalo mobile app.
 *
 * @param {Zalo} zalo - Zalo client instance
 * @returns {Promise<object>} API instance from successful login
 */
async function performQRLogin(zalo) {
  console.log("\n[ZALO-P] Starting QR code login...");
  console.log("[ZALO-P] A QR code URL will be displayed. Open it in your browser and scan with Zalo app.\n");

  const api = await zalo.login({
    onQRCodeGenerated: (qrUrl) => {
      console.log("[ZALO-P] ==========================================");
      console.log("[ZALO-P] Scan this QR code with your Zalo app:");
      console.log(`[ZALO-P] ${qrUrl}`);
      console.log("[ZALO-P] ==========================================\n");
    },
  });

  return api;
}

// --- Zalo connection ---

/**
 * Initialize the Zalo client, authenticate (QR or saved session),
 * and set up message listeners.
 */
async function startZalo() {
  const zalo = new Zalo();
  const savedCredentials = loadCredentials();

  try {
    if (savedCredentials) {
      console.log("[ZALO-P] Attempting login with saved credentials...");
      try {
        zaloApi = await zalo.login({
          credentials: savedCredentials,
        });
        console.log("[ZALO-P] Logged in with saved credentials");
      } catch (err) {
        console.warn("[ZALO-P] Saved credentials expired, falling back to QR login:", err.message);
        zaloApi = await performQRLogin(zalo);
      }
    } else {
      zaloApi = await performQRLogin(zalo);
    }
  } catch (err) {
    console.error("[ZALO-P] Login failed:", err.message);
    throw err;
  }

  // Save credentials for next restart
  try {
    const credentials = zaloApi.getCredentials();
    if (credentials) {
      persistCredentials(credentials);
    }
  } catch (err) {
    console.warn("[ZALO-P] Could not extract credentials for persistence:", err.message);
  }

  console.log("[ZALO-P] Connected to Zalo");

  // Listen for incoming messages
  zaloApi.listener.on("message", async (event) => {
    try {
      await handleIncomingMessage(event);
    } catch (err) {
      console.error("[ZALO-P] Error handling message:", err.message);
    }
  });

  // Listen for group events to discover group IDs
  zaloApi.listener.on("group_event", (event) => {
    if (event.threadId) {
      knownGroupIds.add(String(event.threadId));
    }
  });

  // Handle disconnection and reconnection
  zaloApi.listener.on("error", (err) => {
    console.error("[ZALO-P] Listener error:", err.message);
  });

  zaloApi.listener.on("close", () => {
    console.warn("[ZALO-P] Connection closed. Attempting reconnect in 5s...");
    setTimeout(() => {
      startZalo().catch((err) => {
        console.error("[ZALO-P] Reconnect failed:", err.message);
        process.exit(1);
      });
    }, 5000);
  });

  // Start the real-time listener (WebSocket)
  await zaloApi.listener.start();
  console.log("[ZALO-P] Message listener started");
}

// --- Incoming message handling ---

/**
 * Process an incoming Zalo message event from zca-js.
 *
 * @param {object} event - Message event from zca-js listener
 */
async function handleIncomingMessage(event) {
  const threadId = String(event.threadId || "");
  const senderId = String(event.uidFrom || event.senderId || "");
  const isGroupMessage = event.type === ThreadType.Group || event.isGroup;

  if (!threadId || !senderId) return;

  // Track group IDs as we discover them
  if (isGroupMessage) {
    knownGroupIds.add(threadId);
  }

  // Skip our own messages
  const selfId = zaloApi.getOwnId ? String(zaloApi.getOwnId()) : "";
  if (selfId && senderId === selfId) return;

  const chatId = isGroupMessage ? threadId : senderId;
  const text = event.data?.content || event.data?.msg || event.content || "";

  // Determine media type
  let media = null;
  const msgType = event.data?.msgType || event.msgType || "";

  if (msgType === MessageType.Image || msgType === "image") {
    const imageUrl = event.data?.thumb || event.data?.hdUrl || event.data?.url || "";
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
        console.warn("[ZALO-P] Failed to download image:", err.message);
      }
    }
  } else if (msgType === MessageType.File || msgType === "file") {
    const fileUrl = event.data?.href || event.data?.url || "";
    const fileName = event.data?.fileName || "document";
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
        console.warn("[ZALO-P] Failed to download file:", err.message);
      }
    }
  }

  // Build the sender name from available data
  const senderName = event.data?.senderName || event.senderName || "";

  const normalized = {
    chatId,
    senderId,
    senderName,
    text,
    media,
    extra: {
      thread_id: threadId,
      msg_id: event.data?.msgId || event.msgId || "",
      is_group: isGroupMessage,
    },
  };

  await connector.handleIncoming(normalized);
}

// --- Main ---

async function main() {
  // Pre-populate known group IDs from config
  const configPath = path.join(__dirname, "config.json");
  if (fs.existsSync(configPath)) {
    try {
      const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
      const groups = [
        ...(cfg.whitelisted_groups || []),
        ...(cfg.monitor_groups || []),
      ];
      for (const gid of groups) {
        knownGroupIds.add(String(gid));
      }
    } catch (_) {}
  }

  await connector.start();
  await startZalo();
  console.log("[ZALO-P] Connector running. Send a Zalo message to interact with the brain.");
}

main().catch((err) => {
  console.error("[ZALO-P] Fatal:", err);
  process.exit(1);
});
