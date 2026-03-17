/**
 * iMessage Connector (imsg) — bridges iMessage on macOS to Sentient brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles macOS-specific iMessage integration via:
 *   - SQLite polling of ~/Library/Messages/chat.db for incoming messages
 *   - AppleScript (osascript) for sending outgoing messages
 *
 * Requirements:
 *   - macOS with Messages.app configured
 *   - Full Disk Access granted to the terminal/process running this connector
 *     (System Settings > Privacy & Security > Full Disk Access)
 *   - better-sqlite3 npm package for reading chat.db
 */

const { execFile } = require("child_process");
const { promisify } = require("util");
const path = require("path");
const fs = require("fs");
const os = require("os");
const ConnectorBase = require("../lib/connector-base");

const execFileAsync = promisify(execFile);

const CHAT_DB_PATH = path.join(os.homedir(), "Library", "Messages", "chat.db");
const ATTACHMENTS_BASE = path.join(os.homedir(), "Library", "Messages", "Attachments");

const connector = new ConnectorBase("imessage-imsg", __dirname);

/** @type {import('better-sqlite3').Database | null} */
let db = null;

/** ROWID of the last processed message — only messages after this are handled. */
let lastRowId = 0;

/** Polling timer reference for cleanup. */
let pollTimer = null;

// ---------------------------------------------------------------------------
// Group detection — iMessage group chats use "chat" identifiers that contain
// multiple participants. We detect them by the chat_identifier format.
// ---------------------------------------------------------------------------

/** @type {Map<string, boolean>} chatId -> isGroup cache */
const groupCache = new Map();

connector.setGroupDetector((chatId) => groupCache.get(String(chatId)) === true);

// ---------------------------------------------------------------------------
// SQLite helpers
// ---------------------------------------------------------------------------

/**
 * Open the Messages SQLite database in read-only mode.
 * Throws if the file is inaccessible (Full Disk Access not granted).
 *
 * @returns {import('better-sqlite3').Database}
 */
function openDatabase() {
  // eslint-disable-next-line global-require
  const Database = require("better-sqlite3");
  return new Database(CHAT_DB_PATH, { readonly: true, fileMustExist: true });
}

/**
 * Seed lastRowId to the current maximum so we only process new messages.
 */
function seedLastRowId() {
  const row = db.prepare("SELECT MAX(ROWID) AS maxId FROM message").get();
  lastRowId = row?.maxId ?? 0;
  console.log(`[IMSG] Seeded lastRowId = ${lastRowId}`);
}

/**
 * Determine whether a chat_identifier represents a group conversation.
 * Group chats in iMessage typically have "chat" in their identifier and are
 * flagged with style = 43 (group) in the chat table.
 *
 * @param {string} chatIdentifier
 * @param {number} chatStyle
 * @returns {boolean}
 */
function isGroupIdentifier(chatIdentifier, chatStyle) {
  if (chatStyle === 43) return true;
  if (chatIdentifier.startsWith("chat")) return true;
  return false;
}

// ---------------------------------------------------------------------------
// Attachment helpers
// ---------------------------------------------------------------------------

/**
 * Resolve the real filesystem path for an attachment filename stored in chat.db.
 * iMessage stores paths with a leading "~/" or as absolute paths.
 *
 * @param {string} rawPath - The filename column from the attachment table.
 * @returns {string} Absolute path on disk.
 */
function resolveAttachmentPath(rawPath) {
  if (rawPath.startsWith("~/")) {
    return path.join(os.homedir(), rawPath.slice(2));
  }
  return rawPath;
}

/**
 * Classify an attachment MIME type into the media categories the brain understands.
 *
 * @param {string} mime
 * @returns {'image' | 'audio' | 'video' | 'document'}
 */
function classifyMime(mime) {
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("audio/")) return "audio";
  if (mime.startsWith("video/")) return "video";
  return "document";
}

