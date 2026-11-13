"""SQLite storage for chat conversations."""

import sqlite3
import os
import uuid
from datetime import datetime


_DB_NAME = "chat_history.db"


def _get_db_path(project_root: str) -> str:
    return os.path.join(project_root, _DB_NAME)


def init_db(project_root: str) -> None:
    """Create tables if they don't exist."""
    conn = sqlite3.connect(_get_db_path(project_root))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
        """
    )
    conn.commit()
    conn.close()


def create_conversation(project_root: str) -> str:
    """Create a new conversation. Returns its ID."""
    conv_id = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(_get_db_path(project_root))
    conn.execute(
        "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (conv_id, "新对话", now, now),
    )
    conn.commit()
    conn.close()
    return conv_id


def list_conversations(project_root: str) -> list[dict]:
    """Return all conversations, newest first."""
    conn = sqlite3.connect(_get_db_path(project_root))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_messages(project_root: str, conversation_id: str) -> list[dict]:
    """Return all messages in a conversation, in order."""
    conn = sqlite3.connect(_get_db_path(project_root))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_message(project_root: str, conversation_id: str, role: str, content: str) -> None:
    """Add a message and update the conversation's timestamp and title."""
    now = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(_get_db_path(project_root))
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (conversation_id, role, content, now),
    )
    # Auto-title from first user message
    if role == "user":
        cur = conn.execute(
            "SELECT title FROM conversations WHERE id = ?", (conversation_id,)
        )
        row = cur.fetchone()
        if row and row[0] == "新对话":
            title = content[:30] + ("..." if len(content) > 30 else "")
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conversation_id),
            )
        else:
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id)
            )
    else:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id)
        )
    conn.commit()
    conn.close()


def delete_conversation(project_root: str, conversation_id: str) -> None:
    """Delete a conversation and its messages."""
    conn = sqlite3.connect(_get_db_path(project_root))
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()
