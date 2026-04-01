import telebot
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
XAI_API_KEY = os.getenv('XAI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

# MEMORY CHAT
user_histories = {}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if text == "/clear":
        user_histories[chat_id] = []
        bot.reply_to(message, "✅ History dihapus!")
        return

    if chat_id not in user_histories:
        user_histories[chat_id] = []
    
    user_histories[chat_id].append({"role": "user", "content": text})
    if len(user_histories[chat_id]) > 20:
        user_histories[chat_id] = user_histories[chat_id][-20:]

    try:
        response = client.chat.completions.create(
            model="grok-4.20-reasoning",
            messages=user_histories[chat_id]
        )
        reply = response.choices[0].message.content
        user_histories[chat_id].append({"role": "assistant", "content": reply})
        bot.reply_to(message, reply)
    except:
        bot.reply_to(message, "❌ Coba lagi ya.")

print("✅ Bot Grok V3.0 (Memory + siap Railway) sudah nyala!")
bot.infinity_polling()