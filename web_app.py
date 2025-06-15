from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = 'db.sqlite3'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            username TEXT,
            stars INTEGER DEFAULT 0,
            total_predictions INTEGER DEFAULT 0,
            last_prediction_date TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            prediction_text TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/profile', methods=['GET'])
def get_profile():
    telegram_id = request.args.get('user_id')
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE telegram_id=?', (telegram_id,))
    user = c.fetchone()
    if not user:
        c.execute('INSERT INTO users (telegram_id, username, stars) VALUES (?, ?, ?)', (telegram_id, 'user', 0))
        conn.commit()
        c.execute('SELECT * FROM users WHERE telegram_id=?', (telegram_id,))
        user = c.fetchone()
    profile = dict(user)
    conn.close()
    return jsonify(profile)

@app.route('/api/history', methods=['GET'])
def get_history():
    telegram_id = request.args.get('user_id')
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT prediction_text, date FROM predictions WHERE telegram_id=? ORDER BY date DESC LIMIT 20', (telegram_id,))
    history = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(history)

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT username, total_predictions FROM users ORDER BY total_predictions DESC LIMIT 10')
    leaderboard = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(leaderboard)

@app.route('/api/action', methods=['POST'])
def handle_action():
    data = request.json
    action = data.get('action')
    telegram_id = data.get('user_id')
    username = data.get('username', 'user')
    if action == 'get_prediction':
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT stars FROM users WHERE telegram_id=?', (telegram_id,))
        user = c.fetchone()
        if not user or user['stars'] < 100:
            return jsonify({"success": False, "error": "Недостаточно звёзд!"})
        c.execute('UPDATE users SET stars = stars - 100, total_predictions = total_predictions + 1, last_prediction_date = ? WHERE telegram_id=?',
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), telegram_id))
        prediction = "Ваше новое предсказание!"
        c.execute('INSERT INTO predictions (telegram_id, prediction_text, date) VALUES (?, ?, ?)',
                  (telegram_id, prediction, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "prediction": prediction})
    return jsonify({"success": False, "error": "Неизвестное действие"})

@app.route('/api/add_stars', methods=['POST'])
def add_stars():
    data = request.json
    telegram_id = data.get('user_id')
    stars = int(data.get('stars', 0))
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET stars = stars + ? WHERE telegram_id=?', (stars, telegram_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8000) 