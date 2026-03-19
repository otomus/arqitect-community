/**
 * Slack Connector — bridges Slack workspace messages to the Arqitect brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Slack-specific Bolt integration in Socket Mode.
 *
 * Auth: Bot Token (xoxb-...) + App-Level Token (xapp-...) for Socket Mode.
 */

const { App } = require("@slack/bolt");
const { WebClient } = require("@slack/web-api");
const ConnectorBase = require("../lib/connector-base");
const path = require("path");
const fs = require("fs");
const https = require("https");

const connector = new ConnectorBase("slack", __dirname);

// --- Config loading (pre-boot, needed for Bolt init) ---

const configFile = path.join(__dirname, "config.json");
let bootConfig = {};
if (fs.existsSync(configFile)) {
  try {
    bootConfig = JSON.parse(fs.readFileSync(configFile, "utf8"));
  } catch (_) {}
}

const botToken = bootConfig.bot_token || "";
const appToken = bootConfig.app_token || "";
const signingSecret = bootConfig.signing_secret || "";

if (!botToken) {
  console.error("[SLACK] FATAL: No bot_token in config.json. Provide an xoxb-... token.");
  process.exit(1);
}
if (!appToken) {
  console.error("[SLACK] FATAL: No app_token in config.json. Provide an xapp-... token for Socket Mode.");
  process.exit(1);
}
if (!signingSecret) {
  console.error("[SLACK] FATAL: No signing_secret in config.json.");
  process.exit(1);
}

// --- Bolt app ---

const app = new App({
  token: botToken,
  appToken,
  signingSecret,
  socketMode: true,
});

const webClient = new WebClient(botToken);

// Store the bot's own user ID so we can detect @mentions and ignore own messages.
connector.platformData.botUserId = null;

// --- Group detection ---
// Slack channel_type: "channel" / "group" = group; "im" = DM; "mpim" = multi-party DM
connector.setGroupDetector((chatId) => {
  // We store channel type per chat; fall back to assuming group if unknown
  const channelType = connector.platformData.channelTypes?.[String(chatId)];
  if (!channelType) return true;
  return channelType !== "im";
});

// Track channel types as we see them
connector.platformData.channelTypes = {};

// --- Bot addressing ---

/**
 * Check if text addresses the bot via @mention or name prefix.
 * @param {string} text - Raw message text
 * @returns {boolean}
 */
connector.addressesBot = function (text) {
  const lower = text.toLowerCase().trim();
  const botId = connector.platformData.botUserId;

  // Check for <@BOT_ID> mention pattern
  if (botId && text.includes(`<@${botId}>`)) return true;

  // Check for bot name prefix
  for (const name of connector.botNames) {
    if (lower.startsWith(name)) {
      const after = lower[name.length];
      if (!after || ",: .!?\n".includes(after)) return true;
    }
  }
  return false;
};

/**
 * Strip bot @mention or name prefix from text.
 * @param {string} text - Raw message text
 * @returns {string} Cleaned text
 */
connector.stripBotPrefix = function (text) {
  let result = text;
  const botId = connector.platformData.botUserId;

  // Strip <@BOT_ID> mention
  if (botId) {
    result = result.replace(new RegExp(`<@${botId}>\\s*`, "g"), "").trim();
  }

  // Strip bot name prefix
  const lower = result.toLowerCase().trim();
  for (const name of connector.botNames) {
    if (lower.startsWith(name)) {
      const after = lower[name.length];
      if (!after || ",: .!?\n".includes(after)) {
        let stripped = result.trim().substring(name.length);
        stripped = stripped.replace(/^[,:\s.!?]+/, "").trim();
        return stripped || text;
      }
    }
  }
  return result;
};

// --- Media helpers ---

/**
 * Download a file from Slack using its url_private (requires auth header).
 * @param {string} urlPrivate - The file's url_private from Slack
 * @returns {Promise<Buffer|null>} File contents or null on failure
 */
