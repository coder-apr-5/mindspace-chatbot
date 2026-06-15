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
            onboarding_completed BOOLEAN DEFAULT 0,
            bot_name TEXT,
            gender TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            mood TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
        c.execute('ALTER TABLE users ADD COLUMN bot_name TEXT')
        c.execute('ALTER TABLE users ADD COLUMN gender TEXT')
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
    c.execute('SELECT id, username, email, password_hash, auth_provider, is_verified, display_name, dob, study_info, career_level, onboarding_completed, bot_name, gender FROM users WHERE username = ?', (username,))
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
            "onboarding_completed": bool(user[10]) if len(user) > 10 else False,
            "bot_name": user[11] if len(user) > 11 else None,
            "gender": user[12] if len(user) > 12 else None
        }
    return None

def get_user_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, email, password_hash, auth_provider, is_verified, display_name, dob, study_info, career_level, onboarding_completed, bot_name, gender FROM users WHERE email = ?', (email,))
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
            "onboarding_completed": bool(user[10]) if len(user) > 10 else False,
            "bot_name": user[11] if len(user) > 11 else None,
            "gender": user[12] if len(user) > 12 else None
        }
    return None

def update_user_onboarding(username, dob, study_info, career_level, bot_name, gender):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET dob = ?, study_info = ?, career_level = ?, bot_name = ?, gender = ?, onboarding_completed = 1 
        WHERE username = ?
    ''', (dob, study_info, career_level, bot_name, gender, username))
    conn.commit()
    conn.close()

def verify_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET is_verified = 1 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def save_message(username, role, content):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO messages (username, role, content) VALUES (?, ?, ?)', (username, role, content))
    conn.commit()
    conn.close()

def get_user_messages(username, limit=30):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT role, content FROM (SELECT role, content, timestamp FROM messages WHERE username = ? ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp ASC', (username, limit))
    messages = c.fetchall()
    conn.close()
    return [{"role": msg[0], "content": msg[1]} for msg in messages]

def save_mood(username, mood):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO moods (username, mood) VALUES (?, ?)', (username, mood))
    conn.commit()
    conn.close()

def get_user_moods(username, limit=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT mood FROM (SELECT mood, timestamp FROM moods WHERE username = ? ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp ASC', (username, limit))
    moods = c.fetchall()
    conn.close()
    return [m[0] for m in moods]

def delete_user_history(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE username = ?', (username,))
    c.execute('DELETE FROM moods WHERE username = ?', (username,))
    conn.commit()
    conn.close()

# Initialize when imported
init_db()
