import os
from flask import Flask, request
import telebot
import yt_dlp
import json

# --- Настройки ---
BOT_TOKEN = "8289812320:AAHSGU3hsumhw525yH9NNBawhVxvRjxd0Jo"
CHANNEL_LINK = "https://t.me/zametochkysani"
FREE_DOWNLOAD_LIMIT = 2

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Файл для хранения счетчиков пользователей
COUNTERS_FILE = "user_counters.json"

# Загрузка счетчиков из файла или инициализация пустым словарем
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
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route("/", methods=['GET'])
def index():
    return "Бот запущен через webhook!", 200

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "Привет! 👋\n\n"
        "Я помогу скачать видео с YouTube, TikTok и Instagram без водяных знаков.\n"
        "Просто отправь мне ссылку на видео, и я пришлю его тебе в хорошем качестве.\n\n"
        "⚠️ Внимание: первые 2 скачивания бесплатны.\n"
        "Чтобы продолжить пользоваться ботом, подпишись на мой канал и пришли ссылку ещё раз:\n"
        f"{CHANNEL_LINK}\n\n"
        "Поехали! 🚀"
    )
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(func=lambda message: True)
def download_video(message):
    user_id = str(message.from_user.id)
    url = message.text.strip()

    if not any(site in url for site in ["tiktok.com", "youtu", "instagram.com"]):
        bot.send_message(message.chat.id, "❌ Отправь корректную ссылку на видео с YouTube, TikTok или Instagram.")
        return

    # Проверяем счетчик скачиваний пользователя
    count = user_counters.get(user_id, 0)

    if count >= FREE_DOWNLOAD_LIMIT:
        bot.send_message(
            message.chat.id,
            f"🚫 Ты достиг лимита бесплатных скачиваний ({FREE_DOWNLOAD_LIMIT}).\n"
            f"Подпишись на мой канал, чтобы продолжить:\n{CHANNEL_LINK}"
        )
        return

    bot.send_message(message.chat.id, "⏳ Скачиваю видео, подожди...")

    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'video.%(ext)s',
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'cookies': 'cookies.txt',  # Если используешь куки, если нет — убрать
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        with open(filename, "rb") as f:
            bot.send_video(message.chat.id, f)

        os.remove(filename)

        # Увеличиваем счетчик и сохраняем
        user_counters[user_id] = count + 1
        save_counters()

        # Если после скачивания достигнут лимит, напоминаем про канал
        if user_counters[user_id] == FREE_DOWNLOAD_LIMIT:
            bot.send_message(
                message.chat.id,
                f"✅ Ты использовал все {FREE_DOWNLOAD_LIMIT} бесплатных скачивания.\n"
                f"Чтобы продолжить, подпишись на канал:\n{CHANNEL_LINK}"
            )

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при скачивании видео: {e}")

if __name__ == "__main__":
    bot.remove_webhook()
    WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

