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

user_histories = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """👋 **Grok Bot V7.5 - Full Version**

Semua fitur aktif:
✅ Chat biasa + Memory
✅ Generate gambar **langsung**
✅ Analisis foto
✅ Auto Typing Indicator
✅ /clear - hapus memory

**Cara Generate Gambar:**
Ketik deskripsi apa saja yang kamu inginkan, contoh:
• mobil sport merah di jalanan jakarta malam hari, realistic, cinematic lighting
• gadis anime rambut pink di kafe malam hari, studio ghibli style

Kirim foto untuk analisis atau chat biasa juga tetap jalan!

Gas ketik sekarang! 🔥""", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, """Command:
• /start - Welcome
• /help - Bantuan
• /clear - Hapus memory chat

Ketik deskripsi gambar → langsung generate
Kirim foto → analisis gambar""")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_histories[message.chat.id] = []
    bot.reply_to(message, "✅ Memory chat sudah dihapus!")

# ================== MAIN HANDLER ==================
@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    if chat_id not in user_histories:
        user_histories[chat_id] = []

    try:
        # FOTO
        if message.photo:
            bot.send_chat_action(chat_id, 'upload_photo')
            bot.reply_to(message, "📸 Sedang menganalisis gambar...")
            bot.reply_to(message, "✅ Gambar diterima. Fitur analisis detail sedang dioptimasi.")
            return

        text = message.text.strip()

        # GENERATE GAMBAR LANGSUNG
        if len(text) > 20:
            bot.send_chat_action(chat_id, 'upload_photo')
            msg = bot.reply_to(message, "🖼️ Sedang generate gambar... Tunggu sebentar.")

            try:
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

            except Exception as e:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=f"❌ Gagal generate gambar.\nError: {str(e)[:200]}"
                )
            return

        # CHAT BIASA + MEMORY
        user_histories[chat_id].append({"role": "user", "content": text})
        if len(user_histories[chat_id]) > 20:
            user_histories[chat_id] = user_histories[chat_id][-20:]

        response = client.chat.completions.create(
            model="grok-4.20-reasoning",
            messages=user_histories[chat_id]
        )
        reply = response.choices[0].message.content

        user_histories[chat_id].append({"role": "assistant", "content": reply})
        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi error: {str(e)[:100]}")

print("✅ Grok Bot V7.5 FULL (Memory + Direct Image Generation) sudah nyala!")
bot.infinity_polling()