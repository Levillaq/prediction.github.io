from datetime import datetime, timedelta
import random
from typing import List, Tuple

# Список предсказаний
PREDICTIONS = [
    "Сегодня вас ждет приятная неожиданность!",
    "Впереди вас ждет успех в делах.",
    "Будьте внимательны к знакам судьбы сегодня.",
    "Встреча с важным человеком изменит вашу жизнь.",
    "Не бойтесь принимать важные решения.",
    "Ваши мечты скоро станут реальностью.",
    "Сегодняшний день принесет вам удачу.",
    "Вас ждет интересное предложение.",
    "Не упустите шанс, который представится сегодня.",
    "Ваши усилия скоро будут вознаграждены."
]

def get_random_prediction() -> str:
    """Получить случайное предсказание из списка"""
    return random.choice(PREDICTIONS)

def format_time_remaining(last_prediction_time: datetime) -> str:
    """Форматировать оставшееся время до следующего предсказания"""
    if not last_prediction_time:
        return "0h 0m"
    
    now = datetime.utcnow()
    time_passed = now - last_prediction_time
    time_remaining = timedelta(hours=24) - time_passed
    
    if time_remaining.total_seconds() <= 0:
        return "0h 0m"
    
    hours = int(time_remaining.total_seconds() // 3600)
    minutes = int((time_remaining.total_seconds() % 3600) // 60)
    
    return f"{hours}h {minutes}m"

def can_get_prediction(user):
    """Проверить, может ли пользователь получить предсказание"""
    if not user.last_prediction:
        return True, None
    
    cooldown = timedelta(hours=24)
    time_passed = datetime.utcnow() - user.last_prediction
    
    if time_passed < cooldown:
        time_left = cooldown - time_passed
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        return False, f"{hours} ч. {minutes} мин."
    
    return True, None 