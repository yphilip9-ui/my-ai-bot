import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# הגדרת לקוח ה-OpenAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# נתוני ה-Green-API מהגדרות הסביבה
GREENAPI_INSTANCE = os.environ.get("GREENAPI_INSTANCE")
GREENAPI_TOKEN = os.environ.get("GREENAPI_TOKEN")
GREENAPI_BASE_URL = "https://7107.api.greenapi.com"

@app.route("/whatsapp", methods=['POST'])
def whatsapp_bot():
    try:
        data = request.get_json()
        
        # בדיקה שמדובר בהודעה נכנסת מסוג טקסט
        if not data or data.get('typeWebhook') != 'incomingMessageReceived':
            return jsonify({"status": "ignored"}), 200
            
        message_data = data.get('messageData', {})
        if message_data.get('typeMessage') != 'textMessage':
            return jsonify({"status": "ignored"}), 200

        # שליפת השולח ותוכן ההודעה
        sender = data.get('senderData', {}).get('chatId', '')
        incoming_msg = message_data.get('textMessageData', {}).get('textMessage', '')

        print(f"Received message from {sender}: {incoming_msg}")

        # פנייה ל-OpenAI לקבלת תשובה
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "אתה עוזר אישי חכם. ענה בצורה נחמדה, קצרה ומשעשעת בעברית."},
                {"role": "user", "content": incoming_msg}
            ]
        )
        bot_response = completion.choices[0].message.content
        print(f"Bot response: {bot_response}")

        # שליחת התשובה חזרה לשולח
        url = f"{GREENAPI_BASE_URL}/waInstance{GREENAPI_INSTANCE}/sendMessage/{GREENAPI_TOKEN}"
        payload = {
            "chatId": sender,
            "message": bot_response
        }
        
        response = requests.post(url, json=payload)
        print(f"Green-API Status: {response.status_code}")
        
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
