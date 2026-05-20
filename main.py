# my-ai-bot
import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# התחברות ל-OpenAI באמצעות המפתח הסודי שהגדרנו ב-Render
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# הגדרת פרטי הגישה של Green-API (יוגדרו בהמשך ב-Render)
GREENAPI_INSTANCE = os.environ.get("GREENAPI_INSTANCE")
GREENAPI_TOKEN = os.environ.get("GREENAPI_TOKEN")

# מספר הטלפון של אחותך כפי שהוא מגיע ב-Green-API (בפורמט: מספר@c.us)
SISTER_CHAT_ID = "13473149293@c.us"

@app.route("/whatsapp", methods=['POST'])
def whatsapp_bot():
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

    # בדיקה: האם ההודעה הגיעה מאחותך?
    if sender == SISTER_CHAT_ID:
        try:
            # פנייה ל-OpenAI לקבלת תשובה מהבוט
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "אתה עוזר אישי של אח של המשתמשת. תענה לה בצורה נחמדה, קצרה ומשעשעת בעברית."},
                    {"role": "user", "content": incoming_msg}
                ]
            )
            bot_response = completion.choices[0].message.content
            
            # שליחת התשובה חזרה לאחותך דרך Green-API
            url = f"https://api.green-api.com/waInstance{GREENAPI_INSTANCE}/sendMessage/{GREENAPI_TOKEN}"
            payload = {
                "chatId": SISTER_CHAT_ID,
                "message": bot_response
            }
            requests.post(url, json=payload)
            
        except Exception as e:
            print(f"Error: {e}")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)