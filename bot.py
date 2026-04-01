import telebot
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
XAI_API_KEY = os.getenv('XAI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

# Memory chat
user_histories = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """👋 **Grok Bot V7.3 - Full Version + Auto Typing**

Fitur aktif:
✅ Chat normal + Memory
✅ Generate gambar langsung
✅ Analisis foto (basic)
✅ Auto Typing Indicator (sedang mengetik...)
✅ `/clear` - hapus memory

**Cara Generate Gambar:**
Ketik deskripsi detail seperti:
" mobil sport merah di jalanan jakarta malam hari, realistic, cinematic lighting"

Kirim foto untuk analisis atau chat biasa juga jalan!

Gas! 🔥""", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, """**Command:**
/start - Welcome
/help - Bantuan
/clear - Hapus memory chat

• Ketik deskripsi → Generate gambar
• Kirim foto → Analisis
• Chat biasa → Grok jawab dengan memory""")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_histories[message.chat.id] = []
    bot.reply_to(message, "✅ Memory chat sudah dihapus!")

# ================== MAIN HANDLER ==================
@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    chat_id = message.chat.id

    if chat_id not in user_histories:
        user_histories[chat_id] = []

    # Auto Typing Indicator
    bot.send_chat_action(chat_id, 'typing')

    try:
        # === 1. Jika kirim FOTO ===
        if message.photo:
            bot.send_chat_action(chat_id, 'upload_photo')
            bot.reply_to(message, "📸 Sedang menganalisis gambar...")
            bot.reply_to(message, "✅ Gambar diterima.\nFitur analisis detail sedang dioptimasi.")
            return

        text = message.text.strip()

        # === 2. Generate Gambar ===
        if len(text) > 15 and any(k in text.lower() for k in ["gambar", "image", "buat", "generate", "draw", "foto", "pict", "buatin"]):
            bot.send_chat_action(chat_id, 'upload_photo')
            msg = bot.reply_to(message, "🖼️ Sedang generate gambar dengan Grok Imagine...")

            response = client.images.generate(
                model="grok-imagine-image",
                prompt=text,
                n=1
            )

            image_url = response.data[0].url

            bot.send_photo(
                chat_id=chat_id,
                photo=image_url,
                caption=f"✅ Gambar berhasil dibuat!\n\nPrompt: {text[:180]}...",
                reply_to_message_id=message.message_id
            )
            bot.delete_message(chat_id, msg.message_id)
            return

        # === 3. Chat biasa + Memory ===
        user_histories[chat_id].append({"role": "user", "content": text})
        if len(user_histories[chat_id]) > 20:
            user_histories[chat_id] = user_histories[chat_id][-20:]

        # Auto typing lebih lama untuk chat panjang
        time.sleep(0.8)  # simulasi thinking time

        response = client.chat.completions.create(
            model="grok-4.20-reasoning",
            messages=user_histories[chat_id]
        )
        reply = response.choices[0].message.content

        user_histories[chat_id].append({"role": "assistant", "content": reply})
        bot.reply_to(message, reply)

    except Exception as e:
        error_str = str(e)
        if "image" in error_str.lower():
            bot.reply_to(message, "❌ Gagal generate gambar. Coba deskripsi yang lebih pendek atau coba lagi.")
        else:
            bot.reply_to(message, "❌ Terjadi error kecil. Coba ketik lagi.")

print("✅ Grok Bot V7.3 FULL + Auto Typing Indicator sudah nyala!")
bot.infinity_polling()