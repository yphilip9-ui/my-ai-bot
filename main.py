# הסרנו את הבדיקה של SISTER_CHAT_ID כדי לענות לכולם
        
        # Ask OpenAI for a response
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "אתה עוזר אישי. "
                        "תענה בצורה נחמדה, קצרה, רגועה ומשעשעת בעברית. "
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

        # Send the response back to the original sender
        url = (
            f"{GREENAPI_BASE_URL}/waInstance{GREENAPI_INSTANCE}"
            f"/sendMessage/{GREENAPI_TOKEN}"
        )

        payload = {
            "chatId": sender,  # משתמשים ב-"sender" במקום ב-"SISTER_CHAT_ID"
            "message": bot_response,
        }

        response = requests.post(url, json=payload)
