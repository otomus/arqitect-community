/**
 * Matrix Connector — bridges Matrix room messages to the Arqitect brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Matrix-specific matrix-js-sdk integration.
 *
 * Auth: requires a homeserver URL, bot user ID, and access token.
 */

const sdk = require("matrix-js-sdk");
const https = require("https");
const http = require("http");
const path = require("path");
const fs = require("fs");
const ConnectorBase = require("../lib/connector-base");

const connector = new ConnectorBase("matrix", __dirname);

/** @type {import("matrix-js-sdk").MatrixClient | null} */
let matrixClient = null;

/**
 * Set of room IDs identified as direct messages.
 * Populated from the m.direct account data event.
 * @type {Set<string>}
 */
const directMessageRooms = new Set();

// --- Config loading ---

const configFile = path.join(__dirname, "config.json");
let homeserverUrl = "";
let accessToken = "";
let botUserId = "";

if (fs.existsSync(configFile)) {
  try {
    const loaded = JSON.parse(fs.readFileSync(configFile, "utf8"));
    homeserverUrl = loaded.homeserver_url || "";
    accessToken = loaded.access_token || "";
    botUserId = loaded.user_id || "";
  } catch (_) {}
}

if (!homeserverUrl || !accessToken || !botUserId) {
  console.error("[MATRIX] FATAL: homeserver_url, access_token, and user_id are required in config.json.");
  process.exit(1);
}

// --- Group detection ---

/**
 * Refreshes the set of DM room IDs from the m.direct account data.
 * Matrix marks DMs via the m.direct account data event, which maps
 * user IDs to arrays of room IDs used for direct messaging.
 */
function refreshDirectMessageRooms() {
  if (!matrixClient) return;

  const directEvent = matrixClient.getAccountData("m.direct");
  if (!directEvent) return;

  const directContent = directEvent.getContent();
  directMessageRooms.clear();
  for (const userId of Object.keys(directContent)) {
    const roomIds = directContent[userId];
    if (Array.isArray(roomIds)) {
      for (const roomId of roomIds) {
        directMessageRooms.add(roomId);
      }
    }
  }
}

connector.setGroupDetector((roomId) => !directMessageRooms.has(String(roomId)));

// --- Media helpers ---

/**
 * Convert an mxc:// URL to an HTTP(S) URL and download the content.
 * @param {string} mxcUrl - The mxc:// media URL
 * @returns {Promise<{buffer: Buffer, mime: string} | null>}
 */
async function downloadMxcMedia(mxcUrl) {
  if (!mxcUrl || !mxcUrl.startsWith("mxc://")) return null;

  try {
    const httpUrl = matrixClient.mxcUrlToHttp(mxcUrl);
    if (!httpUrl) return null;

    const buffer = await fetchUrl(httpUrl);
    return buffer ? { buffer, mime: "" } : null;
  } catch (err) {
    console.warn(`[MATRIX] Failed to download media: ${err.message}`);
    return null;
  }
}

/**
 * Fetch a URL and return the response body as a Buffer.
 * Follows a single redirect if needed.
 * @param {string} url - HTTP or HTTPS URL
 * @returns {Promise<Buffer | null>}
 */
function fetchUrl(url) {
  return new Promise((resolve) => {
    const get = url.startsWith("https") ? https.get : http.get;
    get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        fetchUrl(res.headers.location).then(resolve);
        return;
      }
      if (res.statusCode !== 200) {
        resolve(null);
        return;
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks)));
      res.on("error", () => resolve(null));
    }).on("error", () => resolve(null));
  });
}

/**
 * Download media from a Matrix event and save it to the media directory.
 * @param {object} content - The event content containing url/info fields
 * @param {string} mediaType - One of "image", "video", "audio", "document"
 * @returns {Promise<{buffer: Buffer, path: string, size: number, mime: string} | null>}
 */