function downloadSlackFile(urlPrivate) {
  return new Promise((resolve) => {
    const options = {
      headers: { Authorization: `Bearer ${botToken}` },
    };
    https.get(urlPrivate, options, (res) => {
      // Follow redirects
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        https.get(res.headers.location, options, (redirectRes) => {
          const chunks = [];
          redirectRes.on("data", (c) => chunks.push(c));
          redirectRes.on("end", () => resolve(Buffer.concat(chunks)));
          redirectRes.on("error", () => resolve(null));
        }).on("error", () => resolve(null));
        return;
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks)));
      res.on("error", () => resolve(null));
    }).on("error", (err) => {
      console.warn(`[SLACK] Download failed: ${err.message}`);
      resolve(null);
    });
  });
}

/**
 * Download a Slack file and save it to the media directory.
 * @param {string} urlPrivate - The file's url_private
 * @param {string} mediaType - "image", "video", "audio", or "document"
 * @returns {Promise<{buffer: Buffer, path: string, size: number}|null>}
 */
async function downloadAndSaveMedia(urlPrivate, mediaType) {
  const buffer = await downloadSlackFile(urlPrivate);
  if (!buffer) return null;
  const mediaPath = await connector.saveMediaBuffer(buffer, mediaType);
  return { buffer, path: mediaPath, size: buffer.length };
}

/**
 * Map a Slack file mimetype to a normalized media type.
 * @param {string} mimetype - MIME type string
 * @returns {string} One of: "image", "video", "audio", "document"
 */
function classifyMime(mimetype) {
  if (!mimetype) return "document";
  if (mimetype.startsWith("image/")) return "image";
  if (mimetype.startsWith("video/")) return "video";
  if (mimetype.startsWith("audio/")) return "audio";
  return "document";
}

// --- Send hooks ---

connector.setSendHooks({
  /**
   * Send a text message to a Slack channel.
   * Attempts mrkdwn formatting first.
   * @param {string} chatId - Channel or DM ID
   * @param {string} text - Message text
   */
  async sendText(chatId, text) {
    await webClient.chat.postMessage({
      channel: chatId,
      text,
      mrkdwn: true,
    });
  },

  /**
   * Upload and send an image to a Slack channel.
   * @param {string} chatId - Channel or DM ID
   * @param {string} caption - Image caption
   * @param {Buffer} imageBuffer - Image binary data
   * @param {string} mime - MIME type (e.g. "image/png")
   */
  async sendImage(chatId, caption, imageBuffer, mime) {
    const ext = mime === "image/png" ? ".png" : mime === "image/gif" ? ".gif" : ".jpg";
    const filename = `image_${Date.now()}${ext}`;
    await webClient.filesUploadV2({
      channel_id: chatId,
      file: imageBuffer,
      filename,
      initial_comment: caption || undefined,
    });
  },

  /**
   * Send an audio file to a Slack channel.
   * @param {string} chatId - Channel or DM ID
   * @param {string} text - Accompanying text message
   * @param {Buffer} audioBuffer - Audio binary data
   * @param {string} mime - MIME type (e.g. "audio/mp4")
   */
  async sendAudio(chatId, text, audioBuffer, mime) {
    if (text) {
      await webClient.chat.postMessage({ channel: chatId, text, mrkdwn: true });
    }
    const ext = mime === "audio/ogg" ? ".ogg" : mime === "audio/mpeg" ? ".mp3" : ".m4a";
    const filename = `audio_${Date.now()}${ext}`;
    await webClient.filesUploadV2({
      channel_id: chatId,
      file: audioBuffer,
      filename,
    });
  },

  /**
   * Upload and send a document to a Slack channel.
   * @param {string} chatId - Channel or DM ID
   * @param {object} doc - Document descriptor
   * @param {Buffer} doc.buffer - File binary data
   * @param {string} doc.fileName - Original file name
   * @param {string} doc.mime - MIME type
   * @param {string} doc.caption - Optional caption
   */
  async sendDocument(chatId, { buffer, fileName, mime, caption }) {
    await webClient.filesUploadV2({
      channel_id: chatId,
      file: buffer,
      filename: fileName,
      initial_comment: caption || undefined,
    });
  },

  /**
   * Add an emoji reaction to a message.
   * @param {string} chatId - Channel ID
   * @param {string} emoji - Emoji name (without colons, e.g. "thumbsup")
   * @param {object} msgKey - Message key containing { ts } for the target message
   */
  async sendReaction(chatId, emoji, msgKey) {
    // Normalize emoji: strip colons if present, convert common Unicode names
    const emojiName = emoji.replace(/:/g, "").trim();
    await webClient.reactions.add({
      channel: chatId,
      name: emojiName,
      timestamp: msgKey.ts,
    });
  },

  /**
   * Show a typing indicator. Slack does not have a native typing API for bots,
   * so this is a no-op placeholder for interface compatibility.
   * @param {string} _chatId - Channel ID (unused)
   */
  async sendTyping(_chatId) {
    // Slack Bot API does not support typing indicators natively.
    // This hook exists for ConnectorBase compatibility.
  },
});

