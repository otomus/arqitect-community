/**
 * Nextcloud Talk Connector — bridges Nextcloud Talk chat messages to the Sentient brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Nextcloud Talk-specific OCS API integration via HTTP polling.
 *
 * Auth: Nextcloud username + password (or app token) with Basic auth.
 * Messages are fetched by polling the Talk chat API per room.
 */

const axios = require("axios");
const ConnectorBase = require("../lib/connector-base");
const path = require("path");
const fs = require("fs");

const connector = new ConnectorBase("nextcloud-talk", __dirname);

// --- Config bootstrap ---

const configFile = path.join(__dirname, "config.json");
let nextcloudUrl = "";
let username = "";
let password = "";
let pollIntervalMs = 3000;

if (fs.existsSync(configFile)) {
  try {
    const loaded = JSON.parse(fs.readFileSync(configFile, "utf8"));
    nextcloudUrl = (loaded.nextcloud_url || "").replace(/\/+$/, "");
    username = loaded.username || "";
    password = loaded.password || "";
    pollIntervalMs = loaded.poll_interval_ms || 3000;
  } catch (_) {}
}

if (!nextcloudUrl || !username || !password) {
  console.error("[NC-TALK] FATAL: Missing nextcloud_url, username, or password in config.json.");
  process.exit(1);
}

// --- HTTP client setup ---

const OCS_BASE = `${nextcloudUrl}/ocs/v2.php/apps/spreed/api`;
const OCS_HEADERS = {
  "OCS-APIRequest": "true",
  Accept: "application/json",
};

const httpClient = axios.create({
  baseURL: nextcloudUrl,
  auth: { username, password },
  headers: OCS_HEADERS,
  timeout: 30_000,
});

// --- Nextcloud Talk API helpers ---

/**
 * Fetch the list of rooms (conversations) the bot user participates in.
 *
 * @returns {Promise<Array<{token: string, name: string, type: number}>>} List of room objects
 */
async function fetchRooms() {
  const response = await httpClient.get(`${OCS_BASE}/v4/room`);
  return response.data?.ocs?.data || [];
}

/**
 * Fetch new chat messages for a specific room since the given message ID.
 * Uses lookIntoFuture=1 to get only messages newer than lastKnownMessageId.
 *
 * @param {string} roomToken - The Talk room token
 * @param {number} lastKnownMessageId - The ID of the last processed message (0 for initial)
 * @returns {Promise<{messages: Array, lastId: number}>} New messages and the latest message ID
 */
async function fetchNewMessages(roomToken, lastKnownMessageId) {
  const params = {
    lookIntoFuture: 1,
    limit: 100,
    includeLastKnown: 0,
    setReadMarker: 1,
  };
  if (lastKnownMessageId > 0) {
    params.lastKnownMessageId = lastKnownMessageId;
  }

  try {
    const response = await httpClient.get(
      `${OCS_BASE}/v1/chat/${roomToken}`,
      { params }
    );
    const messages = response.data?.ocs?.data || [];
    const lastId = messages.length > 0
      ? Math.max(...messages.map((m) => m.id))
      : lastKnownMessageId;
    return { messages, lastId };
  } catch (err) {
    // 304 Not Modified means no new messages — expected during polling
    if (err.response?.status === 304) {
      return { messages: [], lastId: lastKnownMessageId };
    }
    throw err;
  }
}

/**
 * Send a text message to a Nextcloud Talk room.
 *
 * @param {string} roomToken - The Talk room token
 * @param {string} text - Message text to send
 */
async function sendMessage(roomToken, text) {
  await httpClient.post(`${OCS_BASE}/v1/chat/${roomToken}`, { message: text });
}

/**
 * Share a file to a Nextcloud Talk room.
 * Uploads the file to the bot user's files, then shares it into the room.
 *
 * @param {string} roomToken - The Talk room token
 * @param {Buffer} buffer - File contents
 * @param {string} fileName - Name for the uploaded file
 * @param {string} caption - Optional caption text
 */
async function shareFileToRoom(roomToken, buffer, fileName, caption) {
  // Upload to Nextcloud user files via WebDAV
  const uploadPath = `/remote.php/dav/files/${username}/Talk/${fileName}`;
  await httpClient.put(uploadPath, buffer, {
    headers: { "Content-Type": "application/octet-stream" },
  });

  // Share to the Talk room using the OCS Share API
  await httpClient.post(
    `${nextcloudUrl}/ocs/v2.php/apps/files_sharing/api/v1/shares`,
    {
      path: `/Talk/${fileName}`,
      shareType: 10, // Share type 10 = Talk room
      shareWith: roomToken,
    },
    { headers: OCS_HEADERS }
  );

  // Send a caption as a follow-up message if provided
  if (caption) {
    await sendMessage(roomToken, caption);
  }
}

