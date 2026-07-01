from flask import g
from psycopg import connect
from psycopg.rows import dict_row
from urllib.parse import urlsplit

from .config import BOOK_STATUS_READY, STUDYPDF_DATABASE_CONNECT_TIMEOUT_SECONDS, STUDYPDF_DATABASE_URL


SCHEMA_TABLES = [
    "books",
    "pages",
    "notes",
    "chapters",
    "processing_jobs",
    "understanding_checks",
]


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    original_filename TEXT,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_page_read INTEGER DEFAULT 1,
    last_read_at TEXT,
    status TEXT DEFAULT 'READY',
    processing_error TEXT,
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS pages (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text_content TEXT,
    html_content TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    page_id BIGINT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    selected_text TEXT NOT NULL,
    note_text TEXT,
    note_type TEXT NOT NULL,
    tags TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS chapters (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    level INTEGER NOT NULL,
    start_page INTEGER NOT NULL,
    end_page INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS processing_jobs (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS understanding_checks (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    topic_key TEXT NOT NULL,
    topic_title TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    summary TEXT,
    doubt TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    UNIQUE(book_id, topic_key)
);

CREATE INDEX IF NOT EXISTS idx_pages_book_page ON pages(book_id, page_number);
CREATE INDEX IF NOT EXISTS idx_notes_book ON notes(book_id);
CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(note_type);
CREATE INDEX IF NOT EXISTS idx_chapters_book_page ON chapters(book_id, start_page, end_page);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_understanding_checks_book ON understanding_checks(book_id, page_number);
"""


class PostgresConnection:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=()):
        return self.conn.execute(to_postgres_sql(sql), params)

    def executemany(self, sql, params_seq):
        with self.conn.cursor() as cursor:
            return cursor.executemany(to_postgres_sql(sql), params_seq)

    def executescript(self, script):
        with self.conn.cursor() as cursor:
            cursor.execute(script)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def to_postgres_sql(sql):
    return sql.replace("?", "%s")


def validate_database_config():
    if not STUDYPDF_DATABASE_URL:
        raise RuntimeError("Defina STUDYPDF_DATABASE_URL com a connection string do Supabase/PostgreSQL.")


def describe_database_target():
    if not STUDYPDF_DATABASE_URL:
        return "(nao configurado)"

    try:
        parsed = urlsplit(STUDYPDF_DATABASE_URL)
    except ValueError:
        return "(connection string configurada)"

    if not parsed.hostname:
        return "(connection string configurada)"

    database = parsed.path.lstrip("/") or "(sem database)"
    host = parsed.hostname
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return f"{host}/{database}"


def connect_db():
    validate_database_config()
    return PostgresConnection(
        connect(
            STUDYPDF_DATABASE_URL,
            row_factory=dict_row,
            connect_timeout=STUDYPDF_DATABASE_CONNECT_TIMEOUT_SECONDS,
        )
    )


def check_database_connection():
    db = connect_db()
    try:
        db.execute("SELECT 1")
    finally:
        db.close()


def get_db():
    if "db" not in g:
        g.db = connect_db()
    return g.db


def open_db():
    return connect_db()


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(POSTGRES_SCHEMA)
    db.execute("UPDATE books SET status = ? WHERE status IS NULL", (BOOK_STATUS_READY,))
    db.commit()


def insert_returning_id(db, sql, params=()):
    cursor = db.execute(f"{sql.rstrip()} RETURNING id", params)
    return cursor.fetchone()["id"]


def reset_postgres_sequences(db):
    for table in SCHEMA_TABLES:
        db.execute(
            "SELECT setval(pg_get_serial_sequence(%s, 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM "
            + table,
            (table,),
        )


def row_to_dict(row):
    return dict(row) if row else None