// --- Message handler ---

app.event("message", async ({ event, context }) => {
  // Ignore bot messages and message_changed subtypes to avoid loops
  if (event.subtype && event.subtype !== "file_share") return;
  if (event.bot_id) return;

  // Resolve bot user ID on first message if not set
  if (!connector.platformData.botUserId && context.botUserId) {
    connector.platformData.botUserId = context.botUserId;
  }

  // Ignore messages from the bot itself
  if (event.user === connector.platformData.botUserId) return;

  const chatId = event.channel;
  const userId = event.user;
  const text = event.text || "";

  // Track channel type for group detection
  if (event.channel_type) {
    connector.platformData.channelTypes[chatId] = event.channel_type;
  }

  // --- Resolve sender display name ---
  let senderName = userId;
  try {
    const userInfo = await webClient.users.info({ user: userId });
    senderName = userInfo.user?.real_name
      || userInfo.user?.profile?.display_name
      || userInfo.user?.name
      || userId;
  } catch (err) {
    console.warn(`[SLACK] Could not fetch user info for ${userId}: ${err.message}`);
  }

  // --- Build normalized message ---
  const normalized = {
    chatId: String(chatId),
    senderId: String(userId),
    senderName,
    text,
    msgKey: { ts: event.ts },
    extra: {
      thread_ts: event.thread_ts || event.ts,
      msg_id: event.ts,
    },
  };

  // --- Handle file attachments ---
  if (event.files && event.files.length > 0) {
    const file = event.files[0];
    const mediaType = classifyMime(file.mimetype);
    if (file.url_private) {
      const saved = await downloadAndSaveMedia(file.url_private, mediaType);
      if (saved) {
        normalized.media = {
          type: mediaType,
          path: saved.path,
          mime: file.mimetype || "",
          size: saved.size,
          buffer: saved.buffer,
        };
      }
    }
  }

  await connector.handleIncoming(normalized);
});

// --- Main ---

/**
 * Boot the connector: start ConnectorBase (Redis, config, response handler),
 * resolve the bot's own user ID, then start Bolt in Socket Mode.
 */
async function main() {
  await connector.start();

  // Resolve bot user ID before processing messages
  try {
    const authResult = await webClient.auth.test();
    connector.platformData.botUserId = authResult.user_id;
    console.log(`[SLACK] Bot user ID: ${authResult.user_id}`);
  } catch (err) {
    console.warn(`[SLACK] Could not resolve bot user ID: ${err.message}`);
  }

  await app.start();
  console.log("[SLACK] Bot launched in Socket Mode. Listening for messages...");

  process.once("SIGINT", async () => {
    await app.stop();
    process.exit(0);
  });
  process.once("SIGTERM", async () => {
    await app.stop();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("[SLACK] Fatal:", err);
  process.exit(1);
});
