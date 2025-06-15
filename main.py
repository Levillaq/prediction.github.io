# This is a sample Python script.

# Press Ctrl+F5 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import os
import logging
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    CallbackQueryHandler,
    MessageHandler,
    filters
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
    user = update.effective_user
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔮 Получить предсказание",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user.id}")
        )],
        [InlineKeyboardButton("📊 Рейтинг", callback_data='show_rating')]
    ])
    
    await update.message.reply_text(
        "Привет! Я бот предсказаний. Задай вопрос и получи предсказание за 1 звезду!",
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

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /balance"""
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
    
    if not user:
        await update.message.reply_text("Пожалуйста, сначала используйте команду /start")
        return
    
    await update.message.reply_text(f"Ваш баланс: {user.stars} ⭐")

async def addstars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /addstars (только для админов)"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет прав для использования этой команды")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("Использование: /addstars [user_id] [amount]")
        return
    
    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Неверный формат ID пользователя или количества звезд")
        return
    
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        await update.message.reply_text("Пользователь не найден")
        return
    
    user.stars += amount
    db.commit()
    
    await update.message.reply_text(
        f"Добавлено {amount} ⭐ пользователю {user.username or user_id}\n"
        f"Новый баланс: {user.stars} ⭐"
    )

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем предсказание
    prediction = get_random_prediction()
    
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

def main():
    """Запуск бота"""
    # Инициализация базы данных
    init_db()
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("addstars", addstars))
    
    # Добавление обработчика кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
