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
user_modes = {}  # "cheap" atau "smart"

# ================== MENU ==================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """👋 *Halo Iyud! Grok V4.1 Hemat Credit*

Mode sekarang: **Auto Hemat** (teks murah, foto pintar)
Command baru:
/cheap → pakai mode super irit
/smart → pakai mode full pintar
/help → bantuan lengkap""", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, """*Command Hemat Credit:*
/start - Welcome
/help - Bantuan ini
/clear - Hapus history
/cheap - Mode super murah
/smart - Mode full pintar (lebih bagus)

/mode - Cek mode sekarang

Kirim teks atau foto bebas!""", parse_mode='Markdown')

@bot.message_handler(commands=['cheap'])
def set_cheap(message):
    user_modes[message.chat.id] = "cheap"
    bot.reply_to(message, "✅ Mode **Super Hemat** aktif! (grok-4-1-fast-reasoning)")

@bot.message_handler(commands=['smart'])
def set_smart(message):
    user_modes[message.chat.id] = "smart"
    bot.reply_to(message, "✅ Mode **Full Pintar** aktif! (grok-4.20-reasoning)")

@bot.message_handler(commands=['mode'])
def check_mode(message):
    mode = user_modes.get(message.chat.id, "auto")
    bot.reply_to(message, f"Mode sekarang: **{mode.upper()}**")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    chat_id = message.chat.id
    user_histories[chat_id] = []
    bot.reply_to(message, "✅ History dihapus!")

# ================== MAIN HANDLER (AUTO HEMAT) ==================
@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    if chat_id not in user_histories:
        user_histories[chat_id] = []
    if chat_id not in user_modes:
        user_modes[chat_id] = "auto"  # default auto hemat

    try:
        # AUTO PILIH MODEL (hemat credit!)
        if user_modes[chat_id] == "smart":
            model = "grok-4.20-reasoning"
        elif message.photo or user_modes[chat_id] == "auto":
            model = "grok-4.20-reasoning" if message.photo else "grok-4-1-fast-reasoning"
        else:
            model = "grok-4-1-fast-reasoning"

        if message.photo:
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
            bot.reply_to(message, f"📸 Menganalisis foto dengan {model}...")

        else:
            text = message.text.strip()
            messages_to_send = user_histories[chat_id] + [{"role": "user", "content": text}]

        response = client.chat.completions.create(
            model=model,
            messages=messages_to_send
        )
        reply = response.choices[0].message.content

        # Simpan history
        user_content = caption if message.photo else message.text
        user_histories[chat_id].append({"role": "user", "content": user_content})
        user_histories[chat_id].append({"role": "assistant", "content": reply})

        if len(user_histories[chat_id]) > 20:
            user_histories[chat_id] = user_histories[chat_id][-20:]

        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, "❌ Error kecil, coba lagi atau ketik /cheap")

print("✅ Bot Grok V4.1 (Auto Hemat Credit) sudah nyala!")
bot.infinity_polling()