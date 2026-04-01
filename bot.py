import telebot
from openai import OpenAI
import os
from dotenv import load_dotenv
import base64
import traceback

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
XAI_API_KEY = os.getenv('XAI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

user_histories = {}

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    chat_id = message.chat.id

    if message.text == "/clear":
        user_histories[chat_id] = []
        bot.reply_to(message, "✅ History dihapus!")
        return

    if chat_id not in user_histories:
        user_histories[chat_id] = []

    try:
        if message.photo:
            # === FIX VISION PAKAI BASE64 ===
            photo = message.photo[-1]
            file_info = bot.get_file(photo.file_id)
            photo_bytes = bot.download_file(file_info.file_path)
            base64_image = base64.b64encode(photo_bytes).decode('utf-8')
            
            caption = message.caption or "Deskripsikan gambar ini secara detail."

            content = [
                {"type": "text", "text": caption},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}
            ]

            messages_to_send = user_histories[chat_id] + [{"role": "user", "content": content}]
            bot.reply_to(message, "📸 Sedang menganalisis gambar...")

        else:
            # Teks biasa
            text = message.text.strip()
            messages_to_send = user_histories[chat_id] + [{"role": "user", "content": text}]

        response = client.chat.completions.create(
            model="grok-4.20-reasoning",
            messages=messages_to_send
        )
        reply = response.choices[0].message.content

        # Simpan ke history (hanya teks supaya ringan)
        user_histories[chat_id].append({"role": "user", "content": caption if message.photo else message.text})
        user_histories[chat_id].append({"role": "assistant", "content": reply})

        if len(user_histories[chat_id]) > 20:
            user_histories[chat_id] = user_histories[chat_id][-20:]

        bot.reply_to(message, reply)

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"❌ ERROR VISION: {str(e)}\n{error_detail}")  # Ini akan keliatan di Railway Logs!
        bot.reply_to(message, f"❌ Error: {str(e)}\nCoba kirim foto lagi ya bro.")

print("✅ Bot Grok V3.2 (Vision Fix + Base64) sudah nyala!")
bot.infinity_polling()