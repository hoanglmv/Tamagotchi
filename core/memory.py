"""
Memory and SQLite storage for myDeskAssistant.
Stores conversation history, preferences, and session context.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "memory.db"


class MemoryManager:
    """Manages SQLite persistent storage for conversation messages and user preferences."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Conversation messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # User preferences and settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_message(self, role: str, content: str, session_id: str = "default") -> None:
        """Add a message (user or assistant) to conversation history."""
        if not content:
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            conn.commit()

    def get_recent_messages(self, limit: int = 10, session_id: str = "default") -> List[Dict[str, str]]:
        """Retrieve recent conversation turns for context in chat format: [{'role': ..., 'content': ...}]."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            # Return in chronological order
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def clear_history(self, session_id: Optional[str] = None) -> None:
        """Clear conversation history for a specific session or all sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            else:
                cursor.execute("DELETE FROM messages")
            conn.commit()

    def set_preference(self, key: str, value: str) -> None:
        """Save a user preference key-value pair."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, str(value))
            )
            conn.commit()

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a user preference value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
            return default
