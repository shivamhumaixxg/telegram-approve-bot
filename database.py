import sqlite3
import os
import time

DB_PATH = os.environ.get("DB_PATH", "bot_database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table - stores all users who interacted with bot
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT DEFAULT '',
            username TEXT DEFAULT '',
            joined_at INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0
        )
    """)

    # Groups/Channels where bot is added
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT DEFAULT '',
            chat_type TEXT DEFAULT '',
            added_at INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Approved requests log
    c.execute("""
        CREATE TABLE IF NOT EXISTS approved_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            approved_at INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# ─── USER FUNCTIONS ───
def add_user(user_id: int, first_name: str = "", username: str = ""):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """INSERT OR IGNORE INTO users (user_id, first_name, username, joined_at)
           VALUES (?, ?, ?, ?)""",
        (user_id, first_name, username, int(time.time()))
    )
    # Update name/username if user already exists
    c.execute(
        """UPDATE users SET first_name = ?, username = ? WHERE user_id = ?""",
        (first_name, username, user_id)
    )
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE is_blocked = 0")
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_count():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_blocked_count():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_total_user_count():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count


def set_user_blocked(user_id: int, blocked: bool = True):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET is_blocked = ? WHERE user_id = ?",
        (1 if blocked else 0, user_id)
    )
    conn.commit()
    conn.close()


# ─── CHAT FUNCTIONS ───
def add_chat(chat_id: int, chat_title: str = "", chat_type: str = ""):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """INSERT OR REPLACE INTO chats (chat_id, chat_title, chat_type, added_at, is_active)
           VALUES (?, ?, ?, ?, 1)""",
        (chat_id, chat_title, chat_type, int(time.time()))
    )
    conn.commit()
    conn.close()


def remove_chat(chat_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE chats SET is_active = 0 WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def get_all_chats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM chats WHERE is_active = 1")
    rows = c.fetchall()
    conn.close()
    return rows


def get_chat_count():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM chats WHERE is_active = 1")
    count = c.fetchone()[0]
    conn.close()
    return count


# ─── APPROVED REQUESTS LOG ───
def log_approved_request(user_id: int, chat_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """INSERT INTO approved_requests (user_id, chat_id, approved_at)
           VALUES (?, ?, ?)""",
        (user_id, chat_id, int(time.time()))
    )
    conn.commit()
    conn.close()


def get_total_approved():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM approved_requests")
    count = c.fetchone()[0]
    conn.close()
    return count
