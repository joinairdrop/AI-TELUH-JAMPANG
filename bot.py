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

# MEMORY CHAT (teks saja, biar ringan)
user_histories = {}

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    chat_id = message.chat.id

    # Command clear
    if message.text == "/clear":
        user_histories[chat_id] = []
        bot.reply_to(message, "✅ History dihapus! Mulai baru ya.")
        return

    # Siapkan history teks
    if chat_id not in user_histories:
        user_histories[chat_id] = []

    try:
        if message.photo:
            # === HANDLE FOTO ===
            photo = message.photo[-1]  # foto ukuran terbesar
            file_url = bot.get_file_url(photo.file_id)
            caption = message.caption or "Deskripsikan gambar ini secara detail dan jawab apa yang kamu lihat."

            current_message = [
                {"type": "text", "text": caption},
                {"type": "image_url", "image_url": {"url": file_url, "detail": "high"}}
            ]
            
            messages_to_send = user_histories[chat_id] + [{"role": "user", "content": current_message}]
            
            bot.reply_to(message, "📸 Sedang menganalisis gambar...")

        else:
            # === HANDLE TEKS BIASA ===
            text = message.text.strip()
            current_message = text
            messages_to_send = user_histories[chat_id] + [{"role": "user", "content": current_message}]

        # Kirim ke Grok (support vision + text)
        response = client.chat.completions.create(
            model="grok-4.20-reasoning",
            messages=messages_to_send
        )
        reply = response.choices[0].message.content

        # Simpan reply ke memory (teks saja)
        user_histories[chat_id].append({"role": "user", "content": current_message if isinstance(current_message, str) else caption})
        user_histories[chat_id].append({"role": "assistant", "content": reply})

        # Batasi memory (20 pesan)
        if len(user_histories[chat_id]) > 20:
            user_histories[chat_id] = user_histories[chat_id][-20:]

        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, "❌ Error kecil, coba kirim lagi ya.")

print("✅ Bot Grok V3.1 (Memory + Vision Foto) sudah nyala!")
bot.infinity_polling()