# This is a sample Python script.

# Press Ctrl+F5 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import os
import logging
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice, PreCheckoutQuery
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    CallbackQueryHandler,
    MessageHandler,
    filters,
    PreCheckoutQueryHandler
)
from dotenv import load_dotenv
from database import init_db, get_db, User
from utils import get_random_prediction, can_get_prediction

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
WEBAPP_URL = "https://levillaq.github.io/prediction.github.io/"  # Обновленный URL

# Загрузка предсказаний
with open('static/predictions.json', 'r', encoding='utf-8') as f:
    PREDICTIONS = json.load(f)

# Загрузка статистики
def load_stats():
    try:
        with open('stats.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats(stats):
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# Получение случайного предсказания
def get_random_prediction():
    return random.choice(PREDICTIONS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔮 Открыть предсказания", web_app=WebAppInfo(url="https://levillaq.github.io/prediction.github.io/"))],
        [InlineKeyboardButton("📊 Рейтинг", callback_data="show_rating")]
    ])
    
    await update.message.reply_text(
        "Привет! Я бот предсказаний. Нажмите кнопку ниже, чтобы открыть веб-приложение и получить предсказание!",
        reply_markup=keyboard
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'show_rating':
        stats = load_stats()
        if not stats:
            await query.message.reply_text("Пока нет данных для рейтинга")
            return

        sorted_users = sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)
        rating_text = "📊 Топ пользователей:\n\n"
        for i, (username, data) in enumerate(sorted_users[:10], 1):
            rating_text += f"{i}. @{username}: {data['count']} предсказаний\n"
        
        await query.message.reply_text(rating_text)

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик данных от веб-приложения"""
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        
        if data.get('action') == 'get_prediction':
            # Создаем инвойс для оплаты звездами
            prices = [LabeledPrice(label="XTR", amount=100)]  # 1 звезда = 100 единиц
            
            await update.message.reply_invoice(
                title="Предсказание",
                description=f"Вопрос: {data.get('question', 'Без вопроса')}",
                payload=json.dumps({
                    'action': 'prediction',
                    'user_id': update.effective_user.id,
                    'question': data.get('question', '')
                }),
                provider_token="",  # Для Telegram Stars оставляем пустым
                currency="XTR",
                prices=prices
            )
    except Exception as e:
        print(f"Ошибка при обработке данных веб-приложения: {e}")
        await update.message.reply_text("Произошла ошибка при обработке запроса. Попробуйте позже.")

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик предварительной проверки платежа"""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик успешного платежа"""
    try:
        # Получаем данные из payload
        payload = json.loads(update.message.successful_payment.invoice_payload)
        
        # Получаем предсказание
        prediction = random.choice(PREDICTIONS)
        
        # Обновляем статистику
        stats = load_stats()
        user = update.effective_user.username or str(update.effective_user.id)
        
        if user not in stats:
            stats[user] = {'count': 0}
        stats[user]['count'] += 1
        save_stats(stats)
        
        # Отправляем предсказание
        await update.message.reply_text(
            f"✨ Ваше предсказание:\n\n{prediction}\n\n"
            f"Задайте новый вопрос, чтобы получить следующее предсказание!"
        )
    except Exception as e:
        print(f"Ошибка при обработке платежа: {e}")
        await update.message.reply_text("Произошла ошибка при обработке платежа. Пожалуйста, обратитесь в поддержку.")

async def pay_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /paysupport"""
    await update.message.reply_text(
        "Добровольные пожертвования не подразумевают возврат средств, "
        "однако, если вы очень хотите вернуть средства - свяжитесь с нами."
    )

def main():
    """Запуск бота"""
    # Инициализация базы данных
    init_db()
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("paysupport", pay_support))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
