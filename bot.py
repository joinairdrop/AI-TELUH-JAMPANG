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
    bot.reply_to(message, """🖼️ **Grok Image Generator V6.1**

Cara pakai:
Ketik deskripsi gambar yang kamu mau, contoh:
- "mobil sport merah di jalanan jakarta malam hari, realistic, detail tinggi"
- "gadis anime rambut pink sedang minum kopi di kafe malam hari"

Aku akan generate dan kirim gambar langsung ke chat.

Mau coba sekarang? Gas ketik deskripsinya! 🔥""")

@bot.message_handler(func=lambda message: True)
def generate_image(message):
    prompt = message.text.strip()
    
    if len(prompt) < 10:
        bot.reply_to(message, "Deskripsi terlalu pendek bro. Kasih detail lebih banyak ya.")
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')
    msg = bot.reply_to(message, "🖼️ Sedang generate gambar dengan Grok... Tunggu sebentar.")

    try:
        response = client.images.generate(
            model="grok-imagine-image",     # Model image resmi xAI saat ini
            prompt=prompt,
            n=1,
            size="1024x1024"
            # quality dihapus karena error
        )

        image_url = response.data[0].url

        # Kirim gambar langsung ke Telegram
        bot.send_photo(
            chat_id=message.chat.id,
            photo=image_url,
            caption=f"✅ Berhasil dibuat dengan Grok!\n\nPrompt: {prompt[:200]}...",
            reply_to_message_id=message.message_id
        )

        # Hapus pesan "sedang generate"
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        error_str = str(e)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"❌ Gagal generate gambar.\n\nError: {error_str[:300]}"
        )

print("✅ Bot Grok V6.1 (Image Generator Fixed) sudah nyala!")
bot.infinity_polling()