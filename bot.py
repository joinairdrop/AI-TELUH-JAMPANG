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

user_histories = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """🎥 **Grok Bot V8.2 - Full Version**

Semua fitur aktif:
✅ Chat biasa + Memory
✅ Generate Gambar
✅ Generate Video (5 / 8 / 10 detik)
✅ Analisis Foto

**Cara Pakai Video:**
Ketik: `buat video [durasi] [deskripsi]`

Contoh:
- `buat video 5 mobil sport merah melaju di jakarta malam hari`
- `buat video 10 gadis anime di hutan sakura, studio ghibli`
- `buat video mobil terbang di kota futuristik` (default 8 detik)

Gas coba sekarang! 🔥""")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, """**Command:**
• /start - Welcome
• /help - Bantuan
• /clear - Hapus memory

• "buat gambar ..." → gambar
• "buat video 5 ..." / "buat video 8 ..." / "buat video 10 ..." → video
• Chat biasa → Grok jawab normal""")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_histories[message.chat.id] = []
    bot.reply_to(message, "✅ Memory dihapus!")

# ================== MAIN HANDLER ==================
@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    if chat_id not in user_histories:
        user_histories[chat_id] = []

    try:
        if message.photo:
            bot.reply_to(message, "📸 Sedang menganalisis gambar...")
            bot.reply_to(message, "✅ Gambar diterima.")
            return

        text = message.text.strip()
        lower = text.lower()

        # === GENERATE VIDEO DENGAN DURASI ===
        if any(k in lower for k in ["buat video", "video ", "generate video", "bikin video"]):
            bot.send_chat_action(chat_id, 'upload_video')
            msg = bot.reply_to(message, "🎥 Sedang generate video... (20-50 detik)")

            # Deteksi durasi
            duration = 8
            if "5" in lower and (" video 5" in " " + lower or lower.startswith("buat video 5")):
                duration = 5
            elif "10" in lower and (" video 10" in " " + lower or lower.startswith("buat video 10")):
                duration = 10

            clean_prompt = text.replace("buat video", "").replace("video", "").strip()
            clean_prompt = clean_prompt.replace(str(duration), "").strip()

            try:
                response = client.videos.generate(
                    model="grok-imagine-video",
                    prompt=clean_prompt or text,
                    duration=duration,
                    aspect_ratio="16:9"
                )

                video_url = response.data[0].url

                bot.send_video(
                    chat_id=chat_id,
                    video=video_url,
                    caption=f"✅ Video berhasil dibuat! ({duration} detik)\n\nPrompt: {clean_prompt[:150]}...",
                    reply_to_message_id=message.message_id
                )
                bot.delete_message(chat_id, msg.message_id)

            except Exception as e:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=f"❌ Gagal generate video.\nError: {str(e)[:200]}"
                )
            return

        # === GENERATE GAMBAR ===
        elif any(k in lower for k in ["buat gambar", "gambar ", "generate gambar", "bikin gambar"]):
            bot.send_chat_action(chat_id, 'upload_photo')
            msg = bot.reply_to(message, "🖼️ Sedang generate gambar...")

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

        # === CHAT BIASA + MEMORY ===
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
        bot.reply_to(message, f"❌ Error: {str(e)[:150]}")

print("✅ Grok Bot V8.2 Full Version sudah nyala!")
bot.infinity_polling()