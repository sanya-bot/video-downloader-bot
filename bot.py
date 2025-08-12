import os
from flask import Flask, request
import telebot
import yt_dlp

# --- Настройки ---
BOT_TOKEN = "8289812320:AAHSGU3hsumhw525yH9NNBawhVxvRjxd0Jo"
bot = telebot.TeleBot(BOT_TOKEN)

# URL твоего приложения на Render (пример: https://sanya-bot.onrender.com)
WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"

# --- Flask ---
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route("/", methods=['GET'])
def index():
    return "Бот запущен через webhook!", 200

# --- Команда /start ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! 👋 Отправь мне ссылку на видео с YouTube, TikTok или Instagram, и я пришлю его без водяных знаков."
    )

# --- Обработка ссылок ---
@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if not any(site in url for site in ["tiktok.com", "youtu", "instagram.com"]):
        bot.send_message(message.chat.id, "Отправь корректную ссылку на видео.")
        return

    bot.send_message(message.chat.id, "⏳ Скачиваю...")

    try:
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': 'video.%(ext)s',
            'noplaylist': True,
            'cookies': 'cookies.txt'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open("video.mp4", "rb") as f:
            bot.send_video(message.chat.id, f)

        os.remove("video.mp4")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠ Ошибка: {e}")

# --- Запуск ---
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
