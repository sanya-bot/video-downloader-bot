import telebot
from telebot import types
import os
import requests

TOKEN = os.getenv("BOT_TOKEN")  # Токен бота
CHANNEL_USERNAME = "@zametochkysani"  # Юзернейм канала
MAX_FREE_DOWNLOADS = 3  # Лимит бесплатных скачиваний

bot = telebot.TeleBot(TOKEN)

# Хранилище количества скачиваний
user_downloads = {}

# Кнопка подписки
def get_subscribe_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
    markup.add(btn)
    return markup

# Проверка подписки
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# Старт
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Привет! Отправь ссылку на TikTok, и я скачаю видео без водяного знака.")

# Обработка ссылок
@bot.message_handler(func=lambda message: True)
def handle_link(message):
    user_id = message.from_user.id
    url = message.text.strip()

    # Проверка лимита
    if user_id not in user_downloads:
        user_downloads[user_id] = 0

    if user_downloads[user_id] >= MAX_FREE_DOWNLOADS:
        if not is_subscribed(user_id):
            bot.send_message(
                message.chat.id,
                "🚫 Лимит бесплатных скачиваний исчерпан!\nПодпишитесь на наш канал, чтобы продолжить.",
                reply_markup=get_subscribe_keyboard()
            )
            return

    # Скачивание видео
    try:
        api_url = f"https://api.douyin.wtf/api?url={url}"
        response = requests.get(api_url).json()

        if "nwm_video_url_HQ" in response:
            video_url = response["nwm_video_url_HQ"]
            video_data = requests.get(video_url).content
            bot.send_video(message.chat.id, video_data)

            user_downloads[user_id] += 1
        else:
            bot.send_message(message.chat.id, "❌ Не удалось скачать видео. Проверь ссылку.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠ Ошибка: {e}")

bot.polling()
