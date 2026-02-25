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

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT DEFAULT '',
            username TEXT DEFAULT '',
            joined_at INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT DEFAULT '',
            chat_type TEXT DEFAULT '',
            added_at INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS approved_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            approved_at INTEGER DEFAULT 0
        )
    """)

    # Session storage
    c.execute("""
        CREATE TABLE IF NOT EXISTS session_store (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


# ─── USER FUNCTIONS ───
def add_user(user_id, first_name="", username=""):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (user_id, first_name, username, joined_at) VALUES (?, ?, ?, ?)",
        (user_id, first_name, username, int(time.time()))
    )
    c.execute(
        "UPDATE users SET first_name = ?, username = ? WHERE user_id = ?",
        (first_name, username, user_id)
    )
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_db()
    rows = conn.execute("SELECT * FROM users WHERE is_blocked = 0").fetchall()
    conn.close()
    return rows


def get_user_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0").fetchone()[0]
    conn.close()
    return count


def get_blocked_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1").fetchone()[0]
    conn.close()
    return count


def get_total_user_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


def set_user_blocked(user_id, blocked=True):
    conn = get_db()
    conn.execute("UPDATE users SET is_blocked = ? WHERE user_id = ?", (1 if blocked else 0, user_id))
    conn.commit()
    conn.close()


# ─── CHAT FUNCTIONS ───
def add_chat(chat_id, chat_title="", chat_type=""):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO chats (chat_id, chat_title, chat_type, added_at, is_active) VALUES (?, ?, ?, ?, 1)",
        (chat_id, chat_title, chat_type, int(time.time()))
    )
    conn.commit()
    conn.close()


def remove_chat(chat_id):
    conn = get_db()
    conn.execute("UPDATE chats SET is_active = 0 WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def get_all_chats():
    conn = get_db()
    rows = conn.execute("SELECT * FROM chats WHERE is_active = 1").fetchall()
    conn.close()
    return rows


def get_chat_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM chats WHERE is_active = 1").fetchone()[0]
    conn.close()
    return count


# ─── APPROVED REQUESTS ───
def log_approved_request(user_id, chat_id):
    conn = get_db()
    conn.execute(
        "INSERT INTO approved_requests (user_id, chat_id, approved_at) VALUES (?, ?, ?)",
        (user_id, chat_id, int(time.time()))
    )
    conn.commit()
    conn.close()


def get_total_approved():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM approved_requests").fetchone()[0]
    conn.close()
    return count


# ─── SESSION STORE ───
def save_session(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO session_store (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_session(key):
    conn = get_db()
    row = conn.execute("SELECT value FROM session_store WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else None


def delete_session(key):
    conn = get_db()
    conn.execute("DELETE FROM session_store WHERE key = ?", (key,))
    conn.commit()
    conn.close()
