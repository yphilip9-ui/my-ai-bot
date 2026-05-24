# my-ai-bot

import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Environment variables from Render
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GREENAPI_INSTANCE = os.environ.get("GREENAPI_INSTANCE")
GREENAPI_TOKEN = os.environ.get("GREENAPI_TOKEN")

# Green-API base URL for your instance
GREENAPI_BASE_URL = "https://7107.api.greenapi.com"

# Your sister's WhatsApp chat ID
# Format: international phone number without +, then @c.us
SISTER_CHAT_ID = "13473149293@c.us"

# Check required environment variables
if not OPENAI_API_KEY:
    print("ERROR: Missing OPENAI_API_KEY")

if not GREENAPI_INSTANCE:
    print("ERROR: Missing GREENAPI_INSTANCE")

if not GREENAPI_TOKEN:
    print("ERROR: Missing GREENAPI_TOKEN")

# OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200


@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    try:
        data = request.get_json()

        print("Incoming webhook:", data)

        # Check that this is an incoming WhatsApp message
        if not data or data.get("typeWebhook") != "incomingMessageReceived":
            print("Ignored: not an incoming message")
            return jsonify({"status": "ignored"}), 200

        message_data = data.get("messageData", {})

        # Only answer text messages
        if message_data.get("typeMessage") != "textMessage":
            print("Ignored: not a text message")
            return jsonify({"status": "ignored"}), 200

        # Get sender and message text
        sender = data.get("senderData", {}).get("chatId", "")
        incoming_msg = message_data.get("textMessageData", {}).get("textMessage", "")

        print("Sender:", sender)
        print("Message:", incoming_msg)

        # Only answer your sister
        if sender != SISTER_CHAT_ID:
            print("Ignored: sender is not sister")
            return jsonify({"status": "ignored_not_sister"}), 200

        # Ask OpenAI for a response
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "אתה עוזר אישי של אח של המשתמשת. "
                        "תענה לה בצורה נחמדה, קצרה, רגועה ומשעשעת בעברית. "
                        "אל תכתוב תשובות ארוכות מדי."
                    ),
                },
                {
                    "role": "user",
                    "content": incoming_msg,
                },
            ],
        )

        bot_response = completion.choices[0].message.content

        print("Bot response:", bot_response)

        # Send the response back through Green-API
        url = (
            f"{GREENAPI_BASE_URL}/waInstance{GREENAPI_INSTANCE}"
            f"/sendMessage/{GREENAPI_TOKEN}"
        )

        payload = {
            "chatId": SISTER_CHAT_ID,
            "message": bot_response,
        }

        response = requests.post(url, json=payload)

        print("Green-API response status:", response.status_code)
        print("Green-API response text:", response.text)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
