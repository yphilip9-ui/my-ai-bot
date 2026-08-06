import http from "node:http";

const PORT = Number(process.env.PORT || 3000);

const {
  OPENAI_API_KEY,
  OPENAI_MODEL = "gpt-4.1-mini",
  GREEN_API_ID_INSTANCE,
  GREEN_API_TOKEN_INSTANCE,
  OWNER_CHAT_ID,
  HAGIT_CHAT_ID,
  HAGIT_NAME = "\u05d7\u05d2\u05d9\u05ea",
  DRY_RUN = "false"
} = process.env;

function json(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(data)
  });
  res.end(data);
}

async function readJson(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString("utf8");
  if (!raw) return {};
  return JSON.parse(raw);
}

function getIncomingMessage(payload) {
  const messageData = payload?.messageData || {};
  const type = messageData?.typeMessage;
  const text =
    messageData?.textMessageData?.textMessage ||
    messageData?.extendedTextMessageData?.text ||
    messageData?.quotedMessage?.textMessage ||
    "";

  return {
    webhookType: payload?.typeWebhook,
    senderChatId: payload?.senderData?.chatId || "",
    senderName: payload?.senderData?.senderName || "",
    sender: payload?.senderData?.sender || "",
    timestamp: payload?.timestamp,
    type,
    text
  };
}

function isFromHagit(message) {
  if (HAGIT_CHAT_ID && message.senderChatId === HAGIT_CHAT_ID) return true;
  return Boolean(message.senderName && message.senderName.includes(HAGIT_NAME));
}

async function askOpenAI(message) {
  if (!OPENAI_API_KEY) {
    throw new Error("Missing OPENAI_API_KEY");
  }

  const prompt = [
    "You are Isaiah's Hebrew-language assistant for drafting replies to his sister Hagit on WhatsApp.",
    "Goal: calm the situation, sound human, set financial boundaries when needed, and never send anything automatically as Isaiah.",
    "Return the answer in Hebrew, in this short structure:",
    "1. A brief emotional summary of what she is saying.",
    "2. Any risk/red flag if relevant.",
    "3. A recommended WhatsApp draft reply.",
    "",
    `Sender name: ${message.senderName || "unknown"}`,
    `Message type: ${message.type || "unknown"}`,
    `Content: ${message.text || "[No text; possibly a voice note or image]"}`
  ].join("\n");

  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      "authorization": `Bearer ${OPENAI_API_KEY}`,
      "content-type": "application/json"
    },
    body: JSON.stringify({
      model: OPENAI_MODEL,
      input: prompt
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`OpenAI error ${response.status}: ${errorText}`);
  }

  const data = await response.json();
  return data.output_text || data.output?.flatMap(item => item.content || [])
    .map(part => part.text || "")
    .join("\n")
    .trim();
}

async function sendWhatsApp(chatId, text) {
  if (DRY_RUN === "true") {
    console.log("DRY_RUN sendWhatsApp", { chatId, text });
    return { dryRun: true };
  }
  if (!GREEN_API_ID_INSTANCE || !GREEN_API_TOKEN_INSTANCE) {
    throw new Error("Missing GREEN_API_ID_INSTANCE or GREEN_API_TOKEN_INSTANCE");
  }
  if (!chatId) {
    throw new Error("Missing destination chatId");
  }

  const url = `https://api.green-api.com/waInstance${GREEN_API_ID_INSTANCE}/sendMessage/${GREEN_API_TOKEN_INSTANCE}`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chatId, message: text })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GREEN-API send error ${response.status}: ${errorText}`);
  }
  return response.json();
}

function formatOwnerMessage(message, analysis) {
  return [
    "\u05d4\u05d5\u05d3\u05e2\u05d4 \u05d7\u05d3\u05e9\u05d4 \u05de\u05d7\u05d2\u05d9\u05ea:",
    message.text || `[${message.type || "message without text"}]`,
    "",
    "\u05e0\u05d9\u05ea\u05d5\u05d7 GPT:",
    analysis
  ].join("\n");
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/health") {
      return json(res, 200, { ok: true });
    }

    if (req.method !== "POST" || req.url !== "/webhook") {
      return json(res, 404, { ok: false, error: "Not found" });
    }

    const payload = await readJson(req);
    const message = getIncomingMessage(payload);

    console.log("Incoming webhook", JSON.stringify(message));

    if (message.webhookType !== "incomingMessageReceived") {
      return json(res, 200, { ok: true, ignored: "not incomingMessageReceived" });
    }

    if (!isFromHagit(message)) {
      return json(res, 200, { ok: true, ignored: "not Hagit", message });
    }

    const analysis = await askOpenAI(message);
    const outgoing = formatOwnerMessage(message, analysis);
    const sendResult = await sendWhatsApp(OWNER_CHAT_ID, outgoing);

    return json(res, 200, { ok: true, sent: sendResult });
  } catch (error) {
    console.error(error);
    return json(res, 500, { ok: false, error: error.message });
  }
});

server.listen(PORT, () => {
  console.log(`hagit-gpt-bridge listening on ${PORT}`);
});