async function downloadAndSaveMedia(content, mediaType) {
  const mxcUrl = content.url;
  if (!mxcUrl) return null;

  const downloaded = await downloadMxcMedia(mxcUrl);
  if (!downloaded) return null;

  const mime = content.info?.mimetype || "";
  const mediaPath = await connector.saveMediaBuffer(downloaded.buffer, mediaType);
  return {
    buffer: downloaded.buffer,
    path: mediaPath,
    size: downloaded.buffer.length,
    mime,
  };
}

/**
 * Determine the media type from a Matrix message type (msgtype).
 * @param {string} msgtype - Matrix message type (m.image, m.video, etc.)
 * @returns {string | null} Normalized media type or null
 */
function mediaTypeFromMsgtype(msgtype) {
  const mapping = {
    "m.image": "image",
    "m.video": "video",
    "m.audio": "audio",
    "m.file": "document",
  };
  return mapping[msgtype] || null;
}

// --- Send hooks ---

connector.setSendHooks({
  /**
   * Send a plain text message to a Matrix room.
   * @param {string} roomId - Target room ID
   * @param {string} text - Message text
   */
  async sendText(roomId, text) {
    await matrixClient.sendEvent(roomId, "m.room.message", {
      msgtype: "m.text",
      body: text,
    });
  },

  /**
   * Upload and send an image to a Matrix room.
   * @param {string} roomId - Target room ID
   * @param {string} caption - Image caption
   * @param {Buffer} imageBuffer - Image file content
   * @param {string} mime - MIME type of the image
   */
  async sendImage(roomId, caption, imageBuffer, mime) {
    const uploadResponse = await matrixClient.uploadContent(imageBuffer, {
      type: mime,
      name: `image_${Date.now()}.${mime === "image/png" ? "png" : "jpg"}`,
    });
    const mxcUrl = uploadResponse.content_uri;

    await matrixClient.sendEvent(roomId, "m.room.message", {
      msgtype: "m.image",
      body: caption || "image",
      url: mxcUrl,
      info: { mimetype: mime, size: imageBuffer.length },
    });
  },

  /**
   * Upload and send an audio file to a Matrix room.
   * Sends caption as a separate text message if provided.
   * @param {string} roomId - Target room ID
   * @param {string} text - Optional caption
   * @param {Buffer} audioBuffer - Audio file content
   * @param {string} mime - MIME type of the audio
   */
  async sendAudio(roomId, text, audioBuffer, mime) {
    if (text) {
      await matrixClient.sendEvent(roomId, "m.room.message", {
        msgtype: "m.text",
        body: text,
      });
    }

    const uploadResponse = await matrixClient.uploadContent(audioBuffer, {
      type: mime,
      name: `audio_${Date.now()}.${mime === "audio/ogg" ? "ogg" : "mp4"}`,
    });
    const mxcUrl = uploadResponse.content_uri;

    await matrixClient.sendEvent(roomId, "m.room.message", {
      msgtype: "m.audio",
      body: "audio",
      url: mxcUrl,
      info: { mimetype: mime, size: audioBuffer.length },
    });
  },

  /**
   * Upload and send a document/file to a Matrix room.
   * @param {string} roomId - Target room ID
   * @param {object} doc - Document details
   * @param {Buffer} doc.buffer - File content
   * @param {string} doc.fileName - File name
   * @param {string} doc.mime - MIME type
   * @param {string} doc.caption - Optional caption
   */
  async sendDocument(roomId, { buffer, fileName, mime, caption }) {
    const uploadResponse = await matrixClient.uploadContent(buffer, {
      type: mime,
      name: fileName,
    });
    const mxcUrl = uploadResponse.content_uri;

    await matrixClient.sendEvent(roomId, "m.room.message", {
      msgtype: "m.file",
      body: caption || fileName,
      url: mxcUrl,
      filename: fileName,
      info: { mimetype: mime, size: buffer.length },
    });
  },

  /**
   * Send a reaction (emoji annotation) to a specific event in a room.
   * @param {string} roomId - Target room ID
   * @param {string} emoji - Reaction emoji
   * @param {string} eventId - The event ID to react to
   */
  async sendReaction(roomId, emoji, eventId) {
    await matrixClient.sendEvent(roomId, "m.reaction", {
      "m.relates_to": {
        rel_type: "m.annotation",
        event_id: eventId,
        key: emoji,
      },
    });
  },
});

