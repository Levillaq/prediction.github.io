# This is a sample Python script.

# Press Ctrl+F5 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import os
import logging
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
    
    if not user:
        user = User(
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            stars=0
        )
        db.add(user)
        db.commit()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔮 Получить предсказание",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?user_id={user.telegram_id}")
        )]
    ])
    
    await update.message.reply_text(
        f"Привет, {update.effective_user.first_name}! 👋\n\n"
        f"Я бот предсказаний. Нажмите на кнопку ниже, чтобы получить предсказание.",
        reply_markup=keyboard
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_prediction":
        db = next(get_db())
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        if not user:
            await query.message.reply_text("Пожалуйста, сначала используйте команду /start")
            return
        
        # Проверка кулдауна
        can_predict, time_remaining = can_get_prediction(user.last_prediction_time)
        if not can_predict:
            await query.message.reply_text(
                f"Подождите еще {time_remaining} перед следующим предсказанием"
            )
            return
        
        # Создаем кнопку оплаты
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💫 Оплатить 100 ⭐", callback_data="pay_prediction")]
        ])
        
        await query.message.reply_text(
            "Получить предсказание стоит 100 ⭐\n"
            "Нажмите на кнопку ниже, чтобы оплатить:",
            reply_markup=keyboard
        )
    
    elif query.data == "pay_prediction":
        # Здесь будет интеграция с Telegram Stars
        # Пока просто выдаем предсказание
        prediction = get_random_prediction()
        
        # Обновляем время последнего предсказания
        db = next(get_db())
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if user:
            user.last_prediction_time = datetime.utcnow()
            db.commit()
        
        await query.message.reply_text(
            f"🔮 Ваше предсказание:\n\n"
            f"{prediction}\n\n"
            f"Следующее предсказание будет доступно через 24 часа."
        )

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
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
