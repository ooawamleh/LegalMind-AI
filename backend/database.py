# backend/database.py
import sqlite3
import uuid
from datetime import datetime
from backend.config import SQLITE_DB

def init_db():
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password_hash TEXT)''')
    
    # Updated Sessions Table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (session_id TEXT PRIMARY KEY, username TEXT, title TEXT, created_at TEXT)''')
    
    # NEW: Files Table to track uploads per session
    c.execute('''CREATE TABLE IF NOT EXISTS session_files
                 (file_id TEXT PRIMARY KEY, session_id TEXT, filename TEXT, created_at TEXT)''')
    
    conn.commit()
    conn.close()

# ... (Keep get_user_from_db and create_user_in_db as is) ...
def get_user_from_db(username: str):
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def create_user_in_db(username: str, password_hash: str):
    try:
        conn = sqlite3.connect(SQLITE_DB)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# --- SESSION MANAGEMENT ---

def create_session_db(username: str, title: str):
    session_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", (session_id, username, title, created_at))
    conn.commit()
    conn.close()
    return session_id, created_at

def get_user_sessions(username: str):
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("SELECT session_id, title, created_at FROM sessions WHERE username = ? ORDER BY created_at DESC", (username,))
    rows = c.fetchall()
    conn.close()
    return [{"session_id": r[0], "title": r[1], "created_at": r[2]} for r in rows]

def update_session_title_db(session_id: str, new_title: str):
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("UPDATE sessions SET title = ? WHERE session_id = ?", (new_title, session_id))
    conn.commit()
    conn.close()

def delete_session_db(session_id: str, username: str):
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE session_id = ? AND username = ?", (session_id, username))
    c.execute("DELETE FROM session_files WHERE session_id = ?", (session_id,))
    # LangChain history cleanup
    try:
        c.execute("DELETE FROM message_store WHERE session_id = ?", (session_id,))
    except:
        pass
    conn.commit()
    conn.close()

# --- FILE MANAGEMENT (NEW) ---

def add_file_to_session_db(session_id: str, filename: str, file_id: str):
    created_at = datetime.now().isoformat()
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("INSERT INTO session_files VALUES (?, ?, ?, ?)", (file_id, session_id, filename, created_at))
    conn.commit()
    conn.close()

def get_session_files_db(session_id: str):
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("SELECT file_id, filename FROM session_files WHERE session_id = ?", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [{"file_id": r[0], "filename": r[1]} for r in rows]

def delete_file_db(file_id: str):
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("DELETE FROM session_files WHERE file_id = ?", (file_id,))
    conn.commit()
    conn.close()

# # backend/database.py
# import sqlite3
# from backend.config import SQLITE_DB

# def init_db():
#     conn = sqlite3.connect(SQLITE_DB)
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS users
#                  (username TEXT PRIMARY KEY, password_hash TEXT)''')
#     conn.commit()
#     conn.close()

# def get_user_from_db(username: str):
#     conn = sqlite3.connect(SQLITE_DB)
#     c = conn.cursor()
#     c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
#     row = c.fetchone()
#     conn.close()
#     return row[0] if row else None

# def create_user_in_db(username: str, password_hash: str):
#     try:
#         conn = sqlite3.connect(SQLITE_DB)
#         c = conn.cursor()
#         c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
#         conn.commit()
#         conn.close()
#         return True
#     except sqlite3.IntegrityError:
#         return False