// --- Matrix client setup and event handling ---

/**
 * Handle a single Room.timeline event from the Matrix sync loop.
 * Normalizes the event into the ConnectorBase message format and
 * delegates to connector.handleIncoming.
 * @param {object} event - Matrix timeline event
 * @param {object} room - Matrix room object
 */
async function handleTimelineEvent(event, room) {
  // Only handle m.room.message events
  if (event.getType() !== "m.room.message") return;

  // Ignore our own messages
  const senderId = event.getSender();
  if (senderId === botUserId) return;

  // Ignore events from before the client started (historical sync)
  // The event timestamp should be within the last 30 seconds of startup
  if (event.getTs() < startTimestamp - 30000) return;

  const roomId = room.roomId;
  const content = event.getContent();
  const msgtype = content.msgtype;
  const text = content.body || "";

  const senderMember = room.getMember(senderId);
  const senderName = senderMember?.name || senderId;

  const normalized = {
    chatId: roomId,
    senderId,
    senderName,
    text,
    msgKey: event.getId(),
  };

  // Handle media messages
  const mediaType = mediaTypeFromMsgtype(msgtype);
  if (mediaType && content.url) {
    const saved = await downloadAndSaveMedia(content, mediaType);
    if (saved) {
      normalized.media = {
        type: mediaType,
        path: saved.path,
        mime: saved.mime,
        size: saved.size,
        buffer: saved.buffer,
      };
      // For media messages, the body is usually the filename — use caption if available
      if (msgtype !== "m.text") {
        normalized.text = "";
      }
    }
  }

  await connector.handleIncoming(normalized);
}

/** Timestamp recorded at startup to filter out historical messages */
let startTimestamp = 0;

/**
 * Create and start the Matrix client, begin syncing, and
 * attach the Room.timeline event listener.
 */
async function startMatrix() {
  startTimestamp = Date.now();

  matrixClient = sdk.createClient({
    baseUrl: homeserverUrl,
    accessToken,
    userId: botUserId,
  });

  // Once initial sync completes, refresh DM room list
  matrixClient.once("sync", (state) => {
    if (state === "PREPARED") {
      refreshDirectMessageRooms();
      console.log(`[MATRIX] Initial sync complete. Tracking ${directMessageRooms.size} DM room(s).`);
    }
  });

  // Keep DM room set up to date when account data changes
  matrixClient.on("accountData", (event) => {
    if (event.getType() === "m.direct") {
      refreshDirectMessageRooms();
    }
  });

  // Handle incoming messages
  matrixClient.on("Room.timeline", async (event, room, toStartOfTimeline) => {
    // Ignore paginated/historical events
    if (toStartOfTimeline) return;

    try {
      await handleTimelineEvent(event, room);
    } catch (err) {
      console.error(`[MATRIX] Error handling timeline event: ${err.message}`);
    }
  });

  await matrixClient.startClient({ initialSyncLimit: 0 });
  console.log("[MATRIX] Client started, syncing...");
}

// --- Main ---

async function main() {
  await connector.start();
  await startMatrix();
  console.log("[MATRIX] Connector running. Listening for Matrix messages...");

  process.once("SIGINT", () => {
    matrixClient?.stopClient();
    process.exit(0);
  });
  process.once("SIGTERM", () => {
    matrixClient?.stopClient();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("[MATRIX] Fatal:", err);
  process.exit(1);
});
