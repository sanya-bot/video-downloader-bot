import os
import threading
import time
from flask import Flask
import telebot
import yt_dlp

# --- Твой токен бота ---
BOT_TOKEN = "8289812320:AAHSGU3hsumhw525yH9NNBawhVxvRjxd0Jo"
bot = telebot.TeleBot(BOT_TOKEN)

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
            'cookies': 'cookies.txt',  # <-- Путь к твоему файлу cookies
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open("video.mp4", "rb") as f:
            bot.send_video(message.chat.id, f)

        os.remove("video.mp4")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠ Ошибка: {e}")

# --- Мини HTTP-сервер для Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- Запуск бота с автоперезапуском ---
def run_bot():
    print("Бот запущен...")
    while True:
        try:
            bot.polling(non_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()

