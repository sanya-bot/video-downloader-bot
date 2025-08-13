import os
import json
from flask import Flask, request
import telebot
from telebot import types
import yt_dlp

# --- Настройки ---
BOT_TOKEN = "8289812320:AAHSGU3hsumhw525yH9NNBawhVxvRjxd0Jo"
CHANNEL_LINK = "https://t.me/zametochkysani"
CONTACT = "@ssanyaFG"
FREE_DOWNLOAD_LIMIT = 3

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

COUNTERS_FILE = "user_counters.json"
if os.path.exists(COUNTERS_FILE):
    with open(COUNTERS_FILE, "r") as f:
        user_counters = json.load(f)
else:
    user_counters = {}

def save_counters():
    with open(COUNTERS_FILE, "w") as f:
        json.dump(user_counters, f)

# --- Главное меню ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 Скачать видео TikTok")
    markup.row("❓ Инструкция / FAQ", "ℹ О боте")
    markup.row("💌 Обратная связь", "🔗 Мой канал")
    return markup

# --- Flask webhook ---
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route("/", methods=['GET'])
def index():
    return "Бот запущен!", 200

# --- Команда /start ---
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "Привет! 👋\n\n"
        "Я помогу скачать видео с TikTok без водяных знаков.\n"
        f"⚠ Первые {FREE_DOWNLOAD_LIMIT} скачивания бесплатны.\n"
        "Чтобы продолжить после лимита, подпишись на мой канал."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# --- Обработка сообщений ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    if text == "📥 Скачать видео TikTok":
        msg = bot.send_message(message.chat.id, "Отправь ссылку на видео TikTok:")
        bot.register_next_step_handler(msg, download_tiktok)
    elif text == "❓ Инструкция / FAQ":
        bot.send_message(message.chat.id, "Просто отправь ссылку на TikTok, и я пришлю видео без водяных знаков.", reply_markup=main_menu())
    elif text == "ℹ О боте":
        bot.send_message(message.chat.id, "Бот создан Сани для удобного скачивания TikTok.\nПоддержка бесплатных скачиваний: первые 3 видео.", reply_markup=main_menu())
    elif text == "💌 Обратная связь":
        bot.send_message(message.chat.id, f"Напиши мне здесь: {CONTACT}", reply_markup=main_menu())
    elif text == "🔗 Мой канал":
        bot.send_message(message.chat.id, f"Подписывайся на канал: {CHANNEL_LINK}", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Выбери действие из меню ⬇️", reply_markup=main_menu())

# --- Скачивание TikTok ---
def download_tiktok(message):
    user_id = str(message.from_user.id)
    url = message.text.strip()

    if "tiktok.com" not in url:
        bot.send_message(message.chat.id, "❌ Это не ссылка на TikTok. Попробуй ещё раз.", reply_markup=main_menu())
        return

    count = user_counters.get(user_id, 0)
    if count >= FREE_DOWNLOAD_LIMIT:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Подписаться на канал", url=CHANNEL_LINK))
        bot.send_message(message.chat.id, f"🚫 Лимит бесплатных скачиваний ({FREE_DOWNLOAD_LIMIT}) достигнут.", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "⏳ Скачиваю видео...")

    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'video.%(ext)s',
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as f:
            bot.send_video(message.chat.id, f)

        os.remove(filename)

        # Счётчик и сохранение
        user_counters[user_id] = count + 1
        save_counters()

        if user_counters[user_id] == FREE_DOWNLOAD_LIMIT:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Подписаться на канал", url=CHANNEL_LINK))
            bot.send_message(message.chat.id, f"✅ Ты использовал все {FREE_DOWNLOAD_LIMIT} бесплатных скачивания.\nЧтобы продолжить, подпишись на канал:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, f"✅ Скачивание завершено. Бесплатных осталось: {FREE_DOWNLOAD_LIMIT - user_counters[user_id]}", reply_markup=main_menu())

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠ Ошибка при скачивании: {e}", reply_markup=main_menu())

# --- Запуск ---
if __name__ == "__main__":
    bot.remove_webhook()
    WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