/**
 * Download a shared file from Nextcloud.
 * Resolves the file path from a message's file share parameters.
 *
 * @param {object} messageParams - The message parameters containing share/file info
 * @returns {Promise<{buffer: Buffer, fileName: string, mime: string}|null>} File data or null
 */
async function downloadSharedFile(messageParams) {
  try {
    const filePath = messageParams.path || messageParams.name || "";
    if (!filePath) return null;

    // Try downloading via WebDAV from the share owner's files
    const owner = messageParams.shareOwner || username;
    const davPath = `/remote.php/dav/files/${owner}/${filePath}`;
    const response = await httpClient.get(davPath, { responseType: "arraybuffer" });
    const buffer = Buffer.from(response.data);
    const fileName = path.basename(filePath);
    const mime = response.headers["content-type"] || "application/octet-stream";
    return { buffer, fileName, mime };
  } catch (err) {
    console.warn("[NC-TALK] File download failed:", err.message);
    return null;
  }
}

// --- Nextcloud Talk-specific: group detection ---
// Room types: 1 = one-to-one, 2 = group, 3 = public, 4 = changelog
/** @type {Map<string, number>} roomToken -> room type */
const roomTypes = new Map();

connector.setGroupDetector((chatId) => {
  const roomType = roomTypes.get(String(chatId));
  // Types 2 (group) and 3 (public) are group conversations
  return roomType === 2 || roomType === 3;
});

// Override addressesBot for Nextcloud Talk (@mention support)
connector.addressesBot = function (text) {
  const lower = text.toLowerCase().trim();
  // Nextcloud Talk uses @username for mentions
  if (lower.includes(`@${username.toLowerCase()}`)) return true;
  for (const name of connector.botNames) {
    if (lower.startsWith(name)) {
      const after = lower[name.length];
      if (!after || ",: .!?\n".includes(after)) return true;
    }
  }
  return false;
};

// Override stripBotPrefix for Nextcloud Talk
connector.stripBotPrefix = function (text) {
  // Remove @username mentions
  let result = text.replace(new RegExp(`@${username}\\s*`, "gi"), "").trim();
  const lower = result.toLowerCase();
  for (const name of connector.botNames) {
    if (lower.startsWith(name)) {
      const after = lower[name.length];
      if (!after || ",: .!?\n".includes(after)) {
        let stripped = result.substring(name.length);
        stripped = stripped.replace(/^[,:\s.!?]+/, "").trim();
        return stripped || text;
      }
    }
  }
  return result || text;
};

/**
 * Determine the media type from a MIME string.
 *
 * @param {string} mime - MIME type string
 * @returns {string} Normalized type for the brain
 */
function classifyMime(mime) {
  if (!mime) return "document";
  const lower = mime.toLowerCase();
  if (lower.startsWith("image/")) return "image";
  if (lower.startsWith("audio/")) return "audio";
  if (lower.startsWith("video/")) return "video";
  return "document";
}

// --- Send hooks ---

connector.setSendHooks({
  async sendText(chatId, text) {
    await sendMessage(chatId, text);
  },

  async sendImage(chatId, caption, imageBuffer, mime) {
    const ext = mime === "image/png" ? ".png" : ".jpg";
    const fileName = `sentient_image_${Date.now()}${ext}`;
    await shareFileToRoom(chatId, imageBuffer, fileName, caption);
  },

  async sendDocument(chatId, { buffer, fileName, mime, caption }) {
    await shareFileToRoom(chatId, buffer, fileName, caption);
  },

  async sendAudio(chatId, text, audioBuffer, mime) {
    if (text) {
      await sendMessage(chatId, text);
    }
    const ext = mime === "audio/ogg" ? ".ogg" : ".mp4";
    const fileName = `sentient_audio_${Date.now()}${ext}`;
    await shareFileToRoom(chatId, audioBuffer, fileName, "");
  },

  async sendTyping(chatId) {
    // Nextcloud Talk does not have a typing indicator API — no-op
  },
});

// --- Polling state ---

/** @type {Map<string, number>} roomToken -> lastKnownMessageId */
const lastMessageIds = new Map();

/** @type {NodeJS.Timeout|null} */
let pollTimer = null;

/**
 * Initialize room tracking by fetching the current room list
 * and recording the latest message IDs so we only process new messages.
 */
