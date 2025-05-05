import sqlite3
import bcrypt
from datetime import datetime
from .database import DB_PATH, log_activity, init_db

def signup(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    password_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute('''
            INSERT INTO users (username, password_hashed, registration_date)
            VALUES (?, ?, ?)
        ''', (username, password_hashed, datetime.now().isoformat()))
        conn.commit()

        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        user_id = cursor.fetchone()[0]

        log_activity(user_id, "signup")
        return True, "Signup successful."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, password_hashed FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()

    if result:
        user_id, password_hashed = result
        if bcrypt.checkpw(password.encode('utf-8'), password_hashed):
            log_activity(user_id, "login")
            return True, user_id

    return False, "Invalid credentials."