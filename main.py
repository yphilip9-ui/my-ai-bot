# my-ai-bot
import os
from flask import Flask, request
from openai import OpenAI
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# התחברות ל-OpenAI באמצעות המפתח הסודי שנגדיר בשרת
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# הגדרת מספר הטלפון של אחותך (למשל: 972501234567+)
SISTER_PHONE_NUMBER = "whatsapp:+13473149293" 

@app.route("/whatsapp", methods=['POST'])
def whatsapp_bot():
    # קבלת מספר הטלפון של השולח וההודעה שלו
    sender = request.values.get('From', '')
    incoming_msg = request.values.get('Body', '')
    
    resp = MessagingResponse()
    
    # בדיקה: האם ההודעה הגיעה מאחותך?
    if sender == SISTER_PHONE_NUMBER:
        try:
            # שליחת ההודעה ל-OpenAI לקבלת תשובה
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini", # מודל מעולה, מהיר וזול לבוטים
                messages=[
                    {"role": "system", "content": "אתה עוזר אישי של אח של המשתמשת. תענה לה בצורה נחמדה, קצרה ומשעשעת בעברית."},
                    {"role": "user", "content": incoming_msg}
                ]
            )
            
            # שליחת התשובה חזרה לוואטסאפ
            bot_response = completion.choices[0].message.content
            resp.message(bot_response)
            
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            resp.message("אופס, משהו השתבש בחיבור ל-OpenAI.")
    else:
        # אם מישהו אחר שולח הודעה, הבוט לא יענה לו כדי לא להפריע
        pass

    return str(resp)

if __name__ == "__main__":
    # הרצת השרת בפורט 5000
    app.run(host='0.0.0.0', port=5000)