async function initializeRooms() {
  const rooms = await fetchRooms();
  console.log(`[NC-TALK] Found ${rooms.length} rooms`);

  for (const room of rooms) {
    roomTypes.set(room.token, room.type);

    // Fetch current last message to avoid replaying history on first start
    try {
      const response = await httpClient.get(
        `${OCS_BASE}/v1/chat/${room.token}`,
        { params: { lookIntoFuture: 0, limit: 1, includeLastKnown: 1 } }
      );
      const msgs = response.data?.ocs?.data || [];
      if (msgs.length > 0) {
        lastMessageIds.set(room.token, Math.max(...msgs.map((m) => m.id)));
      } else {
        lastMessageIds.set(room.token, 0);
      }
    } catch (err) {
      // 304 is fine — no messages in room
      if (err.response?.status !== 304) {
        console.warn(`[NC-TALK] Could not initialize room ${room.token}: ${err.message}`);
      }
      lastMessageIds.set(room.token, 0);
    }
  }
}

/**
 * Poll all tracked rooms for new messages and process them.
 * Skips messages from the bot user itself.
 */
async function pollAllRooms() {
  let rooms;
  try {
    rooms = await fetchRooms();
  } catch (err) {
    console.error("[NC-TALK] Failed to fetch rooms:", err.message);
    return;
  }

  // Update room types
  for (const room of rooms) {
    roomTypes.set(room.token, room.type);
    if (!lastMessageIds.has(room.token)) {
      // New room appeared — set marker to current last message
      lastMessageIds.set(room.token, room.lastMessage?.id || 0);
    }
  }

  for (const room of rooms) {
    const token = room.token;
    const lastId = lastMessageIds.get(token) || 0;

    try {
      const { messages, lastId: newLastId } = await fetchNewMessages(token, lastId);
      lastMessageIds.set(token, newLastId);

      for (const msg of messages) {
        // Skip messages from the bot itself
        if (msg.actorId === username) continue;
        // Skip system messages (joins, leaves, etc.)
        if (msg.systemMessage) continue;

        await processIncomingMessage(token, msg);
      }
    } catch (err) {
      console.warn(`[NC-TALK] Poll error for room ${token}: ${err.message}`);
    }
  }
}

/**
 * Process a single incoming Nextcloud Talk message and forward it to ConnectorBase.
 *
 * @param {string} roomToken - The Talk room token the message came from
 * @param {object} msg - The Nextcloud Talk message object from the OCS API
 */
async function processIncomingMessage(roomToken, msg) {
  const text = msg.message || "";
  const senderId = msg.actorId || "";
  const senderName = msg.actorDisplayName || "";

  const normalized = {
    chatId: roomToken,
    senderId,
    senderName,
    text,
    extra: {
      msg_id: msg.id,
      room_token: roomToken,
      timestamp: msg.timestamp,
    },
  };

  // Handle file shares (messageType "comment" with messageParameters containing "file")
  if (msg.messageParameters?.file) {
    const fileParams = msg.messageParameters.file;
    const downloaded = await downloadSharedFile(fileParams);
    if (downloaded) {
      const mediaType = classifyMime(downloaded.mime);
      const mediaPath = await connector.saveMediaBuffer(downloaded.buffer, mediaType);
      normalized.media = {
        type: mediaType,
        path: mediaPath,
        mime: downloaded.mime,
        size: downloaded.buffer.length,
        buffer: downloaded.buffer,
      };
    }
  }

  await connector.handleIncoming(normalized);
}

/**
 * Start the polling loop. Polls all rooms at the configured interval.
 */
function startPolling() {
  console.log(`[NC-TALK] Polling every ${pollIntervalMs}ms`);
  pollTimer = setInterval(async () => {
    try {
      await pollAllRooms();
    } catch (err) {
      console.error("[NC-TALK] Poll cycle error:", err.message);
    }
  }, pollIntervalMs);
}

// --- Main ---

async function main() {
  await connector.start({ poll_interval_ms: pollIntervalMs });

  console.log(`[NC-TALK] Connecting to ${nextcloudUrl} as ${username}`);

  // Verify credentials by fetching rooms
  await initializeRooms();

  startPolling();
  console.log("[NC-TALK] Bot launched. Polling for messages...");

  process.once("SIGINT", () => {
    if (pollTimer) clearInterval(pollTimer);
    process.exit(0);
  });
  process.once("SIGTERM", () => {
    if (pollTimer) clearInterval(pollTimer);
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("[NC-TALK] Fatal:", err);
  process.exit(1);
});
