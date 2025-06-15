# Бот Предсказаний

Telegram бот для получения предсказаний с веб-интерфейсом и системой рейтинга.

## Функциональность

- Получение предсказаний за Telegram Stars
- Личный кабинет пользователя
- Рейтинг пользователей
- Система кулдауна (24 часа между предсказаниями)

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
```bash
pip install -r requirements.txt
```
3. Создайте файл `.env` с настройками:
```
BOT_TOKEN=ваш_токен_бота
ADMIN_IDS=id1,id2
WEBAPP_URL=https://levillaq.github.io/prediction.github.io
```

## Запуск

1. Запустите веб-приложение:
```bash
python webapp.py
```

2. В другом терминале запустите бота:
```bash
python main.py
```

## Технологии

- Python
- FastAPI
- SQLAlchemy
- python-telegram-bot
- Telegram Web App
