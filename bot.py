import os
import telebot
from telebot import types
from datetime import datetime, timedelta
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")  # Токен бота из переменных окружения
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения количества скачек на пользователя
user_downloads = {}
reset_time = datetime.now() + timedelta(days=1)
MAX_DOWNLOADS = 10  # Лимит скачек в день

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📥 Скачать видео", "ℹ️ Помощь")
    markup.add("💬 Мой канал")
    return markup

# Сброс счётчика скачек
def reset_counters():
    global reset_time, user_downloads
    if datetime.now() >= reset_time:
        user_downloads.clear()
        reset_time = datetime.now() + timedelta(days=1)

# Старт
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я помогу тебе скачать видео из TikTok без водяного знака.\n"
        "Отправь мне ссылку на видео, и я всё сделаю.\n\n"
        "📌 Лимит: 10 скачек в день.",
        reply_markup=main_menu()
    )

# Помощь
@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "📖 Инструкция:\n"
        "1. Нажми «📥 Скачать видео»\n"
        "2. Отправь ссылку на TikTok\n"
        "3. Получи видео без водяного знака\n\n"
        f"Лимит: {MAX_DOWNLOADS} скачек в день."
    )

# Обработка кнопок
@bot.message_handler(func=lambda m: True)
def menu_handler(message):
    reset_counters()

    if message.text == "📥 Скачать видео":
        bot.send_message(message.chat.id, "Отправь ссылку на TikTok 🎯")
    elif message.text == "ℹ️ Помощь":
        help_cmd(message)
    elif message.text == "💬 Мой канал":
        bot.send_message(message.chat.id, "Подписывайся ❤️\nhttps://t.me/zametochkysani")
    elif "tiktok.com" in message.text:
        process_tiktok(message)
    else:
        bot.send_message(message.chat.id, "Я тебя не понял 🤔\nВыбери команду в меню.")

# Загрузка видео
def process_tiktok(message):
    user_id = message.from_user.id
    user_downloads[user_id] = user_downloads.get(user_id, 0)

    if user_downloads[user_id] >= MAX_DOWNLOADS:
        bot.send_message(message.chat.id, "🚫 Лимит скачек на сегодня исчерпан!")
        return

    url = message.text
    bot.send_message(message.chat.id, "⏳ Скачиваю видео...")

    try:
        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'mp4',
            'quiet': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = f"video.{info['ext']}"

        with open(video_file, 'rb') as f:
            bot.send_video(message.chat.id, f)

        os.remove(video_file)
        user_downloads[user_id] += 1
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

bot.polling()
