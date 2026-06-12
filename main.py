import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Green-API settings from Render Environment Variables
GREENAPI_INSTANCE = os.environ.get("GREENAPI_INSTANCE")
GREENAPI_TOKEN = os.environ.get("GREENAPI_TOKEN")
GREENAPI_BASE_URL = "https://7107.api.greenapi.com"

# המספר היחיד שהבוט מורשה לענות לו
# כרגע זה המספר האמריקאי שלך
ALLOWED_CHAT_ID = "13473149293@c.us"


def send_whatsapp_message(chat_id, message):
    """
    Sends a WhatsApp message using Green-API.
    """
    url = f"{GREENAPI_BASE_URL}/waInstance{GREENAPI_INSTANCE}/sendMessage/{GREENAPI_TOKEN}"

    payload = {
        "chatId": chat_id,
        "message": message
    }

    response = requests.post(url, json=payload, timeout=30)

    print(f"Green-API send status: {response.status_code}")
    print(f"Green-API send response: {response.text}")

    return response


@app.route("/", methods=["GET"])
def home():
    return "WhatsApp bot is running", 200


@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    try:
        data = request.get_json(silent=True)

        print("Webhook received")

        if not data:
            print("Ignored: empty webhook data")
            return jsonify({"status": "ignored empty data"}), 200

        webhook_type = data.get("typeWebhook")
        print(f"typeWebhook: {webhook_type}")

        # נטפל רק בהודעות נכנסות
        if webhook_type != "incomingMessageReceived":
            print("Ignored: not an incoming message")
            return jsonify({"status": "ignored not incoming message"}), 200

        sender_data = data.get("senderData", {})
        sender = sender_data.get("chatId", "")

        print(f"Sender: {sender}")

        # חסימת קבוצות
        if sender.endswith("@g.us"):
            print(f"Ignored group message from {sender}")
            return jsonify({"status": "ignored group message"}), 200

        # אישור רק למספר המורשה
        if sender != ALLOWED_CHAT_ID:
            print(f"Ignored unauthorized sender: {sender}")
            return jsonify({"status": "ignored unauthorized sender"}), 200

        message_data = data.get("messageData", {})
        message_type = message_data.get("typeMessage")

        print(f"Message type: {message_type}")

        # נטפל רק בהודעות טקסט
        if message_type != "textMessage":
            print("Ignored: not a text message")
            send_whatsapp_message(
                sender,
                "כרגע אני יודע לענות רק להודעות טקסט 🙂"
            )
            return jsonify({"status": "ignored non text message"}), 200

        incoming_msg = (
            message_data
            .get("textMessageData", {})
            .get("textMessage", "")
            .strip()
        )

        if not incoming_msg:
            print("Ignored: empty text message")
            return jsonify({"status": "ignored empty message"}), 200

        print(f"Received message from {sender}: {incoming_msg}")

        # שליחת ההודעה ל-GPT
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "אתה עוזר אישי חכם בווטסאפ. "
                        "ענה בעברית בצורה קצרה, ברורה, נעימה ומעשית. "
                        "אל תאריך מדי. "
                        "אם השאלה לא ברורה, שאל שאלה קצרה להבהרה."
                    )
                },
                {
                    "role": "user",
                    "content": incoming_msg
                }
            ]
        )

        bot_response = completion.choices[0].message.content.strip()

        print(f"Bot response: {bot_response}")

        # שליחת התשובה חזרה לווטסאפ
        send_whatsapp_message(sender, bot_response)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error: {e}")

        # חשוב: גם במקרה של שגיאה נחזיר 200
        # כדי ש-GREEN-API לא ינסה לשלוח שוב ושוב את אותה הודעה
        return jsonify({"status": "error handled", "message": str(e)}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
