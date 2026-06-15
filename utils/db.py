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
            is_verified BOOLEAN DEFAULT 0,
            display_name TEXT,
            dob TEXT,
            study_info TEXT,
            career_level TEXT,
            onboarding_completed BOOLEAN DEFAULT 0
        )
    ''')
    try:
        c.execute('ALTER TABLE users ADD COLUMN display_name TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE users ADD COLUMN dob TEXT')
        c.execute('ALTER TABLE users ADD COLUMN study_info TEXT')
        c.execute('ALTER TABLE users ADD COLUMN career_level TEXT')
        c.execute('ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def create_user(username, email, password_hash, auth_provider='manual', is_verified=False, display_name=None):
    if display_name is None:
        display_name = username
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO users (username, email, password_hash, auth_provider, is_verified, display_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, auth_provider, is_verified, display_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, email, password_hash, auth_provider, is_verified, display_name, dob, study_info, career_level, onboarding_completed FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "password_hash": user[3],
            "auth_provider": user[4],
            "is_verified": bool(user[5]),
            "display_name": user[6] if len(user) > 6 and user[6] else user[1],
            "dob": user[7] if len(user) > 7 else None,
            "study_info": user[8] if len(user) > 8 else None,
            "career_level": user[9] if len(user) > 9 else None,
            "onboarding_completed": bool(user[10]) if len(user) > 10 else False
        }
    return None

def get_user_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, email, password_hash, auth_provider, is_verified, display_name, dob, study_info, career_level, onboarding_completed FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "password_hash": user[3],
            "auth_provider": user[4],
            "is_verified": bool(user[5]),
            "display_name": user[6] if len(user) > 6 and user[6] else user[1],
            "dob": user[7] if len(user) > 7 else None,
            "study_info": user[8] if len(user) > 8 else None,
            "career_level": user[9] if len(user) > 9 else None,
            "onboarding_completed": bool(user[10]) if len(user) > 10 else False
        }
    return None

def update_user_onboarding(username, dob, study_info, career_level):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET dob = ?, study_info = ?, career_level = ?, onboarding_completed = 1 
        WHERE username = ?
    ''', (dob, study_info, career_level, username))
    conn.commit()
    conn.close()

def verify_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET is_verified = 1 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

# Initialize when imported
init_db()
