import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from database import get_db, User
from utils import get_random_prediction, can_get_prediction
import uvicorn
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy import func, desc
import ssl

app = FastAPI()

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

class PaymentRequest(BaseModel):
    user_id: int

def get_user_rank(user_id: int, db) -> int:
    """Получить место пользователя в рейтинге"""
    subquery = db.query(
        User.telegram_id,
        func.count(User.id).label('total_predictions')
    ).group_by(User.telegram_id).subquery()
    
    rank = db.query(func.count(subquery.c.telegram_id)).filter(
        subquery.c.total_predictions > db.query(
            func.count(User.id)
        ).filter(
            User.telegram_id == user_id
        ).scalar()
    ).scalar()
    
    return rank + 1

def get_leaderboard(db, limit: int = 10):
    """Получить топ пользователей"""
    return db.query(
        User.telegram_id,
        User.username,
        func.count(User.id).label('total_predictions')
    ).group_by(
        User.telegram_id,
        User.username
    ).order_by(
        desc('total_predictions')
    ).limit(limit).all()

@app.get("/", response_class=HTMLResponse)
async def get_prediction(request: Request, user_id: int):
    """Обработчик главной страницы"""
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    can_predict, time_left = can_get_prediction(user)
    prediction = get_random_prediction() if can_predict else None
    
    # Получаем статистику пользователя
    total_predictions = db.query(func.count(User.id)).filter(
        User.telegram_id == user_id
    ).scalar()
    
    # Получаем место в рейтинге
    rank = get_user_rank(user_id, db)
    
    # Получаем дату последнего предсказания
    last_prediction = db.query(User).filter(
        User.telegram_id == user_id
    ).order_by(
        User.last_prediction.desc()
    ).first()
    
    last_prediction_date = last_prediction.last_prediction.strftime("%d.%m.%Y %H:%M") if last_prediction and last_prediction.last_prediction else "Нет"
    
    # Получаем топ пользователей
    leaderboard = get_leaderboard(db)
    
    return templates.TemplateResponse(
        "predictionbot.html",
        {
            "request": request,
            "user": {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "stars": user.stars,
                "total_predictions": total_predictions,
                "rank": rank,
                "last_prediction_date": last_prediction_date,
                "avatar_url": f"https://t.me/i/userpic/320/{user.telegram_id}.jpg"
            },
            "prediction": prediction,
            "can_predict": can_predict,
            "time_left": time_left,
            "leaderboard": leaderboard
        }
    )

@app.post("/process_payment")
async def process_payment(payment: PaymentRequest):
    """Обработчик платежа"""
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == payment.user_id).first()
    
    if not user:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "User not found"}
        )
    
    # Проверяем, может ли пользователь получить предсказание
    can_predict, _ = can_get_prediction(user)
    if not can_predict:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Prediction cooldown active"}
        )
    
    # Проверяем баланс
    if user.stars < 100:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Not enough stars"}
        )
    
    # Списываем звезды
    user.stars -= 100
    
    # Устанавливаем время последнего предсказания
    user.last_prediction = datetime.utcnow()
    
    # Сохраняем изменения
    db.commit()
    
    return JSONResponse(
        content={"success": True}
    )

if __name__ == "__main__":
    # Запуск сервера без SSL для разработки
    uvicorn.run(
        "webapp:app",
        host="0.0.0.0",
        port=8001,
        reload=True  # Включаем автоперезагрузку для разработки
    ) 