import telebot
import requests
import os

# Токен бота
BOT_TOKEN = "8289812320:AAHSGU3hsumhw525yH9NNBawhVxvRjxd0Jo"
bot = telebot.TeleBot(BOT_TOKEN)

# Старт
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! 👋 Отправь мне ссылку на видео с YouTube, TikTok или Instagram, и я пришлю его без водяных знаков."
    )

# Обработка ссылок
@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if "tiktok.com" in url or "youtu" in url or "instagram.com" in url:
        bot.send_message(message.chat.id, "⏳ Загружаю видео...")

        try:
            # Пример: используем бесплатный API для скачивания (замени на свой)
            api_url = f"https://api.ryzendesu.com/download?url={url}"
            response = requests.get(api_url)

            if response.status_code == 200:
                with open("video.mp4", "wb") as f:
                    f.write(response.content)

                with open("video.mp4", "rb") as f:
                    bot.send_video(message.chat.id, f)

                os.remove("video.mp4")
            else:
                bot.send_message(message.chat.id, "❌ Не удалось скачать видео. Попробуй другую ссылку.")
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠ Ошибка: {e}")
    else:
        bot.send_message(message.chat.id, "Отправь корректную ссылку на видео.")

print("Бот запущен...")
bot.polling(none_stop=True)
