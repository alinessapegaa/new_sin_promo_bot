from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from io import BytesIO
from flask import Flask  # Добавляем импорт Flask
from threading import Thread  # Импорт для запуска Flask в фоновом режиме
import os

# Создаем Flask приложение
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Бот работает!", 200  # Простой маршрут для проверки, что приложение Flask работает

def run_flask():
    # Используем переменную окружения PORT, чтобы Flask мог работать с Render
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)  # Запуск Flask-приложения на порту 8080

TOKEN = "7909781824:AAHi_E5sHVk9n2HwbWUH2rE0AYKLPkL50A8"

# 📌 Предустановленный текст поста
POST_TEXT = "🔮 Объявляем минуту предсказаний! Уже знаем, **где и как вы проведёте 8 марта** — и раскроем тайну, если нажмёте одну из кнопок.\n\nНе забудьте поделиться результатом в комментариях!"

# 📌 Ответы для кнопок
RESPONSES = [
    "Купите ТУ САМУЮ вещь",
    "Проведёте время в кругу самых близких",
    "Получите лучший в жизни подарок",
    "Будете сиять (спасибо образу из СИН 🤭)",
    "Просто хорошо отдохнёте",
    "Получите даже слишком много букетов",
    "Порадуете себя шопингом в СИН",
    "Получите поздравление от неожиданного человека",
    "Сходите в очень интересное место"
]

# 📌 Словарь для хранения фото пользователей
user_posts = {}

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Просто отправь мне картинку 📷, и я сделаю пост!")

async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    await update.message.reply_text("📥 Получаю фото...")

    try:
        # Получаем фото
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)

        # Путь для временного сохранения
        temp_photo_path = f"photo_{user_id}.jpg"
        await photo_file.download_to_drive(temp_photo_path)

        # Проверяем, существует ли файл
        if not os.path.exists(temp_photo_path):
            await update.message.reply_text("❌ Ошибка: файл не сохранился!")
            return

        # Фиксируем данные для будущей публикации
        context.bot_data["last_photo"] = temp_photo_path
        context.bot_data["last_caption"] = "🔮 Объявляем минуту предсказаний! Уже знаем, **где и как вы проведёте 8 марта** — и раскроем тайну, если нажмёте одну из кнопок.\n\nНе забудьте поделиться результатом в комментариях!"

        # 🔹 Фиксированные кнопки 💖 (3×3)
        keyboard = [
            [
                InlineKeyboardButton("💖", callback_data=f"btn_{i}_{user_id}") for i in range(j, j+3)
            ]
            for j in range(0, 9, 3)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем изображение
        with open(temp_photo_path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=POST_TEXT,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        await update.message.reply_text("✅ Фото загружено! Теперь введи команду:\n\n`/post ID_канала`\n\nПример: `/post -1001234567890`", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: `{str(e)}`", parse_mode="Markdown")


async def post_to_channel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("❌ Ошибка: укажи ID канала после команды.\n\nПример:\n`/post -1001234567890`", parse_mode="Markdown")
        return

    channel_id = context.args[0]

    # Проверяем, есть ли сохранённое фото и текст
    if "last_photo" not in context.bot_data or "last_caption" not in context.bot_data:
        await update.message.reply_text("❌ Ошибка: сначала отправь фото боту.")
        return

    # Достаём последний сохранённый файл и текст
    photo_path = context.bot_data["last_photo"]
    caption = context.bot_data["last_caption"]

    # Проверяем, существует ли файл перед отправкой
    if not os.path.exists(photo_path):
        await update.message.reply_text("❌ Ошибка: фото не найдено! Отправь его заново.")
        return

    # 🔹 Фиксированные кнопки 💖 (3×3)
    keyboard = [
        [
            InlineKeyboardButton("💖", callback_data=f"btn_{i}_{user_id}") for i in range(j, j+3)
        ]
        for j in range(0, 9, 3)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_text("📤 Отправляю пост в канал...")

        # Отправляем пост в канал
        with open(photo_path, "rb") as photo:
            await context.bot.send_photo(
                chat_id=channel_id,
                photo=photo,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
                )


        await update.message.reply_text(f"✅ Пост успешно отправлен в канал {channel_id}!")

        # Удаляем временный файл
        os.remove(photo_path)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при отправке в канал:\n`{str(e)}`", parse_mode="Markdown")


async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    _, button_index, user_id = query.data.split("_")

    response_text = RESPONSES[int(button_index)]

    # Отправляем всплывающее окно
    await query.answer(response_text, show_alert=True)


def main():
    # Запуск Flask-приложения в другом потоке
    thread = Thread(target=run_flask)
    thread.start()

    # Запуск Telegram-бота
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("post", post_to_channel))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
