import telebot
from openai import OpenAI
import os
from dotenv import load_dotenv
import base64
import traceback
from datetime import date

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
XAI_API_KEY = os.getenv('XAI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

user_histories = {}
user_modes = {}
usage_today = {"date": str(date.today()), "input": 0, "output": 0}

# ================== MENU & COMMAND ==================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """👋 *Halo Iyud! Grok V4.2 Monitoring Credit*

Mode: Auto Hemat
Command baru:
/stats → lihat penggunaan token & biaya hari ini
/cheap → mode super irit
/smart → mode full pintar
/clear → hapus history
/help → bantuan lengkap""", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, """*Command Lengkap:*
/start - Welcome
/stats - Statistik token & biaya hari ini
/cheap - Mode super hemat
/smart - Mode full pintar
/mode - Cek mode sekarang
/clear - Hapus history
/help - Bantuan ini

Kirim teks atau foto bebas!""", parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def show_stats(message):
    today = str(date.today())
    if usage_today["date"] != today:
        usage_today["date"] = today
        usage_today["input"] = 0
        usage_today["output"] = 0
    
    input_t = usage_today["input"]
    output_t = usage_today["output"]
    
    # Harga resmi xAI (per 1 juta token)
    model_now = user_modes.get(message.chat.id, "auto")
    if model_now == "smart":
        input_rate = 2.00
        output_rate = 6.00
    else:
        input_rate = 0.20
        output_rate = 0.50
    
    cost = (input_t * input_rate + output_t * output_rate) / 1_000_000
    
    text = f"""📊 **Statistik Hari Ini ({today})**

Input Tokens : {input_t:,}
Output Tokens: {output_t:,}
Total Tokens : {input_t + output_t:,}

Estimasi Biaya: **${cost:.4f} USD**

Mode sekarang: {model_now.upper()}
(/cheap untuk irit, /smart untuk foto)"""
    bot.reply_to(message, text)

@bot.message_handler(commands=['cheap', 'smart', 'mode', 'clear'])
def handle_commands(message):
    chat_id = message.chat.id
    cmd = message.text.lower()
    
    if cmd == '/cheap':
        user_modes[chat_id] = "cheap"
        bot.reply_to(message, "✅ Mode **Super Hemat** aktif!")
    elif cmd == '/smart':
        user_modes[chat_id] = "smart"
        bot.reply_to(message, "✅ Mode **Full Pintar** aktif!")
    elif cmd == '/mode':
        mode = user_modes.get(chat_id, "auto")
        bot.reply_to(message, f"Mode sekarang: **{mode.upper()}**")
    elif cmd == '/clear':
        user_histories[chat_id] = []
        bot.reply_to(message, "✅ History dihapus!")

# ================== MAIN HANDLER ==================
@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    if chat_id not in user_histories:
        user_histories[chat_id] = []
    if chat_id not in user_modes:
        user_modes[chat_id] = "auto"

    try:
        # Pilih model otomatis
        if user_modes[chat_id] == "smart" or message.photo:
            model = "grok-4.20-reasoning"
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
            bot.reply_to(message, f"📸 Menganalisis foto...")

        else:
            text = message.text.strip()
            messages_to_send = user_histories[chat_id] + [{"role": "user", "content": text}]

        response = client.chat.completions.create(
            model=model,
            messages=messages_to_send
        )
        reply = response.choices[0].message.content

        # === UPDATE USAGE STATS ===
        if hasattr(response, 'usage') and response.usage:
            input_t = response.usage.prompt_tokens or 0
            output_t = response.usage.completion_tokens or 0
            usage_today["input"] += input_t
            usage_today["output"] += output_t

        # Simpan history
        user_content = caption if message.photo else message.text
        user_histories[chat_id].append({"role": "user", "content": user_content})
        user_histories[chat_id].append({"role": "assistant", "content": reply})

        if len(user_histories[chat_id]) > 20:
            user_histories[chat_id] = user_histories[chat_id][-20:]

        bot.reply_to(message, reply)

    except Exception as e:
        bot.reply_to(message, "❌ Error kecil, coba lagi atau ketik /stats")

print("✅ Bot Grok V4.2 (Monitoring Credit) sudah nyala!")
bot.infinity_polling()