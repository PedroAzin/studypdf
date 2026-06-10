import sqlite3

from flask import g

from .config import BOOK_STATUS_READY, DATA_DIR, DB_PATH


def get_db():
    if "db" not in g:
        DATA_DIR.mkdir(exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def open_db():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_column(db, table, column, definition):
    columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            original_filename TEXT,
            file_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            text_content TEXT,
            html_content TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            page_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            selected_text TEXT NOT NULL,
            note_text TEXT,
            note_type TEXT NOT NULL,
            tags TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (page_id) REFERENCES pages(id)
        );

        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            slug TEXT NOT NULL,
            level INTEGER NOT NULL,
            start_page INTEGER NOT NULL,
            end_page INTEGER NOT NULL,
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        CREATE TABLE IF NOT EXISTS processing_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        CREATE TABLE IF NOT EXISTS understanding_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            topic_key TEXT NOT NULL,
            topic_title TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            confidence INTEGER NOT NULL,
            summary TEXT,
            doubt TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id),
            UNIQUE(book_id, topic_key)
        );

        CREATE INDEX IF NOT EXISTS idx_pages_book_page ON pages(book_id, page_number);
        CREATE INDEX IF NOT EXISTS idx_notes_book ON notes(book_id);
        CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(note_type);
        CREATE INDEX IF NOT EXISTS idx_chapters_book_page ON chapters(book_id, start_page, end_page);
        CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status, created_at);
        CREATE INDEX IF NOT EXISTS idx_understanding_checks_book ON understanding_checks(book_id, page_number);
        """
    )
    ensure_column(db, "books", "last_page_read", "INTEGER DEFAULT 1")
    ensure_column(db, "books", "last_read_at", "TEXT")
    ensure_column(db, "books", "status", f"TEXT DEFAULT '{BOOK_STATUS_READY}'")
    ensure_column(db, "books", "processing_error", "TEXT")
    ensure_column(db, "books", "processed_at", "TEXT")
    db.execute("UPDATE books SET status = ? WHERE status IS NULL", (BOOK_STATUS_READY,))
    db.commit()


def row_to_dict(row):
    return dict(row) if row else None
