import sqlite3
import os
from datetime import datetime

# Resolve base directory and database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "chatbot.db")

# Automatically ensure the database directory exists
os.makedirs(DB_DIR, exist_ok=True)


def get_db_connection(db_path: str = None):
    """
    Returns a SQLite connection configured with sqlite3.Row factory.
    Automatically creates the parent directory if it does not exist.
    Configured with a 10-second timeout to prevent database locks.
    """
    target_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = None):
    """
    Initializes the SQLite database schema if tables do not exist.
    Creates:
    - chat_history: id, user_message, bot_response, mood, created_at
    - sessions: id, created_at, last_active
    - messages: id, session_id, sender, message, intent, is_crisis, timestamp
    - mood_logs: id, session_id, mood, note, timestamp
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Primary chat_history table as specified
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            mood TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Supporting tables for session-based messaging and mood tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            intent TEXT,
            is_crisis INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            mood TEXT NOT NULL,
            note TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        );
    """)

    # Performance indexes for session querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mood_session ON mood_logs (session_id);")

    conn.commit()
    conn.close()


# Alias for initialize the database
initialize_database = init_db


def save_chat(user_message: str, bot_response: str, mood: str = None, db_path: str = None) -> int:
    """
    Saves a conversation entry to the chat_history table.
    Uses parameterized SQL queries to prevent SQL injection.
    Returns the newly inserted record's id.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (user_message, bot_response, mood, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_message, bot_response, mood))
    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return inserted_id


def retrieve_chat_history(limit: int = 100, db_path: str = None) -> list:
    """
    Retrieves records from the chat_history table ordered chronologically.
    Uses parameterized SQL queries.
    Returns a list of dictionaries with id, user_message, bot_response, mood, created_at.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_message, bot_response, mood, created_at
        FROM chat_history
        ORDER BY id ASC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "id": row["id"],
            "user_message": row["user_message"],
            "bot_response": row["bot_response"],
            "mood": row["mood"],
            "created_at": row["created_at"],
        })
    return history


def clear_chat_history(db_path: str = None) -> int:
    """
    Clears all records from the chat_history table.
    Uses parameterized SQL queries.
    Returns the number of deleted records.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count


# ------------------------------------------------------------------------------
# Supporting Session & Message Functions
# ------------------------------------------------------------------------------
def ensure_session(session_id: str, db_path: str = None):
    """Ensures a session entry exists or updates its last active timestamp."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (id, created_at, last_active)
        VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET last_active = CURRENT_TIMESTAMP
    """, (session_id,))
    conn.commit()
    conn.close()


def save_message(session_id: str, sender: str, message: str, intent: str = None, is_crisis: bool = False, db_path: str = None):
    """Saves a single message (from user or bot) to the session messages table."""
    ensure_session(session_id, db_path=db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (session_id, sender, message, intent, is_crisis, timestamp)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (session_id, sender, message, intent, 1 if is_crisis else 0))
    conn.commit()
    conn.close()


def get_chat_history(session_id_or_limit=None, limit: int = 50, db_path: str = None):
    """
    Flexible history retrieval:
    - If called with an integer or None, retrieves from the chat_history table.
    - If called with a string session_id, retrieves messages for that session.
    """
    if isinstance(session_id_or_limit, int) or session_id_or_limit is None:
        effective_limit = session_id_or_limit if isinstance(session_id_or_limit, int) else limit
        return retrieve_chat_history(limit=effective_limit, db_path=db_path)

    # Session-specific retrieval
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender, message, intent, is_crisis, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
        LIMIT ?
    """, (session_id_or_limit, limit))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "sender": row["sender"],
            "message": row["message"],
            "intent": row["intent"],
            "is_crisis": bool(row["is_crisis"]),
            "timestamp": row["timestamp"]
        })
    return history


def save_mood(session_id: str, mood: str, note: str = None, db_path: str = None):
    """Logs a mood check-in for a session."""
    ensure_session(session_id, db_path=db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mood_logs (session_id, mood, note, timestamp)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (session_id, mood, note))
    conn.commit()
    conn.close()


def get_mood_logs(session_id: str, db_path: str = None):
    """Retrieves logged moods for a session."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mood, note, timestamp
        FROM mood_logs
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()

    return [{"mood": r["mood"], "note": r["note"], "timestamp": r["timestamp"]} for r in rows]


def clear_history(session_id: str = None, db_path: str = None):
    """
    Clears conversation messages and mood logs.
    If session_id is provided, clears records for that session.
    If session_id is None, clears all chat_history, messages, and mood_logs.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if session_id:
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM mood_logs WHERE session_id = ?", (session_id,))
    else:
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM mood_logs")
    conn.commit()
    conn.close()

    if not session_id:
        clear_chat_history(db_path)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
