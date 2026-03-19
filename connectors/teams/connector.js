/**
 * Microsoft Teams Connector — bridges Teams bot messages to the Arqitect brain via Redis.
 *
 * Uses ConnectorBase for Redis, config, access control, and response dispatch.
 * This file handles Teams-specific Bot Framework integration using BotFrameworkAdapter.
 *
 * Auth: Microsoft App ID + App Password from Azure Bot registration.
 * Teams sends activities to an HTTP endpoint; this connector uses restify to serve it.
 */

const {
  BotFrameworkAdapter,
  TurnContext,
  MessageFactory,
  CardFactory,
} = require("botbuilder");
const restify = require("restify");
const ConnectorBase = require("../lib/connector-base");
const path = require("path");
const fs = require("fs");
const https = require("https");
const http = require("http");

const connector = new ConnectorBase("teams", __dirname);

// --- Config bootstrap (need app_id and app_password before adapter creation) ---

const configFile = path.join(__dirname, "config.json");
let appId = "";
let appPassword = "";
let port = 3978;

if (fs.existsSync(configFile)) {
  try {
    const loaded = JSON.parse(fs.readFileSync(configFile, "utf8"));
    appId = loaded.app_id || "";
    appPassword = loaded.app_password || "";
    port = loaded.port || 3978;
  } catch (_) {}
}

if (!appId || !appPassword) {
  console.error("[TEAMS] FATAL: No app_id or app_password in config.json. Register a bot in Azure portal.");
  process.exit(1);
}

// --- Bot Framework Adapter ---

const adapter = new BotFrameworkAdapter({
  appId,
  appPassword,
});

adapter.onTurnError = async (context, error) => {
  console.error("[TEAMS] Unhandled adapter error:", error.message);
  try {
    await context.sendActivity("Sorry, something went wrong processing your message.");
  } catch (_) {}
};

// --- Conversation reference store for proactive messaging ---

/** @type {Map<string, Partial<import('botbuilder').ConversationReference>>} */
const conversationReferences = new Map();

/**
 * Store the conversation reference from an incoming activity.
 * Used later to send proactive messages back to the same conversation.
 *
 * @param {import('botbuilder').Activity} activity - The incoming activity
 */
function storeConversationReference(activity) {
  const ref = TurnContext.getConversationReference(activity);
  const chatId = activity.conversation?.id || "";
  if (chatId) {
    conversationReferences.set(chatId, ref);
  }
}

// --- Teams-specific: group detection ---
// In Teams, channels have conversation type "channel", group chats are "groupChat"
connector.setGroupDetector((chatId) => {
  const ref = conversationReferences.get(String(chatId));
  if (!ref) return false;
  const convType = ref.conversation?.conversationType;
  return convType === "channel" || convType === "groupChat";
});

// Override addressesBot for Teams (@mention and direct message support)
connector.addressesBot = function (text) {
  const lower = text.toLowerCase().trim();
  // Teams strips @mentions into plain text with the bot name
  for (const name of connector.botNames) {
    if (lower.includes(name)) return true;
  }
  return false;
};

// Override stripBotPrefix for Teams (remove <at>BotName</at> tags and name prefixes)
connector.stripBotPrefix = function (text) {
  // Remove HTML-style <at> tags that Teams uses for mentions
  let result = text.replace(/<at>[^<]*<\/at>\s*/gi, "").trim();
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

// --- Media helpers ---

/**
 * Download an attachment from a Teams message URL.
 * Teams attachments include a contentUrl for direct download.
 *
 * @param {string} contentUrl - The URL to download from
 * @returns {Promise<Buffer|null>} Downloaded file buffer, or null on failure
 */
async function downloadAttachment(contentUrl) {
  try {
    const transport = contentUrl.startsWith("https") ? https : http;
    const buffer = await new Promise((resolve, reject) => {
      transport.get(contentUrl, { headers: { Authorization: `Bearer ${appPassword}` } }, (res) => {
        if (res.statusCode === 301 || res.statusCode === 302) {
          // Follow redirect
          transport.get(res.headers.location, (redirectRes) => {
            const chunks = [];
            redirectRes.on("data", (c) => chunks.push(c));
            redirectRes.on("end", () => resolve(Buffer.concat(chunks)));
            redirectRes.on("error", reject);
          }).on("error", reject);
          return;
        }
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () => resolve(Buffer.concat(chunks)));
        res.on("error", reject);
      }).on("error", reject);
    });
    return buffer;
  } catch (err) {
    console.warn("[TEAMS] Attachment download failed:", err.message);
    return null;
  }
}

/**
 * Determine media type from a MIME content type string.
 *
 * @param {string} contentType - MIME type (e.g. "image/png")
 * @returns {string} Normalized media type for the brain
 */
function classifyContentType(contentType) {
  if (!contentType) return "document";
  const lower = contentType.toLowerCase();
  if (lower.startsWith("image/")) return "image";
  if (lower.startsWith("audio/")) return "audio";
  if (lower.startsWith("video/")) return "video";
  return "document";
}

// --- Send hooks ---

/**
 * Send a message to a Teams conversation using a stored conversation reference.
 * Falls back to proactive messaging when no active turn context is available.
 *
 * @param {string} chatId - The conversation ID to send to
 * @param {import('botbuilder').Partial<import('botbuilder').Activity>} activity - The activity to send
 */
async function sendProactiveActivity(chatId, activity) {
  const ref = conversationReferences.get(chatId);
  if (!ref) {
    console.warn(`[TEAMS] No conversation reference for ${chatId}, cannot send`);
    return;
  }
  await adapter.continueConversation(ref, async (turnContext) => {
    await turnContext.sendActivity(activity);
  });
}

