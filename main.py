# This is a sample Python script.

# Press Ctrl+F5 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import os
import json
import random
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from database import init_db, get_db, User
from utils import get_random_prediction, can_get_prediction

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

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

def payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Оплатить 100 ⭐️",
        pay=True,
        invoice=types.Invoice(
            title="Предсказание",
            description="Получите ваше предсказание",
            currency="XTR",  # Валюта Telegram Stars
            prices=[LabeledPrice(label="Предсказание", amount=100)],
            start_parameter="prediction",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )
    )
    return builder.as_markup()

# Получение случайного предсказания
def get_random_prediction():
    return random.choice(PREDICTIONS)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Получить предсказание", web_app=WebAppInfo(url="https://levillaq.github.io/prediction.github.io/"))],
        [InlineKeyboardButton(text="📊 Рейтинг", callback_data="show_rating")]
    ])
    
    await message.answer(
        "Привет! Я бот предсказаний. Нажмите кнопку ниже, чтобы получить предсказание!",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "show_rating")
async def show_rating(callback: types.CallbackQuery):
    """Обработчик показа рейтинга"""
    stats = load_stats()
    if not stats:
        await callback.message.answer("Пока нет данных для рейтинга")
        return

    sorted_users = sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)
    rating_text = "📊 Топ пользователей:\n\n"
    for i, (username, data) in enumerate(sorted_users[:10], 1):
        rating_text += f"{i}. @{username}: {data['count']} предсказаний\n"
    
    await callback.message.answer(rating_text)
    await callback.answer()

@dp.message(lambda message: message.web_app_data is not None)
async def web_app_data(message: types.Message):
    """Обработчик данных от веб-приложения"""
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get('action') == 'get_prediction':
            # Отправляем сообщение с кнопкой оплаты
            await message.answer(
                "Нажмите кнопку ниже для оплаты:",
                reply_markup=payment_keyboard()
            )
    except Exception as e:
        print(f"Ошибка при обработке данных веб-приложения: {e}")
        await message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """Обработчик предварительной проверки платежа"""
    await pre_checkout_query.answer(ok=True)

@dp.message(lambda message: message.successful_payment is not None)
async def successful_payment(message: types.Message):
    """Обработчик успешного платежа"""
    try:
        # Получаем предсказание
        prediction = random.choice(PREDICTIONS)
        
        # Обновляем статистику
        stats = load_stats()
        user = message.from_user.username or str(message.from_user.id)
        
        if user not in stats:
            stats[user] = {'count': 0}
        stats[user]['count'] += 1
        save_stats(stats)
        
        # Отправляем предсказание
        await message.answer(
            f"✨ Ваше предсказание:\n\n{prediction}\n\n"
            f"Нажмите кнопку 'Получить предсказание' для следующего предсказания!"
        )
    except Exception as e:
        print(f"Ошибка при обработке платежа: {e}")
        await message.answer("Произошла ошибка при обработке платежа. Пожалуйста, обратитесь в поддержку.")

@dp.message(Command("paysupport"))
async def pay_support(message: types.Message):
    """Обработчик команды /paysupport"""
    await message.answer(
        "Добровольные пожертвования не подразумевают возврат средств, "
        "однако, если вы очень хотите вернуть средства - свяжитесь с нами."
    )

async def main():
    """Запуск бота"""
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