/**
 * Load attachment metadata and file buffer for a given message ROWID.
 *
 * @param {number} messageRowId
 * @returns {{ type: string, path: string, mime: string, size: number, buffer: Buffer } | null}
 */
function loadAttachment(messageRowId) {
  const row = db.prepare(`
    SELECT a.filename, a.mime_type, a.total_bytes
    FROM attachment a
    JOIN message_attachment_join maj ON maj.attachment_id = a.ROWID
    WHERE maj.message_id = ?
    ORDER BY a.ROWID ASC
    LIMIT 1
  `).get(messageRowId);

  if (!row || !row.filename) return null;

  const absPath = resolveAttachmentPath(row.filename);
  try {
    const buffer = fs.readFileSync(absPath);
    const mediaType = classifyMime(row.mime_type || "application/octet-stream");
    return {
      type: mediaType,
      path: absPath,
      mime: row.mime_type || "application/octet-stream",
      size: buffer.length,
      buffer,
    };
  } catch (err) {
    console.warn(`[IMSG] Could not read attachment ${absPath}: ${err.message}`);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Polling — read new rows from chat.db
// ---------------------------------------------------------------------------

/**
 * Query chat.db for messages with ROWID > lastRowId and dispatch them through
 * ConnectorBase.handleIncoming.
 */
async function pollNewMessages() {
  let rows;
  try {
    rows = db.prepare(`
      SELECT
        m.ROWID          AS row_id,
        m.text           AS text,
        m.is_from_me     AS is_from_me,
        m.date           AS msg_date,
        m.handle_id      AS handle_id,
        m.cache_roomnames AS room_name,
        h.id             AS sender_id,
        c.chat_identifier AS chat_identifier,
        c.style          AS chat_style,
        c.display_name   AS chat_display_name
      FROM message m
      LEFT JOIN handle h ON m.handle_id = h.ROWID
      LEFT JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
      LEFT JOIN chat c ON cmj.chat_id = c.ROWID
      WHERE m.ROWID > ?
      ORDER BY m.ROWID ASC
    `).all(lastRowId);
  } catch (err) {
    console.error(`[IMSG] Poll query failed: ${err.message}`);
    return;
  }

  for (const row of rows) {
    lastRowId = row.row_id;

    // Skip messages sent by this machine (our own outgoing messages)
    if (row.is_from_me) continue;

    const senderId = row.sender_id || "unknown";
    const chatIdentifier = row.chat_identifier || senderId;
    const isGroup = isGroupIdentifier(chatIdentifier, row.chat_style);
    groupCache.set(chatIdentifier, isGroup);

    const chatDisplayName = row.chat_display_name || chatIdentifier;

    const normalized = {
      chatId: chatIdentifier,
      senderId,
      senderName: senderId,
      text: row.text || "",
    };

    // Load first attachment if present
    const attachment = loadAttachment(row.row_id);
    if (attachment) {
      normalized.media = attachment;
    }

    // Extra metadata for the brain
    normalized.extra = {
      chat_display_name: chatDisplayName,
      msg_date: row.msg_date,
    };

    await connector.handleIncoming(normalized);
  }
}

// ---------------------------------------------------------------------------
// AppleScript sending helpers
// ---------------------------------------------------------------------------

/**
 * Send a plain text iMessage to a recipient via AppleScript.
 *
 * @param {string} recipient - Phone number or iMessage email address.
 * @param {string} text - Message body.
 */
async function sendTextViaAppleScript(recipient, text) {
  const escapedText = text.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  const script = `
    tell application "Messages"
      set targetService to 1st account whose service type = iMessage
      set targetBuddy to participant "${recipient}" of targetService
      send "${escapedText}" to targetBuddy
    end tell
  `;
  await execFileAsync("osascript", ["-e", script]);
}

/**
 * Send a text message to an iMessage group chat via AppleScript.
 * Group chats are addressed by their chat name / identifier.
 *
 * @param {string} chatIdentifier - The chat identifier (e.g. "chat123456").
 * @param {string} text - Message body.
 */
async function sendTextToGroupViaAppleScript(chatIdentifier, text) {
  const escapedText = text.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  const script = `
    tell application "Messages"
      set targetChat to chat id "${chatIdentifier}"
      send "${escapedText}" to targetChat
    end tell
  `;
  await execFileAsync("osascript", ["-e", script]);
}

/**
 * Send a text message, automatically choosing DM or group path.
 *
 * @param {string} chatId - Chat identifier or phone/email.
 * @param {string} text - Message body.
 */
async function sendText(chatId, text) {
  if (groupCache.get(chatId)) {
    await sendTextToGroupViaAppleScript(chatId, text);
  } else {
    await sendTextViaAppleScript(chatId, text);
  }
}

/**
 * Send an image file to a recipient via AppleScript.
 * Writes the buffer to a temp file, then sends as a file attachment.
 *
 * @param {string} chatId - Chat identifier or phone/email.
 * @param {string} caption - Text caption to send alongside the image.
 * @param {Buffer} imageBuffer - Raw image bytes.
 * @param {string} mime - MIME type (used for file extension).
 */
async function sendImage(chatId, caption, imageBuffer, mime) {
  const ext = mime === "image/png" ? ".png" : ".jpg";
  const tmpPath = path.join(os.tmpdir(), `sentient_img_${Date.now()}${ext}`);
  fs.writeFileSync(tmpPath, imageBuffer);

  try {
    const posixPath = tmpPath.replace(/ /g, "\\\\ ");
    if (groupCache.get(chatId)) {
      const script = `
        tell application "Messages"
          set targetChat to chat id "${chatId}"
          send POSIX file "${posixPath}" to targetChat
        end tell
      `;
      await execFileAsync("osascript", ["-e", script]);
    } else {
      const script = `
        tell application "Messages"
          set targetService to 1st account whose service type = iMessage
          set targetBuddy to participant "${chatId}" of targetService
          send POSIX file "${posixPath}" to targetBuddy
        end tell
      `;
      await execFileAsync("osascript", ["-e", script]);
    }
    if (caption) {
      await sendText(chatId, caption);
    }
  } finally {
    try { fs.unlinkSync(tmpPath); } catch (_) { /* best effort cleanup */ }
  }
}

// ---------------------------------------------------------------------------
// Send hooks
// ---------------------------------------------------------------------------

connector.setSendHooks({
  sendText,
  sendImage,
});

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

/**
 * Entry point — start the connector, open the database, and begin polling.
 */
async function main() {
  await connector.start({ poll_interval_ms: 2000 });

  // Verify chat.db is accessible
  if (!fs.existsSync(CHAT_DB_PATH)) {
    console.error(`[IMSG] Messages database not found at ${CHAT_DB_PATH}`);
    console.error("[IMSG] Ensure this is running on macOS with Messages.app configured.");
    process.exit(1);
  }

  try {
    db = openDatabase();
  } catch (err) {
    console.error(`[IMSG] Cannot open chat.db: ${err.message}`);
    console.error("[IMSG] Grant Full Disk Access to your terminal in System Settings > Privacy & Security.");
    process.exit(1);
  }

  seedLastRowId();

  const interval = connector.config.poll_interval_ms || 2000;
  console.log(`[IMSG] Polling chat.db every ${interval}ms`);
  pollTimer = setInterval(pollNewMessages, interval);

  console.log("[IMSG] Connector running. Send an iMessage to interact with the brain.");

  // Graceful shutdown
  const shutdown = () => {
    console.log("[IMSG] Shutting down...");
    if (pollTimer) clearInterval(pollTimer);
    if (db) db.close();
    process.exit(0);
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main().catch((err) => {
  console.error("[IMSG] Fatal:", err);
  process.exit(1);
});
