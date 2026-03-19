/**
 * WebChat Connector — browser-based chat UI bridging to the Arqitect brain
 * via Redis and WebSocket.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles the Express HTTP server and WebSocket real-time messaging.
 *
 * Auth: none by default (open access), or session-based via whitelisted_users
 */

const express = require("express");
const http = require("http");
const https = require("https");
const { WebSocketServer } = require("ws");
const crypto = require("crypto");
const ConnectorBase = require("../lib/connector-base");
const path = require("path");
const fs = require("fs");

const connector = new ConnectorBase("webchat", __dirname);

// --- Config ---

const configFile = path.join(__dirname, "config.json");
let serverPort = 3100;
let corsOrigins = "*";

if (fs.existsSync(configFile)) {
  try {
    const loaded = JSON.parse(fs.readFileSync(configFile, "utf8"));
    serverPort = loaded.port || 3100;
    corsOrigins = loaded.cors_origins || "*";
  } catch (_) {}
}

// --- WebSocket session tracking ---

/** @type {Map<string, import("ws").WebSocket>} sessionId -> WebSocket */
const sessions = new Map();

// --- No group concept — every WebSocket connection is a 1:1 chat ---

connector.setGroupDetector(() => false);

// --- Send hooks ---

/**
 * Find the WebSocket connection for a given session/chat ID.
 * @param {string} chatId - Session ID
 * @returns {import("ws").WebSocket | null} The WebSocket or null if disconnected
 */
function getSocket(chatId) {
  const ws = sessions.get(chatId);
  if (!ws || ws.readyState !== ws.OPEN) return null;
  return ws;
}

/**
 * Send a JSON envelope over WebSocket to the given session.
 * @param {string} chatId - Session ID
 * @param {object} payload - JSON-serializable data
 */
function wsSend(chatId, payload) {
  const ws = getSocket(chatId);
  if (!ws) {
    console.warn(`[WEBCHAT] No open socket for session ${chatId}`);
    return;
  }
  ws.send(JSON.stringify(payload));
}

connector.setSendHooks({
  /**
   * Send a text message to the browser client.
   * @param {string} chatId - Session ID
   * @param {string} text - Message text
   */
  async sendText(chatId, text) {
    wsSend(chatId, { type: "text", text });
  },

  /**
   * Send an image to the browser client as base64.
   * @param {string} chatId - Session ID
   * @param {string} caption - Image caption
   * @param {Buffer} imageBuffer - Image data
   * @param {string} mime - MIME type
   */
  async sendImage(chatId, caption, imageBuffer, mime) {
    const base64 = imageBuffer.toString("base64");
    wsSend(chatId, {
      type: "image",
      data: base64,
      mime: mime || "image/png",
      caption: caption || "",
    });
  },

  /**
   * Send an audio clip to the browser client as base64.
   * @param {string} chatId - Session ID
   * @param {string} text - Accompanying text
   * @param {Buffer} audioBuffer - Audio data
   * @param {string} mime - MIME type
   */
  async sendAudio(chatId, text, audioBuffer, mime) {
    const base64 = audioBuffer.toString("base64");
    wsSend(chatId, {
      type: "audio",
      data: base64,
      mime: mime || "audio/mp4",
      text: text || "",
    });
  },

  /**
   * Send a document to the browser client as base64.
   * @param {string} chatId - Session ID
   * @param {object} doc - Document descriptor
   * @param {Buffer} doc.buffer - File data
   * @param {string} doc.fileName - File name
   * @param {string} doc.mime - MIME type
   * @param {string} doc.caption - Caption text
   */
  async sendDocument(chatId, { buffer, fileName, mime, caption }) {
    const base64 = buffer.toString("base64");
    wsSend(chatId, {
      type: "document",
      data: base64,
      fileName: fileName || "document",
      mime: mime || "application/octet-stream",
      caption: caption || "",
    });
  },

  /**
   * Send a structured card to the browser client.
   * @param {string} chatId - Session ID
   * @param {object} card - Card object with title, body, footer
   * @param {string} text - Fallback text
   */
  async sendCard(chatId, card, text) {
    wsSend(chatId, {
      type: "card",
      card,
      text: text || "",
    });
  },

  /**
   * Send a typing indicator to the browser client.
   * @param {string} chatId - Session ID
   */
  async sendTyping(chatId) {
    wsSend(chatId, { type: "typing", active: true });
  },

  /**
   * Clear the typing indicator for the browser client.
   * @param {string} chatId - Session ID
   */
  async clearTyping(chatId) {
    wsSend(chatId, { type: "typing", active: false });
  },
});

