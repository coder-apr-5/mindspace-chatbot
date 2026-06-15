import sqlite3
import os

DB_PATH = "database.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            auth_provider TEXT DEFAULT 'manual',
            is_verified BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def create_user(username, email, password_hash, auth_provider='manual', is_verified=False):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO users (username, email, password_hash, auth_provider, is_verified)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash, auth_provider, is_verified))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "password_hash": user[3],
            "auth_provider": user[4],
            "is_verified": bool(user[5])
        }
    return None

def get_user_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "password_hash": user[3],
            "auth_provider": user[4],
            "is_verified": bool(user[5])
        }
    return None

def verify_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET is_verified = 1 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

# Initialize when imported
init_db()
