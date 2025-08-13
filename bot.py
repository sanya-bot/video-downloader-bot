import os
from flask import Flask, request
import telebot
import yt_dlp
import json

# --- Настройки ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Хранить токен в переменной окружения
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")  # Секретный токен для вебхука
CHANNEL_LINK = "https://t.me/zametochkysani"
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

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != SECRET_TOKEN:
        return "Unauthorized", 403
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route("/", methods=['GET'])
def index():
    return "Бот запущен через webhook!", 200

# --- Главное меню ---
def main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📩 Реклама/Сотрудничество", "🏠 Главное меню")
    markup.row("🔗 Связаться со мной")
    bot.send_message(chat_id, "Главное меню:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "Привет! 👋\n\n"
        "Я помогу скачать видео с TikTok без водяных знаков.\n"
        f"⚠️ Первые {FREE_DOWNLOAD_LIMIT} скачивания бесплатны.\n"
        f"После третьего скачивания подпишись на канал, чтобы продолжить:\n{CHANNEL_LINK}\n\n"
        "Поехали! 🚀"
    )
    bot.send_message(message.chat.id, welcome_text)
    main_menu(message.chat.id)

@bot.message_handler(func=lambda message: True)
def download_video(message):
    user_id = str(message.from_user.id)
    url = message.text.strip()

    if "tiktok.com" not in url:
        bot.send_message(message.chat.id, "❌ Отправь корректную ссылку на TikTok.")
        return

    count = user_counters.get(user_id, 0)

    if count >= FREE_DOWNLOAD_LIMIT:
        bot.send_message(
            message.chat.id,
            f"🚫 Лимит бесплатных скачиваний ({FREE_DOWNLOAD_LIMIT}) достигнут.\n"
            f"Подпишись на канал, чтобы продолжить:\n{CHANNEL_LINK}"
        )
        return

    bot.send_message(message.chat.id, "⏳ Скачиваю видео, подожди...")

    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloads/video.%(ext)s',
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as f:
            bot.send_video(message.chat.id, f)

        os.remove(filename)

        user_counters[user_id] = count + 1
        save_counters()

        if user_counters[user_id] == FREE_DOWNLOAD_LIMIT:
            bot.send_message(
                message.chat.id,
                f"✅ Использованы все {FREE_DOWNLOAD_LIMIT} бесплатные скачивания.\n"
                f"Чтобы продолжить, подпишись на канал:\n{CHANNEL_LINK}"
            )

    except Exception as e:
        print(f"[ERROR] User {user_id}: {e}")
        bot.send_message(message.chat.id, f"⚠️ Ошибка при скачивании видео: {e}")

if __name__ == "__main__":
    bot.remove_webhook()
    WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    bot.set_webhook(url=WEBHOOK_URL, secret_token=SECRET_TOKEN)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