// --- Chat UI HTML ---

/**
 * Generate the self-contained chat UI HTML page.
 * The page opens a WebSocket connection and provides a minimal chat interface.
 * @returns {string} Complete HTML page
 */
function buildChatHtml() {
  const botName = connector.config.bot_name || "Arqitect";
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${botName} Chat</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; height: 100vh; display: flex; flex-direction: column; }
  #header { background: #2c3e50; color: white; padding: 16px 20px; font-size: 18px; font-weight: 600; }
  #messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 8px; }
  .msg { max-width: 70%; padding: 10px 14px; border-radius: 12px; line-height: 1.4; word-wrap: break-word; }
  .msg.user { align-self: flex-end; background: #007bff; color: white; border-bottom-right-radius: 4px; }
  .msg.bot { align-self: flex-start; background: white; color: #333; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
  .msg.bot .card-title { font-weight: 700; margin-bottom: 4px; }
  .msg.bot .card-footer { font-style: italic; color: #666; margin-top: 4px; font-size: 0.9em; }
  .msg.bot img { max-width: 100%; border-radius: 8px; margin-top: 4px; }
  .msg.bot audio { margin-top: 4px; width: 100%; }
  .typing { align-self: flex-start; color: #888; font-style: italic; padding: 4px 14px; }
  #input-area { display: flex; padding: 12px 20px; background: white; border-top: 1px solid #ddd; gap: 8px; }
  #input-area input[type="text"] { flex: 1; padding: 10px 14px; border: 1px solid #ccc; border-radius: 20px; font-size: 14px; outline: none; }
  #input-area input[type="text"]:focus { border-color: #007bff; }
  #input-area button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 20px; cursor: pointer; font-size: 14px; }
  #input-area button:hover { background: #0056b3; }
  #input-area label { display: flex; align-items: center; cursor: pointer; color: #666; font-size: 20px; }
  #input-area input[type="file"] { display: none; }
</style>
</head>
<body>
<div id="header">${botName}</div>
<div id="messages"></div>
<div id="input-area">
  <label title="Attach file"><span>&#128206;</span><input type="file" id="file-input"></label>
  <input type="text" id="msg-input" placeholder="Type a message..." autocomplete="off">
  <button id="send-btn">Send</button>
</div>
<script>
(function() {
  const messagesEl = document.getElementById("messages");
  const msgInput = document.getElementById("msg-input");
  const sendBtn = document.getElementById("send-btn");
  const fileInput = document.getElementById("file-input");
  let typingEl = null;

  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(proto + "//" + location.host + "/ws");

  function addMessage(text, cls) {
    const div = document.createElement("div");
    div.className = "msg " + cls;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addHtmlMessage(html, cls) {
    const div = document.createElement("div");
    div.className = "msg " + cls;
    div.innerHTML = html;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showTyping(active) {
    if (active && !typingEl) {
      typingEl = document.createElement("div");
      typingEl.className = "typing";
      typingEl.textContent = "typing...";
      messagesEl.appendChild(typingEl);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    } else if (!active && typingEl) {
      typingEl.remove();
      typingEl = null;
    }
  }

  ws.onmessage = function(ev) {
    showTyping(false);
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === "typing") { showTyping(msg.active); return; }
      if (msg.type === "text") { addMessage(msg.text, "bot"); return; }
      if (msg.type === "image") {
        const cap = msg.caption ? "<p>" + msg.caption + "</p>" : "";
        addHtmlMessage(cap + '<img src="data:' + msg.mime + ';base64,' + msg.data + '">', "bot");
        return;
      }
      if (msg.type === "audio") {
        const txt = msg.text ? "<p>" + msg.text + "</p>" : "";
        addHtmlMessage(txt + '<audio controls src="data:' + msg.mime + ';base64,' + msg.data + '"></audio>', "bot");
        return;
      }
      if (msg.type === "document") {
        const href = "data:" + msg.mime + ";base64," + msg.data;
        addHtmlMessage('<a href="' + href + '" download="' + msg.fileName + '">Download: ' + msg.fileName + '</a>' + (msg.caption ? "<p>" + msg.caption + "</p>" : ""), "bot");
        return;
      }
      if (msg.type === "card") {
        let html = "";
        if (msg.card.title) html += '<div class="card-title">' + msg.card.title + '</div>';
        html += "<div>" + (msg.card.body || msg.text || "") + "</div>";
        if (msg.card.footer) html += '<div class="card-footer">' + msg.card.footer + '</div>';
        addHtmlMessage(html, "bot");
        return;
      }
    } catch(e) {
      addMessage(ev.data, "bot");
    }
  };

  ws.onclose = function() { addMessage("Connection closed.", "bot"); };

  function sendText() {
    const text = msgInput.value.trim();
    if (!text || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "text", text: text }));
    addMessage(text, "user");
    msgInput.value = "";
  }

  sendBtn.addEventListener("click", sendText);
  msgInput.addEventListener("keydown", function(e) { if (e.key === "Enter") sendText(); });

  fileInput.addEventListener("change", function() {
    const file = fileInput.files[0];
    if (!file || ws.readyState !== WebSocket.OPEN) return;
    const reader = new FileReader();
    reader.onload = function() {
      const base64 = reader.result.split(",")[1];
      ws.send(JSON.stringify({ type: "file", name: file.name, mime: file.type, data: base64 }));
      addMessage("Sent file: " + file.name, "user");
    };
    reader.readAsDataURL(file);
    fileInput.value = "";
  });
})();
</script>
</body>
</html>`;
}

// --- Express + WebSocket server ---
const SSL_CERT = process.env.SSL_CERT || "";
const SSL_KEY = process.env.SSL_KEY || "";

const app = express();
const server = (SSL_CERT && SSL_KEY)
  ? https.createServer({ cert: fs.readFileSync(SSL_CERT), key: fs.readFileSync(SSL_KEY) }, app)
  : http.createServer(app);
const wss = new WebSocketServer({ server, path: "/ws" });

// CORS middleware
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", corsOrigins);
  res.header("Access-Control-Allow-Headers", "Content-Type");
  next();
});

/** Serve the chat UI page. */
app.get("/", (_req, res) => {
  res.type("html").send(buildChatHtml());
});

/** Health check endpoint. */
app.get("/health", (_req, res) => {
  res.json({ status: "ok", sessions: sessions.size });
});

// --- WebSocket connection handler ---

wss.on("connection", (ws) => {
  const sessionId = crypto.randomUUID();
  sessions.set(sessionId, ws);
  console.log(`[WEBCHAT] New session: ${sessionId} (${sessions.size} active)`);

  ws.on("message", async (raw) => {
    try {
      const message = parseIncomingMessage(raw);
      if (!message) return;

      const normalized = buildNormalizedMessage(sessionId, message);
      await connector.handleIncoming(normalized);
    } catch (err) {
      console.error(`[WEBCHAT] Error handling message from ${sessionId}:`, err.message);
    }
  });

  ws.on("close", () => {
    sessions.delete(sessionId);
    console.log(`[WEBCHAT] Session closed: ${sessionId} (${sessions.size} active)`);
  });

  ws.on("error", (err) => {
    console.warn(`[WEBCHAT] Socket error for ${sessionId}: ${err.message}`);
    sessions.delete(sessionId);
  });
});

// --- Message parsing ---

/**
 * Parse an incoming WebSocket message into a structured object.
 * Supports JSON text frames (type: "text" or "file") and raw binary frames.
 * @param {Buffer|string} raw - Raw WebSocket message data
 * @returns {{ type: string, text?: string, name?: string, mime?: string, data?: string, buffer?: Buffer } | null}
 */
function parseIncomingMessage(raw) {
  // Binary frame: treat as raw file upload
  if (Buffer.isBuffer(raw) && !isJsonBuffer(raw)) {
    return { type: "binary", buffer: raw };
  }

  const str = raw.toString("utf8");
  try {
    const parsed = JSON.parse(str);
    if (parsed.type === "text" && parsed.text) {
      return { type: "text", text: parsed.text };
    }
    if (parsed.type === "file" && parsed.data) {
      return {
        type: "file",
        name: parsed.name || "upload",
        mime: parsed.mime || "application/octet-stream",
        data: parsed.data,
        buffer: Buffer.from(parsed.data, "base64"),
      };
    }
    return null;
  } catch (_) {
    // Plain text fallback
    if (str.trim()) return { type: "text", text: str.trim() };
    return null;
  }
}

/**
 * Check whether a buffer looks like it starts with JSON.
 * @param {Buffer} buf - Buffer to check
 * @returns {boolean}
 */
function isJsonBuffer(buf) {
  if (buf.length === 0) return false;
  const firstByte = buf[0];
  // '{' = 123, '[' = 91
  return firstByte === 123 || firstByte === 91;
}

/**
 * Build a ConnectorBase-normalized message from a parsed WebSocket message.
 * @param {string} sessionId - WebSocket session ID
 * @param {object} message - Parsed message from parseIncomingMessage
 * @returns {object} Normalized message for connector.handleIncoming
 */
function buildNormalizedMessage(sessionId, message) {
  const normalized = {
    chatId: sessionId,
    senderId: sessionId,
    senderName: `user-${sessionId.substring(0, 8)}`,
    text: message.text || "",
    extra: {
      session_id: sessionId,
    },
  };

  if (message.type === "file" && message.buffer) {
    const mediaType = classifyMime(message.mime);
    normalized.media = {
      type: mediaType,
      path: "",
      mime: message.mime,
      size: message.buffer.length,
      buffer: message.buffer,
    };
    if (!normalized.text) {
      normalized.text = `[Uploaded ${message.name || "file"}]`;
    }
  }

  if (message.type === "binary" && message.buffer) {
    normalized.media = {
      type: "document",
      path: "",
      mime: "application/octet-stream",
      size: message.buffer.length,
      buffer: message.buffer,
    };
    if (!normalized.text) {
      normalized.text = "[Uploaded binary file]";
    }
  }

  return normalized;
}

/**
 * Classify a MIME type into a media category.
 * @param {string} mime - MIME type string
 * @returns {string} Media category: "image", "audio", "video", or "document"
 */
function classifyMime(mime) {
  const lower = (mime || "").toLowerCase();
  if (lower.startsWith("image/")) return "image";
  if (lower.startsWith("audio/")) return "audio";
  if (lower.startsWith("video/")) return "video";
  return "document";
}

// --- Main ---

/**
 * Boot the WebChat connector: start ConnectorBase (Redis, config),
 * then launch the HTTP + WebSocket server.
 */
async function main() {
  await connector.start();

  const port = connector.config.port || serverPort;
  const scheme = SSL_CERT ? "https" : "http";
  const wsScheme = SSL_CERT ? "wss" : "ws";
  server.listen(port, () => {
    console.log(`[WEBCHAT] Server running on ${scheme}://localhost:${port}`);
    console.log(`[WEBCHAT] Chat UI at ${scheme}://localhost:${port}/`);
    console.log(`[WEBCHAT] WebSocket endpoint at ${wsScheme}://localhost:${port}/ws`);
  });

  process.once("SIGINT", () => {
    console.log("[WEBCHAT] Shutting down...");
    wss.clients.forEach((ws) => ws.close());
    server.close();
    process.exit(0);
  });
  process.once("SIGTERM", () => {
    console.log("[WEBCHAT] Shutting down...");
    wss.clients.forEach((ws) => ws.close());
    server.close();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("[WEBCHAT] Fatal:", err);
  process.exit(1);
});
