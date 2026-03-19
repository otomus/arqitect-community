/**
 * Discord Connector — bridges Discord server and DM messages to the Arqitect brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Discord-specific discord.js integration.
 *
 * Auth: BOT_TOKEN from the Discord Developer Portal (Bot section)
 */

const { Client, GatewayIntentBits, Partials, AttachmentBuilder } = require("discord.js");
const ConnectorBase = require("../lib/connector-base");
const path = require("path");
const fs = require("fs");
const https = require("https");

const connector = new ConnectorBase("discord", __dirname);

// --- Discord-specific: group detection ---
// Guild (server) channels are group chats; DMs are private
connector.setGroupDetector((chatId) => {
  const channel = client.channels.cache.get(chatId);
  return channel ? !channel.isDMBased() : false;
});

/**
 * Override addressesBot for Discord (@mention and bot name prefix support).
 * @param {string} text - Raw message text
 * @returns {boolean} Whether the message is addressed to the bot
 */
connector.addressesBot = function (text) {
  const lower = text.toLowerCase().trim();
  // Check for Discord @mention (rendered as <@BOT_ID>)
  if (connector.platformData.botId && text.includes(`<@${connector.platformData.botId}>`)) {
    return true;
  }
  for (const name of connector.botNames) {
    if (lower.startsWith(name)) {
      const after = lower[name.length];
      if (!after || ",: .!?\n".includes(after)) return true;
    }
  }
  return false;
};

/**
 * Override stripBotPrefix for Discord — removes @mention and bot name prefix.
 * @param {string} text - Raw message text
 * @returns {string} Text with bot prefix removed
 */
connector.stripBotPrefix = function (text) {
  let result = text;
  // Strip Discord @mention
  if (connector.platformData.botId) {
    result = result.replace(new RegExp(`<@!?${connector.platformData.botId}>\\s*`, "g"), "").trim();
  }
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
 * Download a file from a URL into a Buffer.
 * @param {string} url - The URL to download
 * @returns {Promise<Buffer|null>} The file content or null on failure
 */
async function downloadFromUrl(url) {
  try {
    const buffer = await new Promise((resolve, reject) => {
      const handler = (res) => {
        // Follow redirects
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          https.get(res.headers.location, handler).on("error", reject);
          return;
        }
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () => resolve(Buffer.concat(chunks)));
        res.on("error", reject);
      };
      https.get(url, handler).on("error", reject);
    });
    return buffer;
  } catch (err) {
    console.warn(`[DISCORD] Download failed: ${err.message}`);
    return null;
  }
}

/**
 * Download a Discord attachment and save it to the media directory.
 * @param {string} url - Attachment URL
 * @param {string} mediaType - Type of media (image, video, audio, etc.)
 * @returns {Promise<{buffer: Buffer, path: string, size: number}|null>}
 */
async function downloadAndSaveMedia(url, mediaType) {
  const buffer = await downloadFromUrl(url);
  if (!buffer) return null;
  const mediaPath = await connector.saveMediaBuffer(buffer, mediaType);
  return { buffer, path: mediaPath, size: buffer.length };
}

/**
 * Determine the media type from a Discord attachment's content type.
 * @param {import("discord.js").Attachment} attachment - Discord attachment object
 * @returns {string|null} Normalized media type or null if unsupported
 */
function classifyAttachment(attachment) {
  const ct = (attachment.contentType || "").toLowerCase();
  if (ct.startsWith("image/")) return "image";
  if (ct.startsWith("video/")) return "video";
  if (ct.startsWith("audio/")) return "audio";
  // Fallback: check file extension
  const name = (attachment.name || "").toLowerCase();
  if (/\.(png|jpe?g|gif|webp)$/.test(name)) return "image";
  if (/\.(mp4|mov|webm|avi)$/.test(name)) return "video";
  if (/\.(mp3|ogg|wav|m4a|flac)$/.test(name)) return "audio";
  return "document";
}

// --- Bot setup ---

