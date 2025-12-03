
import sqlite3
from typing import List, Tuple, Optional
import os

# Base directory of the project (root folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database location inside /data/memory.db
DB_PATH = os.path.join(BASE_DIR, "data", "memory.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            raw_text TEXT,
            summary TEXT,
            flashcards_json TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_note(raw_text: str, summary: str, flashcards_json: str, timestamp: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (timestamp, raw_text, summary, flashcards_json) VALUES (?, ?, ?, ?)",
        (timestamp, raw_text, summary, flashcards_json),
    )
    conn.commit()
    conn.close()


def get_all_notes() -> List[Tuple]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, timestamp, substr(raw_text,1,120) as preview FROM notes ORDER BY id DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_note_by_id(note_id: int) -> Optional[Tuple]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, timestamp, raw_text, summary, flashcards_json FROM notes WHERE id = ?",
        (note_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def delete_note(note_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
