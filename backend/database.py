# backend/database.py
import sqlite3
import uuid
from datetime import datetime
from backend.config import SQLITE_DB

def init_db():
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    # User Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password_hash TEXT)''')
    
    # Sessions Table (New)
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (session_id TEXT PRIMARY KEY, username TEXT, title TEXT, created_at TEXT)''')
    
    conn.commit()
    conn.close()

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
    c.execute("INSERT INTO sessions (session_id, username, title, created_at) VALUES (?, ?, ?, ?)", 
              (session_id, username, title, created_at))
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

def delete_session_db(session_id: str, username: str):
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE session_id = ? AND username = ?", (session_id, username))
    
    # Also clean up the LangChain message history table for this session
    # Note: LangChain uses a table named 'message_store' by default in SQLChatMessageHistory
    try:
        c.execute("DELETE FROM message_store WHERE session_id = ?", (session_id,))
    except:
        pass # Table might not exist yet if no messages were sent
        
    conn.commit()
    conn.close()
    return True

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