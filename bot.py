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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """👋 Halo! Grok Image Generator aktif.

Cara pakai:
- Ketik deskripsi gambar yang kamu inginkan
- Contoh: "gambar kucing lucu sedang main bola di jakarta malam hari, style anime"
- Aku akan generate dan kirim gambar langsung ke sini.

Mau coba? Ketik saja deskripsinya! 🔥""")

@bot.message_handler(func=lambda message: True)
def generate_image(message):
    prompt = message.text.strip()
    
    if len(prompt) < 5:
        bot.reply_to(message, "Deskripsi terlalu pendek. Coba kasih deskripsi yang lebih detail ya.")
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')
    bot.reply_to(message, "🖼️ Sedang generate gambar... Mohon tunggu sebentar.")

    try:
        response = client.images.generate(
            model="grok-2-image",           # Model image generation dari xAI
            prompt=prompt,
            n=1,                            # generate 1 gambar
            size="1024x1024",               # ukuran standar
            quality="standard"
        )

        image_url = response.data[0].url

        # Kirim gambar langsung ke Telegram (bukan link)
        bot.send_photo(
            chat_id=message.chat.id,
            photo=image_url,
            caption=f"✅ Gambar berhasil dibuat!\n\nPrompt: {prompt}",
            reply_to_message_id=message.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Gagal generate gambar.\nError: {str(e)[:200]}")

print("✅ Bot Grok V6.0 (Image Generator) sudah nyala!")
bot.infinity_polling()