connector.setSendHooks({
  async sendText(chatId, text) {
    await sendProactiveActivity(chatId, MessageFactory.text(text));
  },

  async sendImage(chatId, caption, imageBuffer, mime) {
    const base64 = imageBuffer.toString("base64");
    const contentType = mime || "image/png";
    const activity = MessageFactory.text(caption || "");
    activity.attachments = [{
      contentType,
      contentUrl: `data:${contentType};base64,${base64}`,
    }];
    await sendProactiveActivity(chatId, activity);
  },

  async sendDocument(chatId, { buffer, fileName, mime, caption }) {
    const base64 = buffer.toString("base64");
    const activity = MessageFactory.text(caption || "");
    activity.attachments = [{
      contentType: mime || "application/octet-stream",
      contentUrl: `data:${mime};base64,${base64}`,
      name: fileName,
    }];
    await sendProactiveActivity(chatId, activity);
  },

  async sendAudio(chatId, text, audioBuffer, mime) {
    if (text) {
      await sendProactiveActivity(chatId, MessageFactory.text(text));
    }
    const base64 = audioBuffer.toString("base64");
    const contentType = mime || "audio/mp4";
    const activity = MessageFactory.text("");
    activity.attachments = [{
      contentType,
      contentUrl: `data:${contentType};base64,${base64}`,
    }];
    await sendProactiveActivity(chatId, activity);
  },

  async sendCard(chatId, card, text) {
    const adaptiveCard = CardFactory.adaptiveCard({
      type: "AdaptiveCard",
      $schema: "http://adaptivecards.io/schemas/adaptive-card.json",
      version: "1.4",
      body: [
        ...(card.title ? [{ type: "TextBlock", text: card.title, weight: "Bolder", size: "Medium" }] : []),
        ...(card.body ? [{ type: "TextBlock", text: card.body || text, wrap: true }] : []),
        ...(card.footer ? [{ type: "TextBlock", text: card.footer, isSubtle: true, size: "Small" }] : []),
      ],
    });
    const activity = MessageFactory.attachment(adaptiveCard);
    await sendProactiveActivity(chatId, activity);
  },

  async sendTyping(chatId) {
    const ref = conversationReferences.get(chatId);
    if (!ref) return;
    await adapter.continueConversation(ref, async (turnContext) => {
      await turnContext.sendActivities([{ type: "typing" }]);
    });
  },
});

// --- Activity handler ---

/**
 * Process an incoming Bot Framework activity.
 * Extracts message data, downloads attachments, and forwards to ConnectorBase.
 *
 * @param {import('botbuilder').TurnContext} turnContext - The turn context for this activity
 */
async function handleActivity(turnContext) {
  const activity = turnContext.activity;

  // Store conversation reference for proactive messaging
  storeConversationReference(activity);

  // Only process message activities
  if (activity.type !== "message") return;

  const chatId = activity.conversation?.id || "";
  const senderId = activity.from?.aadObjectId || activity.from?.id || "";
  const senderName = activity.from?.name || "";
  const text = removeMentionText(activity);

  const normalized = {
    chatId,
    senderId,
    senderName,
    text,
    extra: {
      msg_id: activity.id,
      conversation_type: activity.conversation?.conversationType || "personal",
      tenant_id: activity.conversation?.tenantId || "",
    },
  };

  // Handle attachments (images, documents)
  if (activity.attachments && activity.attachments.length > 0) {
    for (const attachment of activity.attachments) {
      // Skip inline/adaptive cards — they are not file attachments
      if (attachment.contentType === "application/vnd.microsoft.card.adaptive") continue;
      if (attachment.contentType === "text/html") continue;

      const contentUrl = attachment.contentUrl;
      if (!contentUrl) continue;

      const buffer = await downloadAttachment(contentUrl);
      if (buffer) {
        const mediaType = classifyContentType(attachment.contentType);
        const mediaPath = await connector.saveMediaBuffer(buffer, mediaType);
        normalized.media = {
          type: mediaType,
          path: mediaPath,
          mime: attachment.contentType || "",
          size: buffer.length,
          buffer,
        };
        break; // Process first file attachment only
      }
    }
  }

  await connector.handleIncoming(normalized);
}

/**
 * Remove the @mention text of the bot from the activity text.
 * Teams includes the bot @mention as part of the message text.
 *
 * @param {import('botbuilder').Activity} activity - The incoming activity
 * @returns {string} Message text with bot mention removed
 */
function removeMentionText(activity) {
  let text = activity.text || "";
  if (activity.entities) {
    for (const entity of activity.entities) {
      if (entity.type === "mention" && entity.mentioned?.id === appId) {
        const mentionText = entity.text || "";
        text = text.replace(mentionText, "").trim();
      }
    }
  }
  return text;
}

// --- HTTP Server ---

const server = restify.createServer({ name: "arqitect-teams" });
server.use(restify.plugins.bodyParser());

server.post("/api/messages", async (req, res) => {
  await adapter.process(req, res, handleActivity);
});

// Health check endpoint
server.get("/health", (req, res) => {
  res.send(200, { status: "ok", connector: "teams" });
});

// --- Main ---

async function main() {
  await connector.start({ port });

  server.listen(port, () => {
    console.log(`[TEAMS] HTTP server listening on port ${port}`);
    console.log(`[TEAMS] Messaging endpoint: http://localhost:${port}/api/messages`);
    console.log("[TEAMS] Bot launched. Waiting for activities...");
  });

  process.once("SIGINT", () => {
    server.close();
    process.exit(0);
  });
  process.once("SIGTERM", () => {
    server.close();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("[TEAMS] Fatal:", err);
  process.exit(1);
});
