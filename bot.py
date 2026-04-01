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

# ================== WELCOME & MENU ==================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """👋 *Halo Iyud! Selamat datang di Grok V4.0*

Aku siap bantu kamu 24/7!

📸 Kirim foto + caption (atau tanpa caption)
💬 Chat biasa
🧹 `/clear` → hapus history obrolan
❓ `/help` → lihat semua command

Mau mulai? Ketik apa saja atau kirim foto! 🔥"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """*Command yang tersedia:*

/start - Mulai bot + welcome
/help - Tampilkan bantuan ini
/clear - Hapus semua history obrolan

Kirim foto atau teks bebas, aku akan jawab dengan memory + vision!

Bot ini selalu online 24/7 di Railway."""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['clear'])
def clear_history(message):
    chat_id = message.chat.id
    user_histories[chat_id] = []
    bot.reply_to(message, "✅ History obrolan sudah dihapus total!\nKita mulai dari nol lagi ya.")

# ================== MAIN HANDLER (Teks + Foto) ==================
@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    chat_id = message.chat.id

    # Typing indicator (sedang mengetik...)
    bot.send_chat_action(chat_id, 'typing')

    if chat_id not in user_histories:
        user_histories[chat_id] = []

    try:
        if message.photo:
            # === VISION FOTO (Base64) ===
            photo = message.photo[-1]
            file_info = bot.get_file(photo.file_id)
            photo_bytes = bot.download_file(file_info.file_path)
            base64_image = base64.b64encode(photo_bytes).decode('utf-8')
            
            caption = message.caption or "Deskripsikan gambar ini secara detail dan jawab apa yang kamu lihat."
            content = [
                {"type": "text", "text": caption},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}
            ]
            messages_to_send = user_histories[chat_id] + [{"role": "user", "content": content}]
            bot.reply_to(message, "📸 Sedang menganalisis gambar...")

        else:
            # === TEKS BIASA ===
            text = message.text.strip()
            messages_to_send = user_histories[chat_id] + [{"role": "user", "content": text}]

        # Panggil Grok
        response = client.chat.completions.create(
            model="grok-4.20-reasoning",
            messages=messages_to_send
        )
        reply = response.choices[0].message.content

        # Simpan ke memory
        user_content = caption if message.photo else message.text
        user_histories[chat_id].append({"role": "user", "content": user_content})
        user_histories[chat_id].append({"role": "assistant", "content": reply})

        if len(user_histories[chat_id]) > 20:
            user_histories[chat_id] = user_histories[chat_id][-20:]

        bot.reply_to(message, reply)

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"ERROR: {str(e)}")
        bot.reply_to(message, "❌ Maaf ada error kecil.\nCoba kirim lagi atau ketik /clear dulu.")

print("✅ Bot Grok V4.0 FULL PRO (Menu + Typing + Vision) sudah nyala!")
bot.infinity_polling()