const configFile = path.join(__dirname, "config.json");
let botToken = "";
if (fs.existsSync(configFile)) {
  try {
    const loaded = JSON.parse(fs.readFileSync(configFile, "utf8"));
    botToken = loaded.bot_token || "";
  } catch (_) {}
}
if (!botToken) {
  console.error("[DISCORD] FATAL: No bot_token in config.json. Get one from the Discord Developer Portal.");
  process.exit(1);
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.DirectMessages,
    GatewayIntentBits.MessageContent,
  ],
  partials: [Partials.Channel], // Required to receive DMs without prior caching
});

connector.platformData.botId = null;

// --- Send hooks ---

/**
 * Split a long message into chunks that fit within Discord's 2000-char limit.
 * @param {string} text - The full message text
 * @returns {string[]} Array of text chunks
 */
function splitMessage(text) {
  const MAX_LENGTH = 2000;
  if (text.length <= MAX_LENGTH) return [text];
  const chunks = [];
  let remaining = text;
  while (remaining.length > 0) {
    if (remaining.length <= MAX_LENGTH) {
      chunks.push(remaining);
      break;
    }
    // Try to split at a newline near the limit
    let splitAt = remaining.lastIndexOf("\n", MAX_LENGTH);
    if (splitAt < MAX_LENGTH * 0.5) splitAt = MAX_LENGTH;
    chunks.push(remaining.substring(0, splitAt));
    remaining = remaining.substring(splitAt).trimStart();
  }
  return chunks;
}

connector.setSendHooks({
  /**
   * Send a text message to a Discord channel.
   * @param {string} chatId - Discord channel ID
   * @param {string} text - Message text
   */
  async sendText(chatId, text) {
    const channel = await client.channels.fetch(chatId);
    if (!channel) return;
    const chunks = splitMessage(text);
    for (const chunk of chunks) {
      await channel.send(chunk);
    }
  },

  /**
   * Send an image to a Discord channel.
   * @param {string} chatId - Discord channel ID
   * @param {string} caption - Image caption
   * @param {Buffer} imageBuffer - Image data
   * @param {string} mime - MIME type
   */
  async sendImage(chatId, caption, imageBuffer, mime) {
    const channel = await client.channels.fetch(chatId);
    if (!channel) return;
    const ext = mime === "image/png" ? "png" : "jpg";
    const attachment = new AttachmentBuilder(imageBuffer, { name: `image.${ext}` });
    await channel.send({ content: caption || undefined, files: [attachment] });
  },

  /**
   * Send a GIF to a Discord channel.
   * @param {string} chatId - Discord channel ID
   * @param {string} caption - GIF caption
   * @param {string} gifUrl - URL of the GIF
   */
  async sendGif(chatId, caption, gifUrl) {
    const channel = await client.channels.fetch(chatId);
    if (!channel) return;
    // Discord auto-embeds GIF URLs; send as text
    const content = caption ? `${caption}\n${gifUrl}` : gifUrl;
    await channel.send(content);
  },

  /**
   * Send an audio message to a Discord channel.
   * @param {string} chatId - Discord channel ID
   * @param {string} text - Accompanying text
   * @param {Buffer} audioBuffer - Audio data
   * @param {string} mime - MIME type
   */
  async sendAudio(chatId, text, audioBuffer, mime) {
    const channel = await client.channels.fetch(chatId);
    if (!channel) return;
    const ext = mime === "audio/ogg" ? "ogg" : "mp4";
    const attachment = new AttachmentBuilder(audioBuffer, { name: `audio.${ext}` });
    await channel.send({ content: text || undefined, files: [attachment] });
  },

  /**
   * Send a sticker to a Discord channel (sent as an image attachment).
   * @param {string} chatId - Discord channel ID
   * @param {Buffer} stickerBuffer - Sticker image data
   * @param {string} text - Accompanying text
   */
  async sendSticker(chatId, stickerBuffer, text) {
    const channel = await client.channels.fetch(chatId);
    if (!channel) return;
    const attachment = new AttachmentBuilder(stickerBuffer, { name: "sticker.webp" });
    await channel.send({ content: text || undefined, files: [attachment] });
  },

  /**
   * Send a document to a Discord channel.
   * @param {string} chatId - Discord channel ID
   * @param {object} doc - Document descriptor
   * @param {Buffer} doc.buffer - File data
   * @param {string} doc.fileName - File name
   * @param {string} doc.mime - MIME type
   * @param {string} doc.caption - Caption text
   */
  async sendDocument(chatId, { buffer, fileName, mime, caption }) {
    const channel = await client.channels.fetch(chatId);
    if (!channel) return;
    const attachment = new AttachmentBuilder(buffer, { name: fileName || "document" });
    await channel.send({ content: caption || undefined, files: [attachment] });
  },

  /**
   * React to a message with an emoji.
   * @param {string} chatId - Discord channel ID
   * @param {string} emoji - Emoji to react with
   * @param {object} msgRef - Message reference containing messageId
   */
  async sendReaction(chatId, emoji, msgRef) {
    const channel = await client.channels.fetch(chatId);
    if (!channel) return;
    const messageId = msgRef?.messageId;
    if (!messageId) return;
    try {
      const message = await channel.messages.fetch(messageId);
      await message.react(emoji);
    } catch (err) {
      console.warn(`[DISCORD] Reaction failed: ${err.message}`);
    }
  },

  /**
   * Show a typing indicator in a Discord channel.
   * @param {string} chatId - Discord channel ID
   */
  async sendTyping(chatId) {
    const channel = await client.channels.fetch(chatId);
    if (!channel) return;
    await channel.sendTyping();
  },
});

// --- Message handler ---

client.on("messageCreate", async (message) => {
  // Ignore messages from the bot itself
  if (message.author.id === client.user.id) return;
  // Ignore messages from other bots
  if (message.author.bot) return;

  const chatId = message.channel.id;
  const userId = message.author.id;
  const text = message.content || "";

  // Extract media from attachments (use the first attachment)
  let mediaType = null;
  let mediaUrl = null;

  if (message.attachments.size > 0) {
    const attachment = message.attachments.first();
    mediaType = classifyAttachment(attachment);
    mediaUrl = attachment.url;
  }

  // Handle stickers — Discord stickers come as a separate collection
  if (message.stickers.size > 0 && !mediaType) {
    const sticker = message.stickers.first();
    mediaType = "sticker";
    mediaUrl = sticker.url;
  }

  const senderName = message.member?.displayName || message.author.displayName || message.author.username;
  const normalized = {
    chatId: String(chatId),
    senderId: String(userId),
    senderName,
    text,
    msgKey: { messageId: message.id },
    extra: {
      msg_id: message.id,
      guild_id: message.guild?.id || "",
    },
  };

  if (mediaType && mediaUrl) {
    const saved = await downloadAndSaveMedia(mediaUrl, mediaType);
    if (saved) {
      const mimeFromType = {
        image: "image/jpeg",
        video: "video/mp4",
        audio: "audio/ogg",
        sticker: "image/webp",
        document: "application/octet-stream",
      };
      normalized.media = {
        type: mediaType,
        path: saved.path,
        mime: mimeFromType[mediaType] || "",
        size: saved.size,
        buffer: saved.buffer,
      };
    }
  }

  await connector.handleIncoming(normalized);
});

// --- Main ---

/**
 * Boot the connector: start ConnectorBase (Redis, config), then log in to Discord.
 */
async function main() {
  await connector.start();

  client.once("ready", () => {
    connector.platformData.botId = client.user.id;
    console.log(`[DISCORD] Bot logged in as ${client.user.tag}. Listening for messages...`);
  });

  await client.login(botToken);

  process.once("SIGINT", () => {
    client.destroy();
    process.exit(0);
  });
  process.once("SIGTERM", () => {
    client.destroy();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("[DISCORD] Fatal:", err);
  process.exit(1);
});
